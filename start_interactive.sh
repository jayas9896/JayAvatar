#!/bin/bash
# Interactive script to start services one by one

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

echo "=========================================="
echo " Interactive Service Starter"
echo "=========================================="
echo ""

# Helper function to start a service
start_service() {
    local name=$1
    local dir=$2
    local cmd=$3
    local log_file="$LOG_DIR/$name.log"
    local pid_file="$PID_DIR/$name.pid"
    
    # Check if already running
    if [ -f "$pid_file" ]; then
        OLD_PID=$(cat "$pid_file")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "  ⚠️  $name already running (PID: $OLD_PID)"
            read -p "  Kill and restart? (y/N): " restart
            if [[ "$restart" =~ ^[Yy]$ ]]; then
                kill $OLD_PID 2>/dev/null
                sleep 0.5
            else
                echo "  ⏭️  Skipped $name"
                return
            fi
        fi
    fi
    
    read -p "Start $name? (Y/n): " answer
    if [[ ! "$answer" =~ ^[Nn]$ ]]; then
        cd "$SCRIPT_DIR/$dir"
        source venv/bin/activate
        nohup $cmd > "$log_file" 2>&1 &
        echo $! > "$pid_file"
        deactivate
        echo "  ✅ $name started (PID: $(cat $pid_file))"
    else
        echo "  ⏭️  Skipped $name"
    fi
    echo ""
}

# Redis check
if ! pgrep -x "redis-server" > /dev/null; then
    read -p "Redis not running. Start it? (Y/n): " start_redis
    if [[ ! "$start_redis" =~ ^[Nn]$ ]]; then
        redis-server --daemonize yes
        echo "  ✅ Redis started"
    fi
else
    echo "✅ Redis already running"
fi
echo ""

# Services
start_service "orchestrator" "orchestrator" "uvicorn main:app --host 0.0.0.0 --port 8000"
start_service "audio" "services/audio" "python worker.py"
start_service "visual" "services/visual" "python worker.py"
start_service "motion" "services/motion" "python worker.py"
start_service "pipeline" "orchestrator" "python pipeline_worker.py"

echo "=========================================="
echo " Done!"
echo "=========================================="
echo "Logs: $LOG_DIR/"
