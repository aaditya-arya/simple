@echo off
title CCTV Registry React GIS Frontend
echo ========================================================
echo   Starting Gujarat CCTV GIS React Frontend
echo   Dashboard UI: http://localhost:5180
echo ========================================================

cd /d "%~dp0frontend"
npm run dev -- --port 5180
pause

