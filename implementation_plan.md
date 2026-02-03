# JayAvatar Implementation Plan

# Goal Description
Create a local, high-end AI video generation pipeline that can produce videos of the user ("Jay") speaking or performing actions based on text input. The system lays the foundation for "Text-to-Video" using the user's own identity.

## User Review Required
> [!IMPORTANT]
> **Hardware Requirements**: This pipeline requires a modern NVIDIA GPU (RTX 3060 or better recommended) with at least 8GB-12GB VRAM particularly for the image generation and rendering models.
>
> **Model Selection Decisions**:
> 1.  **Audio**: Selected **Coqui XTTS v2** for high-quality voice cloning. It requires a 6-10 second sample of your voice.
> 2.  **Talking Head**: Selected **SadTalker** (Image+Audio) and **Wav2Lip-GAN** (Video+Audio). *Reason*: Best open-source balance of quality and strict lip-sync.
> 3.  **Action/Motion**: Selected **Champ** (or Moore-AnimateAnyone) for full-body motivation. *Note*: This is experimental and computationally heavy. We will prioritize the "Talking Head" module first.

## System Architecture: Robust Microservices
The system uses a **Microservices Architecture** to isolate heavy dependencies and ensure stability. Each service runs in its own **Virtual Environment (venv)** and communicates via a persistent **Redis Job Queue**.

### Core Components
1.  **Orchestrator (The Manager)**
    - **Tech**: FastAPI + Redis.
    - **Role**: Accepts user requests, breaks them into tasks (Audio Generation -> Video Generation -> Muxing), and pushes them to the queue. Tracks global state.
    - **Fault Tolerance**: Jobs are persisted in Redis. If the system crashes, the Orchestrator resumes processing pending/in-progress jobs upon restart.

2.  **Audio Microservice (The Voice)**
    - **Tech**: Coqui XTTS v2, Python 3.10.
    - **Environment**: `venv_audio` (prevents conflict with video libraries).
    - **Input**: Text + Speaker Embedding.
    - **Output**: WAV file path.

3.  **Visual Microservice (The Avatar)**
    - **Tech**: Wav2Lip-GAN / SadTalker, PyTorch (CUDA).
    - **Environment**: `venv_visual` (Heavy GPU dependencies).
    - **Input**: Audio path + Reference Image/Video.
    - **Output**: Silent MP4 path.

4.  **Compositor Microservice (The Editor)**
    - **Tech**: FFmpeg.
    - **Environment**: `venv_core` (Lightweight).
    - **Role**: Merges Audio + Video, adds background, runs final checks.

### Fault Tolerance & Reliability
- **Persistent State**: Usage of Redis AOF (Append Only File) to ensure no job is lost on power loss.
- **Atomic Steps**: Each pipeline step saves its output to disk before marking "Complete". On restart, the system checks for existing outputs to skip redundant work.

## Phasing

### Phase 1: The "Talking Head" Core (Current Priority)
- **Goal**: Realistic, lip-synced video of user speaking.
- **Scope**:
    - Infrastructure: Redis + Orchestrator + Separate Venvs.
    - Audio: High-quality Voice Cloning.
    - Visual: `Wav2Lip` / `SadTalker` implementation.
    - No "Full Body" generation yet (to minimize hallucinations).

### Phase 2: Action & Full Body (Future)
- **Goal**: User performing actions (walking, jumping).
- **Scope**:
    - Integration of `Champ` or `AnimateAnyone`.
    - Advanced background consistency checks.

## Dependencies & Setup
Each service has its own `requirements.txt` and `setup.bat`.
- `services/audio/requirements.txt`
- `services/visual/requirements.txt`
- `orchestrator/requirements.txt`

## Verification Plan

### Automated Tests
- Unit tests for Audio generation (check file output stats).
- Integration test for full pipeline using a short "Hello World" text.

### Manual Verification
- **Audio Quality**: Listen to generated voice for similarity to user.
- **Lip Sync**: Visually verify that lip movements match the audio vowels.
- **Performance**: Monitor GPU VRAM usage to ensure no OOM (Out of Memory) crashes.
