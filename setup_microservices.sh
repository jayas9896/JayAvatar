#!/bin/bash
set -e

echo "=================================================="
echo "       JayAvatar Microservices Setup (WSL/Linux)"
echo "       Updated for GPU & High Quality (CUDA 13)"
echo "=================================================="

# 0. System Checks
echo "[INFO] Checking system dependencies..."
if ! command -v redis-server &> /dev/null; then
    echo "[WARNING] redis-server not found! Please install it (e.g., sudo apt install redis-server)."
fi
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] ffmpeg not found! Please install it (e.g., sudo apt install ffmpeg)."
fi

# Function to setup a service
setup_service() {
    SERVICE_NAME=$1
    DIR_PATH=$2
    
    echo ""
    echo "[INFO] Setting up $SERVICE_NAME..."
    mkdir -p "$DIR_PATH"
    pushd "$DIR_PATH" > /dev/null

    # Nuke existing venv to ensure clean update
    if [ -d "venv" ]; then
        echo "[INFO] Removing old venv..."
        rm -rf venv
    fi

    echo "[INFO] Creating new venv..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "[INFO] Upgrading pip..."
    pip install --upgrade pip

    # Check if requirements exist
    if [ -f "requirements.txt" ]; then
        echo "[INFO] Installing dependencies from requirements.txt..."
        # We rely on requirements.txt having the --index-url for cu130 now
        pip install -r requirements.txt
    else
        echo "[WARNING] No requirements.txt found in $DIR_PATH"
    fi
    
    deactivate
    popd > /dev/null
    echo "[SUCCESS] $SERVICE_NAME ready."
}

# 1. Orchestrator
setup_service "Orchestrator" "orchestrator"

# 2. Audio Service
setup_service "Audio Service" "services/audio"

# 3. Visual Service
setup_service "Visual Service" "services/visual"

# 4. Motion Service (SadTalker)
setup_service "Motion Service" "services/motion"

# --- SadTalker Specific: Download Weights ---
echo ""
echo "[INFO] Downloading SadTalker Checkpoints..."
ST_CHECKPOINT_DIR="services/motion/SadTalker/checkpoints"
ST_GFPGAN_DIR="services/motion/SadTalker/gfpgan/weights"
mkdir -p "$ST_CHECKPOINT_DIR"
mkdir -p "$ST_GFPGAN_DIR"

download_if_missing() {
    url=$1
    dest=$2
    if [ ! -f "$dest" ]; then
        echo "      Downloading $(basename $dest)..."
        wget -q --show-progress -O "$dest" "$url"
    else
        echo "      $(basename $dest) exists."
    fi
}

download_if_missing "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109.pth" "$ST_CHECKPOINT_DIR/mapping_00109.pth"
download_if_missing "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors" "$ST_CHECKPOINT_DIR/SadTalker_V0.0.2_256.safetensors"
download_if_missing "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors" "$ST_CHECKPOINT_DIR/SadTalker_V0.0.2_512.safetensors"

# Face Enhancer
download_if_missing "https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth" "$ST_GFPGAN_DIR/alignment_WFLW_4HG.pth"
download_if_missing "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth" "$ST_GFPGAN_DIR/GFPGANv1.4.pth"

# Fix for common issue: download default config matching pytorch version if slightly off?
# Not needed if we use safetensors.

echo ""
echo "=================================================="
echo "[SUCCESS] All Microservices Re-Configured!"
echo "=================================================="
echo "Run services with:"
echo "1. redis-server"
echo "2. cd orchestrator && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"
echo "3. cd services/audio && source venv/bin/activate && python worker.py"
echo "4. cd services/visual && source venv/bin/activate && python worker.py"
echo "5. cd services/motion && source venv/bin/activate && python worker.py"
echo "6. cd orchestrator && source venv/bin/activate && python pipeline_worker.py"
