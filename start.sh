#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  CHITRAL CYBER SQUAD — Bot Startup Script
#  Started at: $(date)
# =============================================================================

LOG_DIR="$HOME/CCS_Bot/logs"
mkdir -p "$LOG_DIR"

BOT_DIR="$HOME/CCS_Bot"

# Kill any old instances
pkill -f "python ccsbot.py" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

# Start the bot
cd "$BOT_DIR"
nohup python ccsbot.py > "$LOG_DIR/bot.log" 2>&1 &
BOT_PID=$!
echo "Bot started with PID $BOT_PID"
echo $BOT_PID > "$LOG_DIR/bot.pid"

# Wait for bot to be ready
sleep 3

# Start cloudflared tunnel
nohup cloudflared tunnel --url http://localhost:8000 --no-autoupdate > "$LOG_DIR/tunnel.log" 2>&1 &
TUNNEL_PID=$!
echo "Tunnel started with PID $TUNNEL_PID"
echo $TUNNEL_PID > "$LOG_DIR/tunnel.pid"

# Wait for cloudflared to generate the URL
sleep 12

# Extract and save the URL
TUNNEL_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$LOG_DIR/tunnel.log" | head -1)
echo "$TUNNEL_URL" > "$LOG_DIR/tunnel_url.txt"

echo ""
echo "==========================================="
echo "  CCS Bot is running"
echo "==========================================="
echo "  Bot PID    : $BOT_PID"
echo "  Tunnel PID : $TUNNEL_PID"
echo "  Tunnel URL : $TUNNEL_URL"
echo ""
echo "  Webhook URL: $TUNNEL_URL/webhook"
echo "  Verify tok : ccs_secret_2026"
echo "==========================================="
