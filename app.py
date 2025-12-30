from flask import Flask, request, jsonify
import os
import json
import requests
import base64
import logging
import sys
from search_maamar_with_openai import search_maamar

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Cloud Run captures stderr
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
HUMAINS_LOGIN_URL = "https://humains-core-dev.appspot.com/auth/login"
HUMAINS_INJECT_URL = "https://humains-core-dev.appspot.com/hub/inject"
HUMAINS_USERNAME = os.environ.get("HUMAINS_USERNAME", "")
HUMAINS_PASSWORD = os.environ.get("HUMAINS_PASSWORD", "")

# Global token storage
humains_token = None


def login_to_humains():
    """
    Login to Humains service and get authentication token
    """
    global humains_token
    
    if not HUMAINS_USERNAME or not HUMAINS_PASSWORD:
        logger.warning("HUMAINS_USERNAME or HUMAINS_PASSWORD not set. Injection will not work.")
        return None
    
    try:
        # Create Basic Auth header
        credentials = f"{HUMAINS_USERNAME}:{HUMAINS_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(HUMAINS_LOGIN_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract token from response
        token_data = response.json()
        humains_token = token_data.get('token') or token_data.get('access_token')
        
        if humains_token:
            logger.info(f"Successfully logged in to Humains service")
            return humains_token
        else:
            logger.error(f"Login response missing token: {token_data}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to login to Humains service: {e}")
        return None


import urllib.request
import urllib.error

def post_json_urllib(url, data, token):
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {token}')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        logger.error(f"Urllib error: {e}")
        return 0, str(e)

def inject_response(client_id, conversation_id, values):
    """
    Inject response back to Humains service
    """
    global humains_token
    
    # Try to login if we don't have a token
    if not humains_token:
        humains_token = login_to_humains()
        if not humains_token:
            logger.error("Cannot inject: No authentication token available")
            return False
    
    try:
        # Simplify values to avoid size issues
        inject_values = values
        
        # Handle truncation for both string and dict formats
        if isinstance(values, dict):
            # Check for known keys like 'server_search', 'answer', 'article'
            for key in ['server_search', 'answer', 'article']:
                if key in values:
                    val = values[key]
                    if isinstance(val, str):
                        # Handle string answer
                        if len(val) > 30000:
                            inject_values = values.copy()
                            inject_values[key] = val[:30000] + "..."
                    break
        
        # Prepare payload matching the reference code structure
        # All fields (client_id, conversation_id, values) go in the JSON body
        payload = {
            "client_id": client_id,
            "conversation_id": conversation_id,
            "values": inject_values
        }
        
        headers = {
            "Authorization": f"Bearer {humains_token.strip()}"
        }
        
        logger.info(f"Injecting to {HUMAINS_INJECT_URL}")
        
        # Manually dump JSON with ensure_ascii=False to send raw UTF-8 Hebrew
        json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        
        headers["Content-Type"] = "application/json; charset=utf-8"
        
        # LOGGING THE EXACT PAYLOAD FOR DEBUGGING
        logger.info(f"--- PREPARED INJECTION PAYLOAD ---")
        logger.info(f"URL: {HUMAINS_INJECT_URL}")
        logger.info(f"Headers keys: {list(headers.keys())}")
        # Log the first 1000 chars of the body to verify structure
        body_preview = json_data.decode('utf-8')[:1000]
        logger.info(f"Body Preview (First 1000 chars): {body_preview}")
        logger.info(f"--- END PAYLOAD DEBUG ---")
        
        # Send request with all data in body (no query params)
        response = requests.post(
            HUMAINS_INJECT_URL, 
            data=json_data, 
            headers=headers, 
            timeout=10
        )
        logger.info(f"Inject response: status={response.status_code}, body={response.text[:200]}")
        
        # If unauthorized, try to login again and retry
        if response.status_code == 401:
            logger.info("Token expired. Re-authenticating...")
            humains_token = login_to_humains()
            if humains_token:
                headers["Authorization"] = f"Bearer {humains_token.strip()}"
                response = requests.post(
                    HUMAINS_INJECT_URL, 
                    data=json_data, 
                    headers=headers, 
                    timeout=10
                )
                logger.info(f"Retry response: status={response.status_code}, body={response.text[:200]}")
        
        if response.status_code >= 400:
            logger.error(f"Failed to inject: {response.status_code} - {response.text}")
            return False
            
        logger.info(f"Injected response to conversation {conversation_id}: Status {response.status_code}")
        return True
            
    except Exception as e:
        logger.error(f"Failed to inject response: {e}")
        return False


