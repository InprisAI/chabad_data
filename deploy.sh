#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if environment parameter is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Environment parameter required!${NC}"
    echo -e "${YELLOW}Usage: ./deploy.sh [dev|prod]${NC}"
    echo -e "${YELLOW}  dev  - Deploy to chabad-data-dev${NC}"
    echo -e "${YELLOW}  prod - Deploy to chabad-data-482813${NC}"
    exit 1
fi

ENV=$1

# Set project based on environment
if [ "$ENV" = "dev" ]; then
    PROJECT="chabad-data-dev"
elif [ "$ENV" = "prod" ]; then
    PROJECT="chabad-data-482813"
else
    echo -e "${RED}Error: Invalid environment '${ENV}'!${NC}"
    echo -e "${YELLOW}Usage: ./deploy.sh [dev|prod]${NC}"
    echo -e "${YELLOW}  dev  - Deploy to chabad-data-dev${NC}"
    echo -e "${YELLOW}  prod - Deploy to chabad-data-482813${NC}"
    exit 1
fi

REGION="europe-west4"
SERVICE_NAME="chabad-data-api"

echo -e "${GREEN}🚀 Deploying Chabad Data API to Cloud Run...${NC}"
echo -e "${YELLOW}Environment: ${ENV}${NC}"
echo -e "${YELLOW}Project: ${PROJECT}${NC}"
echo -e "${YELLOW}Region: ${REGION}${NC}"
echo -e "${YELLOW}Service: ${SERVICE_NAME}${NC}"

# Enable required APIs
echo -e "${YELLOW}Checking required APIs...${NC}"
REQUIRED_APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "containerregistry.googleapis.com"
    "artifactregistry.googleapis.com"
)

for API in "${REQUIRED_APIS[@]}"; do
    echo -e "${YELLOW}Checking ${API}...${NC}"
    if ! gcloud services list --enabled --project=${PROJECT} --filter="name:${API}" --format="value(name)" 2>/dev/null | grep -q "${API}"; then
        echo -e "${YELLOW}Enabling ${API}...${NC}"
        if gcloud services enable ${API} --project=${PROJECT} 2>&1 | grep -q "PERMISSION_DENIED"; then
            echo -e "${RED}❌ Permission denied to enable ${API}${NC}"
            echo -e "${YELLOW}Please enable it manually:${NC}"
            echo -e "${YELLOW}  https://console.developers.google.com/apis/api/${API}/overview?project=${PROJECT}${NC}"
            echo -e "${YELLOW}Or ask your project admin to grant you 'Service Usage Admin' role.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ ${API} enabled${NC}"
        # Wait a few seconds for API to propagate
        sleep 3
    else
        echo -e "${GREEN}✅ ${API} already enabled${NC}"
    fi
done

# Check/create Artifact Registry repository
ARTIFACT_REGISTRY_REPO="cloud-run-source-deploy"
ARTIFACT_REGISTRY_LOCATION="europe-west4"
echo -e "${YELLOW}Checking Artifact Registry repository...${NC}"

if ! gcloud artifacts repositories describe ${ARTIFACT_REGISTRY_REPO} \
    --location=${ARTIFACT_REGISTRY_LOCATION} \
    --project=${PROJECT} \
    --format="value(name)" 2>/dev/null | grep -q "${ARTIFACT_REGISTRY_REPO}"; then
    echo -e "${YELLOW}Creating Artifact Registry repository '${ARTIFACT_REGISTRY_REPO}'...${NC}"
    if gcloud artifacts repositories create ${ARTIFACT_REGISTRY_REPO} \
        --repository-format=docker \
        --location=${ARTIFACT_REGISTRY_LOCATION} \
        --project=${PROJECT} \
        --description="Cloud Run source deployments" 2>&1 | grep -q "PERMISSION_DENIED"; then
        echo -e "${YELLOW}⚠️  Could not create Artifact Registry repository automatically.${NC}"
        echo -e "${YELLOW}It will be created automatically during deployment if you have permissions.${NC}"
        echo -e "${YELLOW}If deployment fails, you may need 'Artifact Registry Admin' role.${NC}"
    else
        echo -e "${GREEN}✅ Artifact Registry repository created${NC}"
    fi
else
    echo -e "${GREEN}✅ Artifact Registry repository already exists${NC}"
fi

# Check if .dockerignore exists
if [ ! -f .dockerignore ]; then
    echo -e "${RED}Error: .dockerignore file not found!${NC}"
    exit 1
fi

# Check build context size (approximate)
echo -e "${YELLOW}Checking build context size...${NC}"
CONTEXT_SIZE=$(du -sh . 2>/dev/null | cut -f1)
echo -e "${YELLOW}Current directory size: ${CONTEXT_SIZE}${NC}"

