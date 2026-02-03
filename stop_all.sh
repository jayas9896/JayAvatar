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

# Optional: Stop Redis
read -p "Stop Redis server? (y/N): " stop_redis
if [[ "$stop_redis" =~ ^[Yy]$ ]]; then
    redis-cli shutdown 2>/dev/null && echo "✅ Redis stopped" || echo "⚠️  Redis not running or couldn't stop"
fi

echo ""
echo "=========================================="
echo "     All Services Stopped"
echo "=========================================="
