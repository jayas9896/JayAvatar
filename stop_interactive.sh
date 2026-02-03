#!/bin/bash
# Interactive script to stop services one by one

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"

echo "=========================================="
echo " Interactive Service Stopper"
echo "=========================================="
echo ""

SERVICES=("orchestrator" "audio" "visual" "motion" "pipeline")

for service in "${SERVICES[@]}"; do
    PID_FILE="$PID_DIR/$service.pid"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            read -p "Stop $service (PID: $PID)? (y/N): " answer
            if [[ "$answer" =~ ^[Yy]$ ]]; then
                kill $PID 2>/dev/null
                rm -f "$PID_FILE"
                echo "  ✅ $service stopped"
            else
                echo "  ⏭️  Skipped $service"
            fi
        else
            echo "  ⚠️  $service not running (removing stale PID)"
            rm -f "$PID_FILE"
        fi
    else
        echo "  ℹ️  $service: not tracked (no PID file)"
    fi
    echo ""
done

# Redis
read -p "Stop Redis server? (y/N): " stop_redis
if [[ "$stop_redis" =~ ^[Yy]$ ]]; then
    redis-cli shutdown 2>/dev/null && echo "  ✅ Redis stopped" || echo "  ⚠️  Redis not running"
else
    echo "  ⏭️  Skipped Redis"
fi

echo ""
echo "=========================================="
echo " Done!"
echo "=========================================="
