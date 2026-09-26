#!/usr/bin/env python3
# =============================================================================
#  CHITRAL CYBER SQUAD — WhatsApp Bot (no crypto dependency)
#  Admin : ZIA AKBAR
#  Requires only: flask, requests, colorama, beautifulsoup4, dnspython
# =============================================================================

import os, sys, json, time, ssl, socket, threading, re
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    from flask import Flask, request, jsonify
    from colorama import Fore, Style, init
    init(autoreset=True)
    R, G, Y, C, M, W, B, X = (Fore.RED, Fore.GREEN, Fore.YELLOW,
                              Fore.CYAN, Fore.MAGENTA, Fore.WHITE,
                              Style.BRIGHT, Style.RESET_ALL)
except ImportError as e:
    print(f"[!] Missing: {e}")
    print("[!] pip install flask requests colorama beautifulsoup4 dnspython")
    sys.exit(1)

# =============================================================================
#  LOAD ENV
# =============================================================================
def load_env():
    env_path = os.path.expanduser("~/CCS_Bot/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

load_env()

WA_TOKEN    = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WA_PHONE_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
MY_NUMBER   = os.environ.get("WHATSAPP_MY_NUMBER", "")
ADMIN       = os.environ.get("ADMIN_NUMBER", MY_NUMBER)
VERIFY      = os.environ.get("WEBHOOK_VERIFY_TOKEN", "ccs_secret_2026")
GEMINI_KEY  = os.environ.get("GEMINI_API_KEY", "")

SITES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sites.txt")
LOG_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ccsbot.log")

app = Flask(__name__)

# =============================================================================
#  UI
# =============================================================================
def clear(): os.system('clear')

def banner():
    clear()
    print(f"{C}{B}")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║      CHITRAL CYBER SQUAD — WHATSAPP BOT                  ║")
    print("  ║      Admin : ZIA AKBAR                                   ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(X)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"  {C}[*]{X} {line}")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# =============================================================================
#  WHATSAPP SEND
# =============================================================================
def wa_send(to, text):
    if not WA_TOKEN or not WA_PHONE_ID:
        log(f"{R}Cannot send — missing WA credentials{X}")
        return False
    url = f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4000]},
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        if r.status_code == 200:
            log(f"{G}Sent → {to}{X}")
            return True
        log(f"{R}Send failed {r.status_code}: {r.text[:150]}{X}")
        return False
    except Exception as e:
        log(f"{R}Send error: {e}{X}")
        return False

# =============================================================================
#  GEMINI VIA REST (no SDK)
# =============================================================================
def gemini_ask(prompt):
    if not GEMINI_KEY:
        return "❌ Gemini key missing in .env"
    url = ("https://generativelanguage.googleapis.com/v1beta/"
           f"models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}")
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            return f"❌ Gemini error {r.status_code}: {r.text[:200]}"
        d = r.json()
        return d["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Gemini exception: {e}"

# =============================================================================
#  SITE CHECKS
# =============================================================================
SEC_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Frame-Options", "X-Content-Type-Options",
    "Referrer-Policy", "Permissions-Policy",
]

def load_sites():
    if not os.path.exists(SITES_FILE):
        return []
    with open(SITES_FILE) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]

