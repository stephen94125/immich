#!/bin/bash

# ================= Configuration =================
PYTHON_PATCH_SCRIPT="patch_onnx_models.py"

# Local temporary directories
LOCAL_ORIGIN_DIR="./origin_weights"
LOCAL_PATCHED_DIR="./patched_weights"
# =============================================

# Color definitions
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage information
show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 <namespace> <release_name>"
    echo ""
    echo -e "${YELLOW}Arguments:${NC}"
    echo -e "  namespace     The Kubernetes namespace where Immich is deployed (e.g., 'immich' or 'personal')"
    echo -e "  release_name  The Helm release name of your Immich deployment (e.g., 'immich')"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo -e "  $0 personal immich"
    echo -e "  $0 default my-immich-app"
    exit 1
}

# Check if arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo -e "${RED}❌ Error: Missing required arguments.${NC}"
    show_usage
fi

NAMESPACE="$1"
RELEASE_NAME="$2"

echo -e "${CYAN}🚀 Starting Immich ML Model Patcher${NC}"
echo -e "   Namespace   : ${GREEN}${NAMESPACE}${NC}"
echo -e "   Release Name: ${GREEN}${RELEASE_NAME}${NC}"
echo ""

# 1. Automatically find the Pod name
echo -e "${CYAN}🔍 Finding Machine Learning Pod...${NC}"
# Use kubectl get pods with grep to find the pod.
# We assume the standard naming convention used by Immich Helm charts: <release>-machine-learning
POD_NAME=$(kubectl get pods -n "${NAMESPACE}" | grep "${RELEASE_NAME}-machine-learning" | awk '{print $1}' | head -n 1)

if [ -z "$POD_NAME" ]; then
    echo -e "${RED}❌ Error: Could not find any pod matching '${RELEASE_NAME}-machine-learning' in namespace '${NAMESPACE}'${NC}"
    exit 1
fi

echo -e "   🎯 Target Pod: ${YELLOW}${POD_NAME}${NC}"
echo ""

# 2. Download models (Filtering out metadata)
echo -e "${CYAN}⬇️  Downloading models from Pod... (Skipping metadata)${NC}"
echo -e "   Source: ${YELLOW}${POD_NAME}:/cache${NC}"
echo -e "   Dest  : ${YELLOW}${LOCAL_ORIGIN_DIR}${NC}"

# Ensure directory exists and is clean
rm -rf "${LOCAL_ORIGIN_DIR}"
mkdir -p "${LOCAL_ORIGIN_DIR}"

# Use Tar Pipe trick to download while excluding specific metadata directories
# This avoids downloading unnecessary cache/metadata files.
kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- tar cf - \
    --exclude='huggingface-xet' \
    --exclude='matplotlib-config' \
    -C /cache . | tar xf - -C "${LOCAL_ORIGIN_DIR}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Download complete.${NC}"
else
    echo -e "${RED}❌ Download failed. Please check your kubectl connection/permissions.${NC}"
    exit 1
fi
echo ""

# 3. Run Python Patch Script
echo -e "${CYAN}🔧 Running Python Patch Script...${NC}"

if [ ! -f "${PYTHON_PATCH_SCRIPT}" ]; then
    echo -e "${RED}❌ Error: Python script '${PYTHON_PATCH_SCRIPT}' not found!${NC}"
    exit 1
fi

# Execute using 'uv' (assuming uv is installed and manages the environment)
uv run "${PYTHON_PATCH_SCRIPT}"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Patching script failed. Aborting upload.${NC}"
    exit 1
fi
echo ""

# 4. Upload patched models
echo -e "${CYAN}⬆️  Uploading patched weights to Pod...${NC}"
echo -e "   Source: ${YELLOW}${LOCAL_PATCHED_DIR}${NC}"
echo -e "   Dest  : ${YELLOW}${POD_NAME}:/cache${NC}"

# Check if patched directory exists
if [ ! -d "${LOCAL_PATCHED_DIR}" ]; then
    echo -e "${RED}❌ Error: Patched directory '${LOCAL_PATCHED_DIR}' not found. Did the python script run correctly?${NC}"
    exit 1
fi

# Upload logic:
# We iterate through the top-level directories in patched_weights (e.g., ocr, clip, facial-recognition)
# and copy them one by one into the pod's /cache directory.
# This prevents creating a nested /cache/patched_weights structure.
echo -e "   (Overwriting existing files in Pod...)"

found_dirs=false
for DIR in "${LOCAL_PATCHED_DIR}"/*; do
    if [ -d "$DIR" ]; then
        found_dirs=true
        DIR_NAME=$(basename "$DIR")
        echo -e "   📦 Uploading ${DIR_NAME}..."
        kubectl cp -n "${NAMESPACE}" "$DIR" "${POD_NAME}:/cache/${DIR_NAME}"
    fi
done

if [ "$found_dirs" = false ]; then
     echo -e "${YELLOW}⚠️  Warning: No subdirectories found in ${LOCAL_PATCHED_DIR} to upload.${NC}"
fi

echo ""
echo -e "${GREEN}✨ All Done! Your Immich ML Pod has been patched.${NC}"
echo -e "   You might want to restart the pod to ensure models are reloaded:"
echo -e "   ${YELLOW}kubectl delete pod -n ${NAMESPACE} ${POD_NAME}${NC}"
