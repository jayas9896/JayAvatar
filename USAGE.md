# JayAvatar - Usage Guide

This guide explains how to start the microservices, trigger jobs, and find the generated outputs.

## 1. Prerequisites
Ensure you are in the **WSL** environment (Ubuntu) and have run the setup script:
```bash
./setup_microservices.sh
```

## 2. Starting the Services
You need to run each component in a separate terminal window (or use `tmux`).

### Terminal 1: Redis
Start the Redis server (if not already running as a service):
```bash
redis-server
```

### Terminal 2: Orchestrator
The API server that manages jobs.
```bash
cd orchestrator
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*   **URL**: `http://localhost:8000`
*   **Docs**: `http://localhost:8000/docs` (Swagger UI)

### Terminal 3: Audio Service (TTS)
Generates audio from text using Coqui TTS.
```bash
cd services/audio
source venv/bin/activate
# Note: FORCE_CPU=1 is required for RTX 50-series compatibility with current PyTorch versions
FORCE_CPU=1 python worker.py
```

### Terminal 4: Visual Service (Wav2Lip)
Lip-syncs a face image/video to audio.
```bash
cd services/visual
source venv/bin/activate
FORCE_CPU=1 python worker.py
```

---

## 3. How to Run (Process Flow)

### Step 1: Generate Audio (TTS)
Send a POST request to `/generate`.

**Input**:
*   `text`: The text to speak.
*   `voice_id`: (Optional) Voice ID for Coqui TTS (defaults to `speaker.wav` cloning).

**Command**:
```bash
curl -X POST "http://localhost:8000/generate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, this is a test of the JayAvatar system."}'
```

**Response**:
```json
{"job_id": "uuid-string", "status": "queued"}
```
**Output Location**: `services/audio/outputs/<job_id>.wav`

### Step 2: Animate Face (Wav2Lip)
Once you have an audio file (from Step 1 or elsewhere) and a face image/video, send a request to `/animate`.

**Input**:
*   `audio_path`: Absolute path to the audio file.
*   `video_path`: Absolute path to the face image or video.

**Command**:
```bash
curl -X POST "http://localhost:8000/animate" \
     -H "Content-Type: application/json" \
     -d '{
           "audio_path": "/home/jayas/JayAvatar/services/audio/outputs/<AUDIO_JOB_ID>.wav",
           "video_path": "/home/jayas/JayAvatar/services/visual/test_face.png"
         }'
```
*(Note: Replace `<AUDIO_JOB_ID>` with the actual ID from Step 1, or use any valid path)*

**Response**:
```json
{"job_id": "uuid-string", "status": "queued"}
```
**Output Location**: `services/visual/outputs/<job_id>.mp4`

---

## 4. Checking Job Status
You can check the status of any job (audio or visual) using its Job ID.

**Command**:
```bash
curl "http://localhost:8000/status/<job_id>"
```

**Response (Example)**:
```json
{
  "id": "...",
  "status": "completed",
  "result": "/home/jayas/JayAvatar/services/visual/outputs/....mp4",
  ...
}
```

## 5. Troubleshooting
*   **Redis Connection Error**: Ensure `redis-server` is running.
*   **GPU Errors**: If you see CUDA errors, ensure `FORCE_CPU=1` is set before running output workers.
*   **Missing Dependencies**: Re-run `./setup_microservices.sh` or checks `requirements.txt` in the respective service folder.

## 6. One-Shot Pipeline (Text -> Video)
Automates the flow: Text -> Audio -> Video.

### 1. Start Pipeline Worker (Terminal 5)
```bash
cd orchestrator
source venv/bin/activate
python pipeline_worker.py
```

### 2. Run Pipeline Job
**Endpoint**: `POST /pipeline`

**Command**:
```bash
curl -X POST "http://localhost:8000/pipeline" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "This is a full pipeline executing correctly.",
           "video_path": "/home/jayas/JayAvatar/services/visual/test_face.png"
         }'
```

**Output**:
A **Unified Directory** is created at `JayAvatar/outputs/<JOB_ID>/`, containing:
*   `audio.wav`: The generated speech.
*   `video.mp4`: The final lip-synced video.
