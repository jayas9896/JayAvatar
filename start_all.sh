#!/bin/bash
# Start all JayAvatar services in the background
# Creates PID files for tracking

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

# --- Stop any existing services first ---
SERVICES=("orchestrator" "audio" "visual" "motion" "pipeline")
for service in "${SERVICES[@]}"; do
    PID_FILE="$PID_DIR/$service.pid"
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "[*] Stopping existing $service (PID: $OLD_PID)..."
            kill $OLD_PID 2>/dev/null
            sleep 0.5
        fi
        rm -f "$PID_FILE"
    fi
done

echo "=========================================="
echo "     Starting JayAvatar Services"
echo "=========================================="

# 1. Redis (if not already running)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "[*] Starting Redis..."
    redis-server --daemonize yes
    echo "✅ Redis started"
else
    echo "✅ Redis already running"
fi

# 2. Orchestrator API
echo "[*] Starting Orchestrator API..."
cd "$SCRIPT_DIR/orchestrator"
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/orchestrator.log" 2>&1 &
echo $! > "$PID_DIR/orchestrator.pid"
deactivate
echo "✅ Orchestrator started (PID: $(cat $PID_DIR/orchestrator.pid))"

# 3. Audio Worker
echo "[*] Starting Audio Worker..."
cd "$SCRIPT_DIR/services/audio"
source venv/bin/activate
nohup python worker.py > "$LOG_DIR/audio.log" 2>&1 &
echo $! > "$PID_DIR/audio.pid"
deactivate
echo "✅ Audio Worker started (PID: $(cat $PID_DIR/audio.pid))"

# 4. Visual Worker
echo "[*] Starting Visual Worker..."
cd "$SCRIPT_DIR/services/visual"
source venv/bin/activate
nohup python worker.py > "$LOG_DIR/visual.log" 2>&1 &
echo $! > "$PID_DIR/visual.pid"
deactivate
echo "✅ Visual Worker started (PID: $(cat $PID_DIR/visual.pid))"

# 5. Motion Worker
echo "[*] Starting Motion Worker..."
cd "$SCRIPT_DIR/services/motion"
source venv/bin/activate
nohup python worker.py > "$LOG_DIR/motion.log" 2>&1 &
echo $! > "$PID_DIR/motion.pid"
deactivate
echo "✅ Motion Worker started (PID: $(cat $PID_DIR/motion.pid))"

# 6. Pipeline Worker
echo "[*] Starting Pipeline Worker..."
cd "$SCRIPT_DIR/orchestrator"
source venv/bin/activate
nohup python pipeline_worker.py > "$LOG_DIR/pipeline.log" 2>&1 &
echo $! > "$PID_DIR/pipeline.pid"
deactivate
echo "✅ Pipeline Worker started (PID: $(cat $PID_DIR/pipeline.pid))"

echo ""
echo "=========================================="
echo "     All Services Started!"
echo "=========================================="
echo "Logs:     $LOG_DIR/"
echo "PIDs:     $PID_DIR/"
echo "API:      http://localhost:8000"
echo ""
echo "Run './stop_all.sh' to stop all services."