# Check if required API keys are set (optional, but recommended)
if [ -z "${GROQ_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
    echo -e "${YELLOW}⚠️  Warning: GROQ_API_KEY or OPENAI_API_KEY environment variable not set.${NC}"
    echo -e "${YELLOW}   Semantic search features will not work unless you set it in Cloud Run after deployment.${NC}"
    echo -e "${YELLOW}   You can set it later with:${NC}"
    echo -e "${YELLOW}   gcloud run services update ${SERVICE_NAME} --project=${PROJECT} --region=${REGION} --set-env-vars GROQ_API_KEY=your-key,OPENAI_API_KEY=your-key${NC}"
    echo ""
    read -p "Continue with deployment? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Deploy to Cloud Run
echo -e "${GREEN}Starting deployment...${NC}"
echo -e "${YELLOW}This may take several minutes. You'll see real-time progress below:${NC}"
echo ""

# Build deploy command (deploy without --allow-unauthenticated first to avoid IAM issues)
DEPLOY_CMD="gcloud run deploy ${SERVICE_NAME} \
  --project=${PROJECT} \
  --region=${REGION} \
  --source=. \
  --no-allow-unauthenticated \
  --platform=managed \
  --timeout=3600 \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=10"

# Add API keys if set
ENV_VARS=""
if [ -n "${GROQ_API_KEY:-}" ]; then
    ENV_VARS="${ENV_VARS}GROQ_API_KEY=${GROQ_API_KEY},"
fi
if [ -n "${OPENAI_API_KEY:-}" ]; then
    ENV_VARS="${ENV_VARS}OPENAI_API_KEY=${OPENAI_API_KEY},"
fi
if [ -n "${HUMAINS_USERNAME:-}" ]; then
    ENV_VARS="${ENV_VARS}HUMAINS_USERNAME=${HUMAINS_USERNAME},"
fi
if [ -n "${HUMAINS_PASSWORD:-}" ]; then
    ENV_VARS="${ENV_VARS}HUMAINS_PASSWORD=${HUMAINS_PASSWORD},"
fi
# Remove trailing comma if any vars were added
if [ -n "${ENV_VARS}" ]; then
    ENV_VARS="${ENV_VARS%,}"  # Remove trailing comma
    DEPLOY_CMD="${DEPLOY_CMD} --set-env-vars ${ENV_VARS}"
fi

# Deploy with real-time output (no --quiet flag)
# The output will stream directly to the terminal so user can see progress
# Use eval to properly handle the command string with environment variables
if eval "${DEPLOY_CMD}"; then
    
    # After successful deployment, set IAM policy to allow unauthenticated access
    echo ""
    echo -e "${YELLOW}Setting IAM policy to allow unauthenticated access...${NC}"
    if gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
      --project=${PROJECT} \
      --region=${REGION} \
      --member="allUsers" \
      --role="roles/run.invoker" \
      >/dev/null 2>&1; then
        echo -e "${GREEN}✅ IAM policy updated successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Warning: Could not set IAM policy automatically.${NC}"
        echo -e "${YELLOW}   The service is deployed but requires authentication.${NC}"
        echo -e "${YELLOW}   To allow public access, run:${NC}"
        echo "  gcloud run services add-iam-policy-binding ${SERVICE_NAME} \\"
        echo "    --project=${PROJECT} \\"
        echo "    --region=${REGION} \\"
        echo "    --member='allUsers' \\"
        echo "    --role='roles/run.invoker'"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}Getting service URL...${NC}"
    
    # Wait a moment for the service to be fully ready
    sleep 2
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
      --project=${PROJECT} \
      --region=${REGION} \
      --format='value(status.url)' 2>/dev/null)
    
    if [ -n "$SERVICE_URL" ]; then
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🎉 Your service is live!${NC}"
        echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    else
        echo -e "${YELLOW}⚠️  Could not retrieve service URL automatically.${NC}"
        echo -e "${YELLOW}Check the Cloud Console:${NC}"
        echo -e "${YELLOW}  https://console.cloud.google.com/run?project=${PROJECT}${NC}"
    fi
else
    DEPLOY_EXIT=$?
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo ""
    
    # Check for common errors and provide helpful messages
    echo -e "${YELLOW}Common issues and solutions:${NC}"
    echo ""
    echo -e "${YELLOW}Required IAM Roles:${NC}"
    echo -e "${YELLOW}  • Cloud Run Admin (roles/run.admin)${NC}"
    echo -e "${YELLOW}  • Artifact Registry Admin (roles/artifactregistry.admin)${NC}"
    echo -e "${YELLOW}  • Service Account User (roles/iam.serviceAccountUser)${NC}"
    echo -e "${YELLOW}  • Cloud Build Service Account (roles/cloudbuild.builds.editor)${NC}"
    echo ""
    echo -e "${YELLOW}To check your current permissions:${NC}"
    echo "  gcloud projects get-iam-policy ${PROJECT} --flatten='bindings[].members' --filter='bindings.members:raz@inprisltd.com' --format='table(bindings.role)'"
    echo ""
    echo -e "${YELLOW}To grant yourself permissions (if you're a project owner):${NC}"
    echo "  gcloud projects add-iam-policy-binding ${PROJECT} \\"
    echo "    --member='user:raz@inprisltd.com' \\"
    echo "    --role='roles/run.admin'"
    echo "  gcloud projects add-iam-policy-binding ${PROJECT} \\"
    echo "    --member='user:raz@inprisltd.com' \\"
    echo "    --role='roles/artifactregistry.admin'"
    echo ""
    echo -e "${YELLOW}Or ask your project admin to grant these roles.${NC}"
    echo ""
    echo -e "${YELLOW}Check build logs for detailed error information:${NC}"
    echo "  gcloud builds list --project=${PROJECT} --limit=1"
    echo ""
    exit $DEPLOY_EXIT
fi

