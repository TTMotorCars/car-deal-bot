#!/usr/bin/env bash
#
# One-shot setup for the car deal bot.
# Run:  bash setup.sh
#
# What it does:
#   1. Creates a Python virtual environment.
#   2. Installs dependencies.
#   3. Copies .env.example -> .env if you don't have one.
#   4. Walks you through setting Twilio credentials interactively.
#   5. Runs the bot once in DRY-RUN mode so you can verify it works.

set -e

cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "   Car Deal Bot - Setup"
echo "=============================================="
echo ""

# --- Python check ------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    echo "  macOS:  brew install python"
    echo "  Ubuntu: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi
echo "[OK] Python 3 found: $(python3 --version)"

# --- venv --------------------------------------------------------------------
if [ ! -d ".venv" ]; then
    echo "[..] Creating virtual environment..."
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "[OK] Virtual environment ready."

# --- deps --------------------------------------------------------------------
echo "[..] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "[OK] Dependencies installed."

# --- .env --------------------------------------------------------------------
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[OK] Created .env from template."
else
    echo "[OK] .env already exists, leaving it alone."
fi

# --- interactive Twilio setup -----------------------------------------------
echo ""
echo "----------------------------------------------"
echo "  Twilio setup (for text messages)"
echo "----------------------------------------------"
echo ""
echo "Don't have a Twilio account yet? Sign up here first (free trial,"
echo "\$15 credit), then come back:"
echo ""
echo "    https://www.twilio.com/try-twilio"
echo ""
read -r -p "Press Enter once you have your Twilio dashboard open, or type 'skip' and Enter to skip Twilio setup for now: " resume
if [ "$resume" != "skip" ]; then
    echo ""
    read -r -p "Account SID (starts with AC):      " TW_SID
    read -r -p "Auth Token:                        " TW_TOK
    read -r -p "Your Twilio number (+13125551212): " TW_FROM
    read -r -p "Your real phone (+17735551212):    " TW_TO

    # Write values into .env (replacing placeholders).
    python3 - <<PY
import re, pathlib
p = pathlib.Path(".env")
text = p.read_text()
pairs = {
    "TWILIO_ACCOUNT_SID": "$TW_SID",
    "TWILIO_AUTH_TOKEN":  "$TW_TOK",
    "TWILIO_FROM_NUMBER": "$TW_FROM",
    "ALERT_TO_NUMBER":    "$TW_TO",
}
for k, v in pairs.items():
    if not v.strip():
        continue
    text = re.sub(rf"^{k}=.*$", f"{k}={v}", text, flags=re.M)
p.write_text(text)
print("[OK] Twilio creds written to .env")
PY
fi

# --- dry-run test ------------------------------------------------------------
echo ""
echo "----------------------------------------------"
echo "  Running one test scan (DRY RUN, no texts)"
echo "----------------------------------------------"
echo ""
DRY_RUN=1 python3 main.py --verbose || true

echo ""
echo "=============================================="
echo "   Setup complete."
echo "=============================================="
echo ""
echo "Run it for real whenever you want:"
echo "    source .venv/bin/activate && python main.py"
echo ""
echo "To automate (text you 24/7), see DEPLOY.md"
echo ""
