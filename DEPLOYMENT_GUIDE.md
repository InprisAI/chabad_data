# Maamar Search API - Google Cloud Run Deployment Guide

## Files Included

| File | Description |
|------|-------------|
| `app.py` | Flask API application |
| `search_maamar_with_openai.py` | Search logic with fuzzy matching |
| `requirements.txt` | Python dependencies |
| `2_maamarim_unified.pkl.gz` | Article database with embeddings (automatically renamed in Docker) |
| `Dockerfile` | Docker container definition |
| `create_pickle.py` | Script to regenerate data file (optional) |
| `QUERY_GUIDE.md` | API usage documentation |

## Quick Deploy to Google Cloud Run

### 1. Prerequisites
```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Login to your Google account
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Deploy
```bash
# Navigate to the extracted folder
cd maamar-search

# Deploy to Cloud Run
# Note: Replace placeholders with your actual keys
gcloud run deploy maamar-search \
  --source . \
  --region europe-west4 \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "OPENAI_API_KEY=your-openai-key,HUMAINS_USERNAME=your-username,HUMAINS_PASSWORD=your-password,GROQ_API_KEY=your-groq-key,ENABLE_SEMANTIC_SEARCH=1"
```

### 3. Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (or Grok/xAI key if using compatible endpoint) |
| `HUMAINS_USERNAME` | Humains service username (for injection) |
| `HUMAINS_PASSWORD` | Humains service password (for injection) |
| `GROQ_API_KEY` | Groq/xAI API Key for keyword extraction |
| `ENABLE_SEMANTIC_SEARCH` | Set to `1` to enable semantic search features |

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your-key
export HUMAINS_USERNAME=your-username
export HUMAINS_PASSWORD=your-password
export GROQ_API_KEY=your-groq-key
export ENABLE_SEMANTIC_SEARCH=1

# Run locally
python app.py
```

## API Usage

### Health Check
```
GET /health
```

### Search
```
GET /search?name=באתי לגני&question=שכינה&top_n=5
POST /search
Content-Type: application/json
{"article": "באתי לגני", "quastion": "שכינה", "top_n": 5}
```

See `QUERY_GUIDE.md` for more examples.
