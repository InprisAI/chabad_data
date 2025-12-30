# Maamar Search API - Google Cloud Run Deployment Guide

## Files Included

| File | Description |
|------|-------------|
| `deploy.sh` | **Automated deployment script** (Recommended) |
| `app.py` | Flask API application |
| `search_maamar_with_openai.py` | Search logic with fuzzy matching |
| `requirements.txt` | Python dependencies |
| `2_maamarim_unified.pkl.gz` | Article database |
| `Dockerfile` | Docker container definition |
| `.dockerignore` | Build context exclusions |
| `QUERY_GUIDE.md` | API usage documentation |

## Option 1: Automated Deployment (Recommended)

The `deploy.sh` script handles API enabling, Artifact Registry creation, and deployment configuration automatically.

### 1. Prerequisites
- Google Cloud CLI installed and authenticated
- Bash terminal (Linux, macOS, or Git Bash on Windows)

### 2. Set Environment Variables
The script uses environment variables for configuration. Set them before running the script:

```bash
export OPENAI_API_KEY="your-openai-key"
export HUMAINS_USERNAME="your-username"
export HUMAINS_PASSWORD="your-password"
export GROQ_API_KEY="your-groq-key" # Optional
```

### 3. Run Deployment
Choose the target environment (`dev` or `prod`):

```bash
# Deploy to Development (Project: chabad-data-dev)
./deploy.sh dev

# Deploy to Production (Project: chabad-data-482813)
./deploy.sh prod
```

## Option 2: Manual Deployment

If you cannot use the script, run these commands manually (adjusting for Windows PowerShell if needed).

### 1. Configuration
```bash
# Set your target project (dev or prod)
gcloud config set project chabad-data-dev  # OR chabad-data-482813
```

### 2. Deploy
This command matches the configuration in `deploy.sh` (2 CPU, 2Gi Memory, etc.).

```bash
gcloud run deploy chabad-data-api \
  --source . \
  --region europe-west4 \
  --no-allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --timeout 3600 \
  --set-env-vars "OPENAI_API_KEY=your-key,HUMAINS_USERNAME=your-user,HUMAINS_PASSWORD=your-pass,GROQ_API_KEY=your-key,ENABLE_SEMANTIC_SEARCH=1"
```

### 3. Allow Public Access
After successful deployment, allow unauthenticated access:

```bash
gcloud run services add-iam-policy-binding chabad-data-api \
  --region europe-west4 \
  --member="allUsers" \
  --role="roles/run.invoker"
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
