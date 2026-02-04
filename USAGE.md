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

---

## Configuration

Settings are loaded from `config.yaml` with environment variable overrides.

### Edit `config.yaml`

```yaml
pipeline:
  max_concurrent: 3      # Parallel pipeline jobs

motion:
  timeout_seconds: 300   # 5 min timeout
  size: 512              # Video resolution
  still: true            # Anchor face position

audio:
  timeout_seconds: 120

visual:
  timeout_seconds: 180
```

### Environment Variable Overrides

| Setting | Env Var | Default |
|---------|---------|---------|
| Pipeline concurrency | `MAX_CONCURRENT_PIPELINES` | 3 |
| Motion timeout | `MOTION_TIMEOUT` | 300s |
| Audio timeout | `AUDIO_TIMEOUT` | 120s |
| Visual timeout | `VISUAL_TIMEOUT` | 180s |

**Example:**
```bash
MAX_CONCURRENT_PIPELINES=5 MOTION_TIMEOUT=600 ./start_all.sh
```

---

## Logs

```bash
tail -f logs/orchestrator.log  # API server
tail -f logs/audio.log         # TTS worker
tail -f logs/visual.log        # Wav2Lip worker
tail -f logs/motion.log        # SadTalker worker
tail -f logs/pipeline.log      # Pipeline orchestrator
```

---

## Testing

### Run Tests Locally

```bash
pip install pydantic pyyaml
python3 tests/test_basic.py
```

### Test Coverage

| Test | Description |
|------|-------------|
| `test_imports` | Verify core modules load |
| `test_schema_validation` | Pydantic model validation |
| `test_config_defaults` | Config returns valid defaults |
| `test_srt_generation` | Subtitle file generation |
| `test_assets_exist` | Sample files present |

### Test Assets

Located in `tests/assets/`:
- `test_face.jpg` - Sample face image for testing

### GitHub Actions

Tests run automatically on:
- Push to `main` or `feature/*`
- Pull requests to `main`

> **Note:** GPU inference tests are skipped on GitHub (no GPU available).


