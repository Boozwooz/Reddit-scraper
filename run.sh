#!/usr/bin/env bash
set -e

echo "========================================================================="
echo "         REDDIT DATASET GRABBER (100% VIBE CODED EDITION)"
echo "========================================================================="
echo ""
echo "[*] Checking Python dependencies..."
python3 -m pip install -r requirements.txt --quiet

echo "[*] Installing/verifying Playwright Chromium browser..."
python3 -m playwright install chromium

echo ""
echo "[+] Starting Reddit Grabber..."
echo "========================================================================="
echo ""

python3 reddit_grabber.py "$@"
