#!/bin/bash
set -e

echo "=================================================="
echo "       JayAvatar Microservices Setup (WSL/Linux)"
echo "=================================================="

# 1. Orchestrator Setup
echo "[INFO] Setting up Orchestrator..."
mkdir -p orchestrator
cd orchestrator
if [ ! -d "venv" ]; then
    echo "[INFO] Creating venv for Orchestrator..."
    python3 -m venv venv
fi
echo "[INFO] Installing Orchestrator dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
cd ..
echo "[SUCCESS] Orchestrator ready."

# 2. Audio Service Setup
echo ""
echo "[INFO] Setting up Audio Service (Coqui TTS)..."
mkdir -p services/audio
cd services/audio
if [ ! -d "venv" ]; then
    echo "[INFO] Creating venv for Audio..."
    python3 -m venv venv
fi
echo "[INFO] Installing Audio dependencies..."
source venv/bin/activate
pip install --upgrade pip
# Install PyTorch explicitly first
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
deactivate
cd ../..
echo "[SUCCESS] Audio Service ready."

# 3. Visual Service Setup
echo ""
echo "[INFO] Setting up Visual Service (Wav2Lip/Torch)..."
mkdir -p services/visual
cd services/visual
if [ ! -d "venv" ]; then
    echo "[INFO] Creating venv for Visual..."
    python3 -m venv venv
fi
echo "[INFO] Installing Visual dependencies..."
source venv/bin/activate
pip install --upgrade pip
# Install Visual-specific PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
deactivate
cd ../..
echo "[SUCCESS] Visual Service ready."

echo ""
echo "=================================================="
echo "[SUCCESS] All Microservices Configured!"
echo "=================================================="
