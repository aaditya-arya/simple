@echo off
title MediaMTX RTSP Server
echo ========================================================
echo   Starting MediaMTX RTSP and HLS Streaming Server
echo   RTSP:  rtsp://localhost:8554/stream/1
echo   HLS:   http://localhost:8888/stream/1/index.m3u8
echo   WHEP:  http://localhost:8889/stream/1/whep
echo ========================================================
cd /d "%~dp0mediamtx"
mediamtx.exe
pause