@app.route('/search', methods=['GET', 'POST'])
def search_api():
    """
    API Endpoint for searching Maamarim.
    
    Accepts both GET (URL params) and POST (JSON body).
    
    Parameters:
    - name OR article: (Optional) The name/title of the Maamar (e.g., "באתי לגני")
    - question OR quastion: (Optional) The concept or question (e.g., "שכינה")
    - top_n: (Optional) Number of results to return (default: 1)
    
    GET Examples:
    /search?name=באתי לגני&question=שכינה&top_n=10
    /search?article=באתי לגני&quastion=שכינה&top_n=10
    
    POST Example (Standard):
    {"name": "באתי לגני", "question": "שכינה", "top_n": 10}
    OR
    {"article": "באתי לגני", "quastion": "שכינה", "top_n": 10}
    
    POST Example (Humains Service):
    [{"value": "{\"article\": \"באתי לגני\", \"quastion\": \"שכינה\"}", ...}]
    """
    try:
        # Extract headers for injection (case-insensitive)
        client_id = request.headers.get('client-id') or request.headers.get('CLIENT-ID')
        conversation_id = request.headers.get('conversation-id') or request.headers.get('CONVERSATION-ID')
        
        # Determine if this is a Humains request based on presence of headers
        is_humains_request = bool(client_id and conversation_id)
        
        logger.info(f"Request headers: client_id={client_id}, conversation_id={conversation_id}, is_humains={is_humains_request}")
        
        # 1. Get parameters from either GET or POST
        if request.method == 'POST':
            raw_data = request.get_json()
            logger.info(f"Raw POST data: {raw_data}")
            
            # Check if it's the Humains service nested array format
            if isinstance(raw_data, list) and len(raw_data) > 0 and 'value' in raw_data[0]:
                # Parse the nested JSON string
                value_str = raw_data[0]['value']
                data = json.loads(value_str)
                # Map their field names to ours
                name = data.get('article', '').strip()
                question = data.get('quastion', '').strip()  # Note: their typo
                top_n = int(data.get('top_n', 1))
            else:
                # Standard JSON format - accept both "name" and "article"
                data = raw_data or {}
                name = data.get('name') or data.get('article', '')
                name = name.strip()
                question = data.get('question') or data.get('quastion', '')
                question = question.strip()
                top_n = int(data.get('top_n', 1))
        else:  # GET - accept both "name" and "article"
            name = request.args.get('name') or request.args.get('article', '')
            name = name.strip()
            question = request.args.get('question') or request.args.get('quastion', '')
            question = question.strip()
            top_n = int(request.args.get('top_n', 1))

        # 2. Validation: Need at least one search term
        if not name and not question:
            error_msg = "Please provide at least a 'name' or a 'question'."
            
            # If Humains request, inject error response
            if is_humains_request:
                inject_response(client_id, conversation_id, {"server_search": error_msg})
            
            return jsonify({"error": error_msg}), 400

        # Log search parameters
        logger.info(f"Search params: name='{name}', question='{question}', top_n={top_n}")

        # 3. Run Search
        # Note: In the new version search_maamar, question is used for filtering/ranking.
        # If the user only provided a name but no question, we might want to still pass the name as the maamar_name.
        results = search_maamar(
            maamar_name=name,
            question=question, # In the new API, this parameter is used for extracting keywords
            # max_results=top_n, # This parameter is supported by search_maamar
            # use_semantic=True  # This parameter is not in the signature but handled inside if configured
        )

        # 4. Format Response
        response_data = []
        for r in results:
            response_data.append({
                "name": r.get('name'),
                "score": r.get('score'),
                "text_preview": r.get('text', '')[:300] + "...",
                "full_text": r.get('text', ''),
                "filename": r.get('filename'),
                "year": r.get('year', '')
            })

        result = {
            "count": len(response_data),
            "results": response_data
        }
        
        # 5. If Humains request, inject the response wrapped in "server_search" key
        if is_humains_request:
            # Prepare string answer (full text of first result, or "No results")
            answer_text = ""
            if len(response_data) > 0:
                answer_text = response_data[0]['full_text']
            else:
                answer_text = "לא נמצאו מאמרים תואמים."
                
            inject_response(client_id, conversation_id, {"server_search": answer_text})

        return jsonify(result)

    except Exception as e:
        error_result = {"error": str(e)}
        
        # Try to inject error if we have the headers
        try:
            if is_humains_request:
                inject_response(client_id, conversation_id, {"answer": f"Error: {str(e)}"})
        except:
            pass
        
        return jsonify(error_result), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Maamar Search API is running"}), 200

if __name__ == '__main__':
    # Login to Humains service on startup
    logger.info("Logging in to Humains service...")
    login_to_humains()
    
    # Local development run
    app.run(host='0.0.0.0', port=5000, debug=True)


# For production (Cloud Run/PythonAnywhere), login when module is imported
logger.info("Production mode: Logging in to Humains service...")
login_to_humains()

