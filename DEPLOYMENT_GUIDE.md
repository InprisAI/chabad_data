# Maamar Search API - Deployment Guide

## Overview
The Flask API now supports:
1. **Standard GET/POST requests** (existing functionality)
2. **Humains service integration** with automatic login and response injection

## What's New

### 1. Humains Service Integration
- Automatically logs in to `https://chatwith.humains.com/login` on startup
- Handles the nested array format from Humains service
- Maps field names: `article` → `name`, `quastion` → `question`
- Automatically injects search results back to conversations

### 2. Authentication Flow
```
Startup → Login with Basic Auth → Get Token → Use Token for all injections
```

### 3. Request Formats Supported

#### Standard GET Request
```bash
curl "https://nisyron.pythonanywhere.com/search?name=באתי לגני&top_n=5"
```

#### Standard POST Request
```bash
curl -X POST https://nisyron.pythonanywhere.com/search \
  -H "Content-Type: application/json" \
  -d '{"name": "באתי לגני", "question": "שכינה", "top_n": 10}'
```

#### Humains Service Format (Automatic)
```json
[
  {
    "value": "{\"article\": \"באתי לגני\", \"quastion\": \"שכינה\"}",
    "_IMTHEADERS_": [...]
  }
]
```

## Deployment to PythonAnywhere

### Step 1: Update Environment Variables
On PythonAnywhere, edit the WSGI configuration file:

```python
# /var/www/nisyron_pythonanywhere_com_wsgi.py

import sys
import os

project_home = '/home/nisyron'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set ALL environment variables
os.environ["OPENAI_API_KEY"] = "sk-proj-SUyrI..."  # Your OpenAI key
os.environ["HUMAINS_USERNAME"] = "your_username"    # NEW: Humains username
os.environ["HUMAINS_PASSWORD"] = "your_password"    # NEW: Humains password

from app import app as application
```

### Step 2: Upload Updated Files
1. Go to https://www.pythonanywhere.com/user/nisyron/files/home/nisyron
2. Delete the old `app.py` (if it exists)
3. Upload the new `app.py`

### Step 3: Reload the Web App
1. Go to https://www.pythonanywhere.com/user/nisyron/webapps/
2. Click "Reload" button
3. Check the server log to verify login succeeded

### Step 4: Verify
Check the server log at:
https://www.pythonanywhere.com/user/nisyron/files/var/log/nisyron.pythonanywhere.com.server.log

You should see:
```
Production mode: Logging in to Humains service...
Successfully logged in to Humains service
```

## How It Works

### 1. Incoming Request Detection
```python
# Detects Humains format by checking if request body is an array with 'value' field
if isinstance(raw_data, list) and len(raw_data) > 0 and 'value' in raw_data[0]:
    is_humains_format = True
```

### 2. Header Extraction
```python
# Extracts necessary headers for injection
client_id = request.headers.get('client-id')
conversation_id = request.headers.get('conversation-id')
```

### 3. Response Injection
```python
# Automatically injects results back to Humains service
if is_humains_format and client_id and conversation_id:
    inject_response(client_id, conversation_id, result)
```

### 4. Token Management
- Logs in on startup
- Stores token globally
- Auto-refreshes if token expires (401 response)

## Testing

### Test Standard API (unchanged)
```python
import requests

# GET
r = requests.get('https://nisyron.pythonanywhere.com/search', params={
    'name': 'באתי לגני',
    'top_n': 5
})
print(r.json())

# POST
r = requests.post('https://nisyron.pythonanywhere.com/search', json={
    'name': 'באתי לגני',
    'top_n': 5
})
print(r.json())
```

### Test Humains Format
```python
import requests

# Simulate Humains service request
r = requests.post('https://nisyron.pythonanywhere.com/search', 
    json=[{
        "value": '{"article": "באתי לגני", "quastion": "שכינה"}'
    }],
    headers={
        'client-id': 'test_client:test_user',
        'conversation-id': 'test-conversation-123'
    }
)
print(r.json())
```

## Troubleshooting

### Issue: "HUMAINS_USERNAME or HUMAINS_PASSWORD not set"
**Solution**: Add credentials to WSGI config (see Step 1)

### Issue: "Failed to login to Humains service"
**Solutions**:
1. Verify credentials are correct
2. Check if login URL is accessible: `https://chatwith.humains.com/login`
3. Check server logs for detailed error

### Issue: "Cannot inject: No authentication token available"
**Solutions**:
1. Verify login succeeded on startup (check server log)
2. Manually test login endpoint
3. Check network connectivity from PythonAnywhere

### Issue: Injection fails with 401
**Solution**: Token will auto-refresh. Check logs to ensure re-authentication succeeded.

## API Response Format

Both standard and Humains requests return the same format:

```json
{
  "count": 2,
  "results": [
    {
      "name": "באתי לגני אחותי כלה2 תשי"א",
      "score": 95,
      "text_preview": "בס\"ד, יו\"ד שבט, תשי\"א...",
      "full_text": "...",
      "filename": "maamarim_chunks\\maamarim_chunk_01.json",
      "year": ""
    }
  ]
}
```

For Humains requests, this response is **also** injected back to the conversation.

## Security Notes

1. **Credentials**: Never commit credentials to git. Use environment variables only.
2. **Token Storage**: Token is stored in memory, lost on restart (will auto-login again).
3. **HTTPS**: All communication uses HTTPS (both incoming and outgoing).

## Support

For issues, check:
1. PythonAnywhere error log: `nisyron.pythonanywhere.com.error.log`
2. PythonAnywhere server log: `nisyron.pythonanywhere.com.server.log`
3. Test endpoints individually to isolate issues







