#!/bin/bash
# Interactive script to restart services one by one

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

echo "=========================================="
echo " Interactive Service Restarter"
echo "=========================================="
echo ""

# Helper function to restart a service
restart_service() {
    local name=$1
    local dir=$2
    local cmd=$3
    local log_file="$LOG_DIR/$name.log"
    local pid_file="$PID_DIR/$name.pid"
    
    # Check current status
    status="not running"
    if [ -f "$pid_file" ]; then
        OLD_PID=$(cat "$pid_file")
        if ps -p $OLD_PID > /dev/null 2>&1; then
            status="running (PID: $OLD_PID)"
        fi
    fi
    
    read -p "Restart $name [$status]? (y/N): " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        # Stop if running
        if [ -f "$pid_file" ]; then
            OLD_PID=$(cat "$pid_file")
            if ps -p $OLD_PID > /dev/null 2>&1; then
                echo "  [*] Stopping $name..."
                kill $OLD_PID 2>/dev/null
                sleep 0.5
            fi
            rm -f "$pid_file"
        fi
        
        # Start fresh
        cd "$SCRIPT_DIR/$dir"
        source venv/bin/activate
        nohup $cmd > "$log_file" 2>&1 &
        echo $! > "$pid_file"
        deactivate
        echo "  ✅ $name restarted (PID: $(cat $pid_file))"
    else
        echo "  ⏭️  Skipped $name"
    fi
    echo ""
}

# Services
restart_service "orchestrator" "orchestrator" "uvicorn main:app --host 0.0.0.0 --port 8000"
restart_service "audio" "services/audio" "python worker.py"
restart_service "visual" "services/visual" "python worker.py"
restart_service "motion" "services/motion" "python worker.py"
restart_service "pipeline" "orchestrator" "python pipeline_worker.py"

echo "=========================================="
echo " Done!"
echo "=========================================="
