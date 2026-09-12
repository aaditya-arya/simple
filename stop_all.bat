@echo off
title Gujarat CCTV Platform Stop Services
echo ========================================================
echo   Stopping All CCTV Platform Services...
echo ========================================================

echo Terminating MediaMTX...
taskkill /F /IM mediamtx.exe 2>nul

echo Terminating FFmpeg Streams...
taskkill /F /IM ffmpeg.exe 2>nul

echo Releasing Port 8000 (Backend)...
for /f tokens=5 %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

echo Releasing Port 5173 (Frontend)...
for /f tokens=5 %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)

echo ========================================================
echo   All Services Successfully Stopped!
echo ========================================================
pause
