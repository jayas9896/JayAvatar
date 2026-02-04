#!/bin/bash
# Stop all JayAvatar services

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"

echo "=========================================="
echo "     Stopping JayAvatar Services"
echo "=========================================="

SERVICES=("pipeline" "motion" "visual" "audio" "orchestrator")

for service in "${SERVICES[@]}"; do
    PID_FILE="$PID_DIR/$service.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "[*] Stopping $service (PID: $PID)..."
            kill $PID 2>/dev/null
            rm -f "$PID_FILE"
            echo "✅ $service stopped"
        else
            echo "⚠️  $service not running (stale PID file removed)"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  $service: No PID file found"
    fi
done

echo ""
echo "=========================================="
echo "     All Services Stopped"
echo "=========================================="
echo "(Redis left running - managed as system daemon)"
