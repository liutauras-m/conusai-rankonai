#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
OWNER="liutauras-m"
REPO="conusai-rankonai"
PLATFORM="linux/amd64"
TAG="${1:-latest}"

FRONTEND_IMAGE="${REGISTRY}/${OWNER}/${REPO}-frontend:${TAG}"
BACKEND_IMAGE="${REGISTRY}/${OWNER}/${REPO}-backend:${TAG}"

# Load .env file if exists
ENV_FILE="./frontend/.env"
if [ -f "$ENV_FILE" ]; then
    # Extract GITHUB_API_KEY from .env (handles export and quotes)
    GITHUB_TOKEN=$(grep -E "^(export )?GITHUB_API_KEY=" "$ENV_FILE" | sed 's/^export //' | cut -d'=' -f2 | tr -d '"')
fi

# Fallback to root .env
if [ -z "$GITHUB_TOKEN" ] && [ -f "./.env" ]; then
    GITHUB_TOKEN=$(grep -E "^(export )?GITHUB_TOKEN=" "./.env" | sed 's/^export //' | cut -d'=' -f2 | tr -d '"')
fi

echo -e "${YELLOW}🚀 Building and publishing images for ${PLATFORM}${NC}"
echo -e "${YELLOW}   Tag: ${TAG}${NC}"
echo ""

# Login to GHCR if token available
if [ -n "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}🔐 Logging in to ${REGISTRY}...${NC}"
    echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$OWNER" --password-stdin
    echo ""
fi

echo -e "${GREEN}✅ Logged in to ${REGISTRY}${NC}"
echo ""

# Create buildx builder if it doesn't exist
if ! docker buildx inspect multiarch-builder &>/dev/null; then
    echo -e "${YELLOW}📦 Creating buildx builder...${NC}"
    docker buildx create --name multiarch-builder --use
fi
docker buildx use multiarch-builder

# Build and push Frontend
echo -e "${YELLOW}📦 Building frontend for ${PLATFORM}...${NC}"
docker buildx build \
    --platform ${PLATFORM} \
    --build-arg BACKEND_URL=http://backend:8000 \
    -t ${FRONTEND_IMAGE} \
    --push \
    ./frontend

echo -e "${GREEN}✅ Frontend pushed: ${FRONTEND_IMAGE}${NC}"

# Build and push Backend
echo -e "${YELLOW}📦 Building backend for ${PLATFORM}...${NC}"
docker buildx build \
    --platform ${PLATFORM} \
    -t ${BACKEND_IMAGE} \
    --push \
    ./backend

echo -e "${GREEN}✅ Backend pushed: ${BACKEND_IMAGE}${NC}"

echo ""
echo -e "${GREEN}🎉 All images published successfully!${NC}"
echo ""
echo -e "Images:"
echo -e "  - ${FRONTEND_IMAGE}"
echo -e "  - ${BACKEND_IMAGE}"
echo ""
echo -e "Deploy on Dokploy with:"
echo -e "  IMAGE_TAG=${TAG} docker stack deploy -c docker-compose.prod.yml rankonai"