def check_site(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    out = {"url": url, "status": None, "ms": None,
           "ssl_days": None, "missing": [], "error": None}
    try:
        t0 = time.time()
        r = requests.get(url, timeout=12, allow_redirects=True,
                         headers={"User-Agent": "CCS-Bot/1.0"})
        out["status"] = r.status_code
        out["ms"] = round((time.time() - t0) * 1000, 0)
        out["missing"] = [h for h in SEC_HEADERS if h not in r.headers]
        try:
            host = urlparse(url).hostname
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(6)
                s.connect((host, 443))
                cert = s.getpeercert()
            exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            out["ssl_days"] = (exp - datetime.utcnow()).days
        except Exception:
            pass
    except Exception as e:
        out["error"] = str(e)[:80]
    return out

# =============================================================================
#  COMMANDS
# =============================================================================
def cmd_help():
    return (
        "🤖 *Chitral Cyber Squad Bot*\n\n"
        "*Site Monitoring*\n"
        "• /risk — scan all sites\n"
        "• /ssl <site>\n"
        "• /headers <site>\n"
        "• /ports <site>\n\n"
        "*Intelligence*\n"
        "• /ip <ip>\n"
        "• /dns <domain>\n"
        "• /subs <domain>\n"
        "• /breach <email>\n"
        "• /cve <product>\n\n"
        "*AI*\n"
        "• /ask <question>\n\n"
        "*System*\n"
        "• /ops\n"
        "• /list\n"
        "• /status"
    )

def cmd_ops():
    return (
        "🖥️ *CCS CONTROL PANEL*\n\n"
        f"📡 Sites configured: {len(load_sites())}\n"
        f"🤖 Gemini: {'✅' if GEMINI_KEY else '❌'}\n"
        f"💬 WhatsApp: {'✅' if WA_TOKEN else '❌'}\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "Type /help for commands."
    )

def cmd_risk():
    sites = load_sites()
    if not sites:
        return "⚠️ No sites in ~/CCS_Bot/sites.txt"
    lines = [f"🔍 *RISK SCAN — {len(sites)} sites*", ""]
    healthy = warning = critical = 0
    for s in sites:
        r = check_site(s)
        if r["error"]:
            lines.append(f"🔴 `{s}` — DOWN")
            critical += 1
            continue
        issues = []
        if r["status"] != 200:
            issues.append(f"HTTP {r['status']}")
        if r["ssl_days"] is not None and r["ssl_days"] < 30:
            issues.append(f"SSL {r['ssl_days']}d")
        if r["missing"]:
            issues.append(f"{len(r['missing'])} hdrs")
        if issues:
            lines.append(f"🟡 `{s}` — {', '.join(issues)}")
            warning += 1
        else:
            lines.append(f"🟢 `{s}` — OK ({int(r['ms'])}ms)")
            healthy += 1
    lines.append("")
    lines.append(f"✅ {healthy}  ⚠️ {warning}  🔴 {critical}")
    return "\n".join(lines)

def cmd_ssl(site):
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    try:
        host = urlparse(site).hostname
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(8)
            s.connect((host, 443))
            cert = s.getpeercert()
            proto = s.version()
        subj = dict(x[0] for x in cert["subject"])
        iss = dict(x[0] for x in cert["issuer"])
        exp = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days = (exp - datetime.utcnow()).days
        return (
            f"🔒 *SSL — {host}*\n\n"
            f"CN: `{subj.get('commonName','?')}`\n"
            f"Issuer: {iss.get('organizationName','?')}\n"
            f"Until: {cert['notAfter']}\n"
            f"Days: *{days}*\n"
            f"Proto: {proto}"
        )
    except Exception as e:
        return f"❌ {e}"

def cmd_headers(site):
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    try:
        r = requests.get(site, timeout=12, headers={"User-Agent": "CCS-Bot/1.0"})
        missing = [h for h in SEC_HEADERS if h not in r.headers]
        present = [h for h in SEC_HEADERS if h in r.headers]
        lines = [f"📋 *HEADERS — {site}*", ""]
        for h in present:
            lines.append(f"✅ {h}")
        for h in missing:
            lines.append(f"❌ {h}")
        lines.append("")
        lines.append(f"Server: `{r.headers.get('Server','hidden')}`")
        lines.append(f"Powered-By: `{r.headers.get('X-Powered-By','hidden')}`")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ {e}"

PORT_LIST = [21,22,80,443,3306,3389,5432,8080,8443]

def cmd_ports(site):
    host = urlparse(site if "://" in site else "https://"+site).hostname
    allowed = load_sites()
    if host not in allowed and host not in ("127.0.0.1","localhost"):
        return f"🚫 `{host}` not in allowlist"
    lines = [f"🔌 *PORTS — {host}*", ""]
    for p in PORT_LIST:
        try:
            s = socket.socket(); s.settimeout(1.2)
            rc = s.connect_ex((host, p)); s.close()
            if rc == 0:
                lines.append(f"🟢 {p} OPEN")
        except Exception:
            pass
    if len(lines) == 2:
        lines.append("No common ports open.")
    return "\n".join(lines)

def cmd_ip(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=8)
        d = r.json()
        if d.get("status") != "success":
            return f"❌ {d.get('message','failed')}"
        return (
            f"🌍 *IP — {ip}*\n\n"
            f"Country: {d.get('country','?')}\n"
            f"City: {d.get('city','?')}\n"
            f"ISP: {d.get('isp','?')}\n"
            f"ASN: {d.get('as','?')}"
        )
    except Exception as e:
        return f"❌ {e}"

def cmd_dns(domain):
    try:
        import dns.resolver
        lines = [f"🌐 *DNS — {domain}*", ""]
        for rtype in ["A","AAAA","MX","NS","TXT"]:
            try:
                ans = dns.resolver.resolve(domain, rtype, lifetime=5)
                vals = [str(a) for a in ans][:3]
                lines.append(f"*{rtype}*: " + ", ".join(vals))
            except Exception:
                pass
        return "\n".join(lines) if len(lines) > 2 else "❌ No records"
    except Exception as e:
        return f"❌ {e}"

def cmd_subs(domain):
    try:
        r = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20)
        data = r.json()
        names = set()
        for e in data:
            for n in e.get("name_value","").split("\n"):
                n = n.strip().lower()
                if n and "*" not in n and domain in n:
                    names.add(n)
        names = sorted(names)[:20]
        if not names:
            return "No subdomains found."
        return f"🔎 *SUBDOMAINS — {domain}* ({len(names)})\n\n" + "\n".join(f"• `{n}`" for n in names)
    except Exception as e:
        return f"❌ {e}"

