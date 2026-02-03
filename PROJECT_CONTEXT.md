# JayAvatar Project Context & Migration Guide

**Date**: 2026-02-03
**Status**: Infrastructure Setup Phase

## 1. Project Objective
Create a high-end, local AI video generation pipeline ("JayAvatar") that can produce videos of the user speaking or performing actions.
*   **Goal**: Realistic "Text-to-Video" using the user's authentic voice and visual likeness.
*   **Quality Standard**: Premium, realistic output avoiding typical AI artifacts (e.g., "6 fingers", morphing backgrounds).

## 2. Architecture: Microservices
To handle conflicting dependencies (Audio libraries vs. Visual libraries) and ensure robustness, we adopted a **Microservices Architecture**.

### The Trio
1.  **Orchestrator (Manager)**
    *   **Stack**: FastAPI, Redis.
    *   **Role**: Manages the job queue. If the system crashes, it resumes from the last state saved in Redis.
2.  **Audio Service (The Voice)**
    *   **Stack**: Coqui XTTS v2, Python 3.10.
    *   **Role**: Clones user voice from a reference sample.
    *   **Env**: `services/audio/venv`
3.  **Visual Service (The Avatar)**
    *   **Stack**: Wav2Lip-GAN / SadTalker, PyTorch (CUDA).
    *   **Role**: Syncs lip movements of a real video/image to the generated audio.
    *   **Env**: `services/visual/venv`

## 3. Key Decisions & Discussions
*   **Hybrid Realism Strategy**: To avoid "uncanny valley" or "hallucinations" (extra fingers), we decided to use **Lip-Sync on Real Video** (Wav2Lip) rather than full-body generation (Champ) for the initial phase. This ensures the body and background remain 100% authentic.
*   **Redis**: Chosen for the job queue to ensure fault tolerance.
*   **WSL Migration**: The project is being moved to WSL for better compatibility with AI/Linux-first libraries.

## 4. Work Completed
*   [x] Requirements defined for all 3 services.
*   [x] Architecture approved.
*   [x] Folder structure created.
*   [ ] (Next) Run setup scripts in WSL.
*   [ ] (Next) Install Redis in WSL (`sudo apt install redis`).

## 5. WSL Setup Instructions
Use the `setup_microservices.sh` script to set up the environment:

1.  **Install System Dependencies**:
    ```bash
    sudo apt update && sudo apt install python3-venv python3-pip ffmpeg redis
    ```
2.  **Run Setup Script**:
    ```bash
    chmod +x setup_microservices.sh
    ./setup_microservices.sh
    ```
3.  **Start Redis**:
    ```bash
    sudo service redis-server start
    ```
