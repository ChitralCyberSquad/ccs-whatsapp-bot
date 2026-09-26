#!/data/data/com.termux/files/usr/bin/bash
LOG_DIR="$HOME/CCS_Bot/logs"

echo "=== CCS Bot Status ==="
echo ""

# Bot
if pgrep -f "python ccsbot.py" > /dev/null; then
    echo "✅ Bot: RUNNING (PID $(pgrep -f 'python ccsbot.py' | head -1))"
else
    echo "❌ Bot: NOT RUNNING"
fi

# Tunnel
if pgrep -f "cloudflared tunnel" > /dev/null; then
    echo "✅ Tunnel: RUNNING (PID $(pgrep -f 'cloudflared tunnel' | head -1))"
else
    echo "❌ Tunnel: NOT RUNNING"
fi

echo ""
echo "=== Tunnel URL ==="
if [ -f "$LOG_DIR/tunnel_url.txt" ]; then
    cat "$LOG_DIR/tunnel_url.txt"
    echo ""
    echo "Webhook URL: $(cat "$LOG_DIR/tunnel_url.txt")/webhook"
else
    echo "(not yet generated)"
fi

echo ""
echo "=== Last 5 bot log lines ==="
tail -5 "$LOG_DIR/bot.log" 2>/dev/null

echo ""
echo "=== Last 5 tunnel log lines ==="
tail -5 "$LOG_DIR/tunnel.log" 2>/dev/null
