@echo off
title Gujarat CCTV Platform Launcher
echo ========================================================
echo   Launching All Services (MediaMTX + RTSP + FastAPI + React)
echo ========================================================
cd /d %~dp0
python run_all.py
pause
