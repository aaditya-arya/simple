@echo off
title CCTV Registry FastAPI Backend
echo ========================================================
echo   Starting Gujarat CCTV Central Registry Backend
echo   FastAPI REST API: http://localhost:8000/docs
echo   WebSocket Stream: ws://localhost:8000/api/v1/ws/inference/1
echo ========================================================

cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
