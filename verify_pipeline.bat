@echo off
title Streaming Pipeline Verification Suite
echo ========================================================
echo   Running End-to-End Pipeline Verification Suite
echo ========================================================

cd /d "%~dp0"
python scripts\verify_full_pipeline.py
pause