def cmd_breach(email):
    try:
        r = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={"User-Agent": "CCS-Bot"}, timeout=10)
        if r.status_code == 404:
            return f"✅ `{email}` — clean."
        if r.status_code == 200:
            b = r.json()
            lines = [f"⚠️ *BREACHES — {email}*", ""]
            for x in b[:10]:
                lines.append(f"• {x.get('Name')} ({x.get('BreachDate')})")
            return "\n".join(lines)
        return f"⚠️ HIBP {r.status_code}"
    except Exception as e:
        return f"❌ {e}"

def cmd_cve(product):
    try:
        r = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={"keywordSearch": product, "resultsPerPage": 5},
            timeout=20)
        d = r.json()
        vulns = d.get("vulnerabilities", [])[:5]
        if not vulns:
            return f"No recent CVEs for `{product}`"
        lines = [f"🧨 *CVEs — {product}*", ""]
        for v in vulns:
            c = v["cve"]
            desc = c["descriptions"][0]["value"][:100]
            lines.append(f"• *{c['id']}*\n  {desc}...")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ {e}"

def cmd_ask(q):
    reply = gemini_ask(
        "You are CCS Cyber Mentor for Chitral Cyber Squad. "
        f"Answer concisely. Question: {q}"
    )
    return f"🤖 *CCS Mentor*\n\n{reply[:3500]}"

# =============================================================================
#  ROUTER
# =============================================================================
def route(msg):
    m = msg.strip()
    low = m.lower()
    if low in ("/help","help"): return cmd_help()
    if low == "/ops": return cmd_ops()
    if low == "/risk": return cmd_risk()
    if low == "/list":
        s = load_sites()
        return ("📋 *Your sites*\n\n" + "\n".join(f"• `{x}`" for x in s)) if s else "No sites yet."
    if low == "/status":
        return f"✅ Online\nAdmin: {ADMIN}\nTime: {datetime.now().strftime('%H:%M:%S')}"
    if low.startswith("/ssl "):     return cmd_ssl(m[5:].strip())
    if low.startswith("/headers "): return cmd_headers(m[9:].strip())
    if low.startswith("/ports "):   return cmd_ports(m[7:].strip())
    if low.startswith("/ip "):      return cmd_ip(m[4:].strip())
    if low.startswith("/dns "):     return cmd_dns(m[5:].strip())
    if low.startswith("/subs "):    return cmd_subs(m[6:].strip())
    if low.startswith("/breach "):  return cmd_breach(m[8:].strip())
    if low.startswith("/cve "):     return cmd_cve(m[5:].strip())
    if low.startswith("/ask "):     return cmd_ask(m[5:].strip())
    return "Unknown. Type /help"

# =============================================================================
#  WEBHOOK
# =============================================================================
@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY:
            log("Webhook verified")
            return challenge, 200
        return "Forbidden", 403

    data = request.get_json(silent=True) or {}
    try:
        for e in data.get("entry", []):
            for ch in e.get("changes", []):
                for msg in ch.get("value", {}).get("messages", []):
                    sender = msg.get("from")
                    if msg.get("type") == "text":
                        body = msg["text"]["body"]
                        log(f"{C}MSG {sender}: {body[:60]}{X}")
                        reply = route(body)
                        wa_send(sender, reply)
    except Exception as e:
        log(f"{R}Webhook error: {e}{X}")
    return jsonify({"status":"ok"}), 200

# =============================================================================
#  AUTOPILOT — 8 AM scan
# =============================================================================
def autopilot():
    while True:
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            log("Autopilot: daily scan")
            wa_send(MY_NUMBER, cmd_risk())
            time.sleep(60)
        time.sleep(30)

# =============================================================================
#  MAIN
# =============================================================================
def main():
    banner()
    print(f"  {Y}WA token    : {'✅' if WA_TOKEN else '❌'}{X}")
    print(f"  {Y}Phone ID    : {WA_PHONE_ID or '❌'}{X}")
    print(f"  {Y}Gemini key  : {'✅' if GEMINI_KEY else '❌'}{X}")
    print(f"  {Y}Sites       : {len(load_sites())}{X}")
    print(f"  {Y}Verify tok  : {VERIFY}{X}")
    print()

    if not WA_TOKEN or not WA_PHONE_ID:
        print(f"  {R}[!] Add credentials to ~/CCS_Bot/.env{X}")
        sys.exit(1)

    threading.Thread(target=autopilot, daemon=True).start()
    print(f"  {G}[+] Listening on http://0.0.0.0:8000/webhook{X}")
    print(f"  {G}[+] Run cloudflared: cloudflared tunnel --url http://localhost:8000{X}\n")
    app.run(host="0.0.0.0", port=8000, debug=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {R}Stopped.{X}\n")
