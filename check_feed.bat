@echo off
title Live Camera Feed and Protocol Diagnostics
echo ========================================================
echo   Running Live Camera Feed and Protocol Diagnostics...
echo ========================================================
cd /d %~dp0
python scripts\check_live_feed.py
pause
