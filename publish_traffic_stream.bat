@echo off
title FFmpeg RTSP Traffic Stream Publisher
echo ========================================================
echo   Publishing Traffic Video to MediaMTX RTSP Server
echo   Source:  videos/traffic_sample.mp4
echo   Target:  rtsp://127.0.0.1:8554/stream/1
echo ========================================================

cd /d "%~dp0"
if not exist "videos\traffic_sample.mp4" (
    echo [ERROR] Sample video videos\traffic_sample.mp4 not found!
    pause
    exit /b 1
)

echo Streaming in continuous loop over TCP...
ffmpeg -re -stream_loop -1 -i "videos/traffic_sample.mp4" -c:v libx264 -preset ultrafast -tune zerolatency -b:v 2000k -pix_fmt yuv420p -an -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/stream/1
pause
