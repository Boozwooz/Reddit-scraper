@echo off
title Reddit Dataset Grabber - 100% Vibe Coded
color 0B

echo =========================================================================
echo          REDDIT DATASET GRABBER (100%% VIBE CODED EDITION)
echo                   Automated Multi-Threaded Scraper
echo =========================================================================
echo.
echo [*] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet

echo [*] Verifying Playwright Chromium browser binaries...
python -m playwright install chromium

echo.
echo [+] Launching Reddit Grabber...
echo =========================================================================
echo.

python reddit_grabber.py %*

echo.
pause
