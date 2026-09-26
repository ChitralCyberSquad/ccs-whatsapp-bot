#!/data/data/com.termux/files/usr/bin/bash
LOG_DIR="$HOME/CCS_Bot/logs"

echo "Stopping CCS Bot..."
pkill -f "python ccsbot.py" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

echo "Stopped."
