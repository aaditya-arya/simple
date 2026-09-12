#!/usr/bin/env python3
"
=============================================================================
 Gujarat CCTV Registry & AI Video Analytics - Unified System Orchestrator
=============================================================================
Single-command launcher that initializes and monitors all 4 system tiers:
 1. MediaMTX Streaming Server (RTSP :8554, HLS :8888)
 2. FFmpeg RTSP Traffic Stream Loop Publisher
 3. FastAPI AI Backend & YOLOv8 Inference WebSocket (:8005)
 4. React GIS Leaflet Frontend Dashboard (:5180)

Usage:
  python run_all.py
  (or double-click run_all.bat)
=============================================================================
"

import os
import sys
import time
import socket
import signal
import webbrowser
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
MEDIAMTX_DIR = ROOT_DIR / mediamtx
MEDIAMTX_EXE = MEDIAMTX_DIR / mediamtx.exe
MEDIAMTX_CONFIG = MEDIAMTX_DIR / mediamtx.yml
VIDEO_PATH = ROOT_DIR / videos / traffic_sample.mp4
BACKEND_DIR = ROOT_DIR / backend
FRONTEND_DIR = ROOT_DIR / frontend

BACKEND_PORT = 8005
FRONTEND_PORT = 5180

processes = []

def check_port(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def wait_for_port(host: str, port: int, timeout_sec: int = 15) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        if check_port(host, port):
            return True
        time.sleep(0.5)
    return False

def cleanup(signum=None, frame=None):
    print(\n + = * 65)
    print( [!] Shutting down all system services cleanly...)
    print(= * 65)
    for p in reversed(processes):
        if p.poll() is None:
            try:
                if os.name == 'nt':
                    subprocess.run(ftaskkill /F /T /PID {p.pid}, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    p.terminate()
            except Exception:
                pass
    print( [OK] All services terminated. Goodbye!)
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(= * 70)
    print( GUJARAT CCTV CENTRAL REGISTRY & VIDEO ANALYTICS (MODEL 1 + MODEL 3))
    print( UNIFIED SYSTEM LAUNCHER)
    print(= * 70)

    if not MEDIAMTX_EXE.exists():
        print(f [ERROR] MediaMTX executable not found at: {MEDIAMTX_EXE})
        return
    if not VIDEO_PATH.exists():
        print(f [ERROR] Traffic sample video not found at: {VIDEO_PATH})
        return

    # 1. Start MediaMTX
    print(\n[1/4] Launching MediaMTX RTSP/HLS Streaming Server...)
    mediamtx_proc = subprocess.Popen(
        [str(MEDIAMTX_EXE), str(MEDIAMTX_CONFIG)],
        cwd=str(MEDIAMTX_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(mediamtx_proc)
    
    if wait_for_port(127.0.0.1, 8554, timeout_sec=8):
        print( -> MediaMTX RTSP: rtsp://127.0.0.1:8554/stream/1 [ONLINE])
        print( -> MediaMTX HLS: http://127.0.0.1:8888/stream/1/index.m3u8 [ONLINE])
    else:
        print( -> MediaMTX started.)

    # 2. Start FFmpeg RTSP Loop Publisher
    print(\n[2/4] Publishing Continuous RTSP Traffic Stream via FFmpeg...)
    ffmpeg_cmd = [
        ffmpeg,
        -re,
        -stream_loop, -1,
        -i, str(VIDEO_PATH),
        -c:v, libx264,
        -preset, ultrafast,
        -tune, zerolatency,
        -b:v, 2000k,
        -pix_fmt, yuv420p,
        -an,
        -f, rtsp,
        -rtsp_transport, tcp,
        rtsp://127.0.0.1:8554/stream/1
    ]
    ffmpeg_proc = subprocess.Popen(
        ffmpeg_cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(ffmpeg_proc)
    print( -> FFmpeg Loop Stream: Active (Broadcasting to rtsp://127.0.0.1:8554/stream/1))

    # 3. Start FastAPI Backend on Port 8005
    print(f\n[3/4] Launching FastAPI Backend & YOLOv8 Inference Engine (: {BACKEND_PORT})...)
    backend_cmd = [sys.executable, -m, uvicorn, app.main:app, --host, 0.0.0.0, --port, str(BACKEND_PORT)]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(backend_proc)

    if wait_for_port(127.0.0.1, BACKEND_PORT, timeout_sec=15):
        print(f -> FastAPI REST API: http://127.0.0.1:{BACKEND_PORT}/docs [ONLINE])
        print(f -> WebSocket Engine: ws://127.0.0.1:{BACKEND_PORT}/api/v1/ws/inference/1 [READY])
    else:
        print(f -> FastAPI Backend starting up on port {BACKEND_PORT}...)

    # 4. Start React Frontend on Port 5180
    print(f\n[4/4] Launching React GIS Leaflet Dashboard (: {FRONTEND_PORT})...)
    npm_cmd = npm.cmd if os.name == nt else npm
    frontend_proc = subprocess.Popen(
        [npm_cmd, run, dev, --, --port, str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(frontend_proc)

    if wait_for_port(127.0.0.1, FRONTEND_PORT, timeout_sec=15):
        print(f -> React Web Dashboard: http://localhost:{FRONTEND_PORT} [ONLINE])
    else:
        print(f -> Vite Frontend starting up on http://localhost:{FRONTEND_PORT}...)

    # Summary Display
    print(\n + = * 70)
    print( ALL SERVICES ARE RUNNING! SYSTEM READY FOR DEMONSTRATION)
    print(= * 70)
    print(f * Web Dashboard: http://localhost:{FRONTEND_PORT})
    print(f * API Documentation: http://localhost:{BACKEND_PORT}/docs)
    print( * RTSP Stream URL: rtsp://127.0.0.1:8554/stream/1)
    print( * HLS Browser Stream: http://127.0.0.1:8888/stream/1/index.m3u8)
    print(f * WebSocket Inference: ws://127.0.0.1:{BACKEND_PORT}/api/v1/ws/inference/{{camera_id}})
    print(= * 70)
    print( 👉 Press [Ctrl+C] in this window to stop all services cleanly.)
    print(= * 70 + \n)

    time.sleep(1.5)
    try:
        webbrowser.open(fhttp://localhost:{FRONTEND_PORT})
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == __main__:
    main()
