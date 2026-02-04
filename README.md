# JayAvatar 🎭

AI-powered talking avatar generator. Create lip-synced videos with natural head motion from just text and a face image.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GPU](https://img.shields.io/badge/GPU-NVIDIA-76B900)

## Features

- 🎤 **Text-to-Speech** - XTTS v2 with multi-language support (English, Hindi, Telugu)
- 👄 **Lip Sync** - Wav2Lip for accurate mouth movement
- 🎬 **Natural Motion** - SadTalker for head motion + blinking
- 📝 **Subtitles** - Auto-generated SRT files
- ⚡ **Parallel Processing** - Configurable concurrent jobs
- 🔧 **Microservices** - Redis-based job queue architecture

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/JayAvatar.git
cd JayAvatar

# Setup (downloads models, creates venvs)
./setup_microservices.sh

# Start all services
./start_all.sh

# Generate a video
curl -X POST http://localhost:8000/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! This is JayAvatar speaking.",
    "video_path": "/path/to/face.jpg"
  }'
```

## Requirements

- **Python 3.12+**
- **NVIDIA GPU** with 8GB+ VRAM
- **CUDA 13.x**
- **Redis** server

## Architecture

```
┌─────────────────┐
│   Orchestrator  │ ← FastAPI (port 8000)
│    /pipeline    │
└────────┬────────┘
         │ Redis Queue
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌────────┐ ┌────────┐
│ Audio │ │ Visual │ │ Motion │
│ XTTS  │ │Wav2Lip │ │SadTalk │
└───────┘ └────────┘ └────────┘
```

## Animation Modes

| Mode | Engine | What it does |
|------|--------|--------------|
| `motion` | SadTalker | Lip-sync + head motion + blinking |
| `lipsync` | Wav2Lip | Fast lip-sync only |
| `emage` | EMAGE | Full body (coming soon) |

## Configuration

Edit `config.yaml` or use environment variables:

```yaml
pipeline:
  max_concurrent: 3

motion:
  timeout_seconds: 300
```

```bash
MAX_CONCURRENT_PIPELINES=5 ./start_all.sh
```

## Documentation

See [USAGE.md](USAGE.md) for full API documentation.

## License

MIT License - see [LICENSE](LICENSE)
