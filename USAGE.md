# JayAvatar Usage Guide

## Quick Start

```bash
# Start all services
./start_all.sh

# Check status
curl http://localhost:8000/health
```

## Pipeline API

Generate talking avatar videos from text.

### Endpoint
```
POST http://localhost:8000/pipeline
```

### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | ✅ | - | The text to speak |
| `video_path` | string | ✅ | - | Path to face image/video |
| `voice_id` | string | ❌ | null | Custom voice reference |
| `mode` | string | ❌ | `"motion"` | Animation mode (see below) |

### Animation Modes

| Mode | Engine | Features | Speed |
|------|--------|----------|-------|
| `"motion"` | SadTalker | Lip-sync + head motion + blinking | ~60s |
| `"lipsync"` | Wav2Lip | Lip-sync only (static head) | ~15s |
| `"emage"` | EMAGE | Full body + gestures (coming soon) | TBD |

### Examples

**Default (natural head motion):**
```bash
curl -X POST "http://localhost:8000/pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test with natural head movement.",
    "video_path": "/path/to/face.jpg"
  }'
```

**Fast lip-sync only:**
```bash
curl -X POST "http://localhost:8000/pipeline" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quick lip sync without head motion.",
    "video_path": "/path/to/face.jpg",
    "mode": "lipsync"
  }'
```

### Response

```json
{
  "job_id": "abc123-...",
  "status": "queued"
}
```

### Check Job Status

```bash
curl http://localhost:8000/status/{job_id}
```

### Output Location

Videos are saved to: `outputs/{job_id}/video.mp4`

---

## Individual Services

### Audio Generation (TTS)
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

### Visual Only (Wav2Lip)
```bash
curl -X POST "http://localhost:8000/animate" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "/path/to/audio.wav",
    "video_path": "/path/to/face.jpg"
  }'
```

### Motion Only (SadTalker)
```bash
curl -X POST "http://localhost:8000/motion" \
  -H "Content-Type: application/json" \
  -d '{
    "source_image": "/path/to/face.jpg",
    "driven_audio": "/path/to/audio.wav"
  }'
```

---

## Service Management

| Script | Description |
|--------|-------------|
| `./start_all.sh` | Start all services |
| `./stop_all.sh` | Stop all services |
| `./start_interactive.sh` | Start with Y/N prompts |
| `./stop_interactive.sh` | Stop with Y/N prompts |
| `./restart_interactive.sh` | Restart with Y/N prompts |

## Logs

```bash
tail -f logs/orchestrator.log  # API server
tail -f logs/audio.log         # TTS worker
tail -f logs/visual.log        # Wav2Lip worker
tail -f logs/motion.log        # SadTalker worker
tail -f logs/pipeline.log      # Pipeline orchestrator
```
