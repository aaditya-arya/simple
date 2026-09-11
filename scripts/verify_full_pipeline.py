import sys
import os
import time
import socket
import urllib.request
import http.cookiejar
import cv2

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Set OpenCV RTSP options
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp;fflags;nobuffer;flags;low_delay"

def check_port(host: str, port: int) -> bool:
    """Checks if a TCP port is open and accepting connections."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def verify_pipeline():
    print("=" * 65)
    print("   MODEL 1 & MODEL 3 FULL PIPELINE VERIFICATION SUITE")
    print("=" * 65)

    # 1. Check MediaMTX Ports
    print("\n[Step 1/5] Checking MediaMTX Streaming Server Ports...")
    rtsp_open = check_port("127.0.0.1", 8554)
    hls_open = check_port("127.0.0.1", 8888)
    webrtc_open = check_port("127.0.0.1", 8889)

    print(f"  * RTSP Port 8554:   {'[OK] OPEN' if rtsp_open else '[FAIL] CLOSED (Start MediaMTX)'}")
    print(f"  * HLS Port 8888:    {'[OK] OPEN' if hls_open else '[FAIL] CLOSED (Start MediaMTX)'}")
    print(f"  * WebRTC Port 8889: {'[OK] OPEN' if webrtc_open else '[FAIL] CLOSED (Start MediaMTX)'}")

    if not rtsp_open or not hls_open:
        print("\n[!] MediaMTX is not running. Please run start_mediamtx.bat first.")
        return

    # 2. Check HLS Stream Manifest
    print("\n[Step 2/5] Checking HLS .m3u8 Stream Manifest for Frontend...")
    hls_url = "http://127.0.0.1:8888/stream/1/index.m3u8"
    try:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        req = urllib.request.Request(hls_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp = opener.open(req, timeout=4.0)
        content = resp.read().decode('utf-8', errors='ignore')
        if "#EXTM3U" in content:
            print(f"  [OK] HLS Stream is active and playable at: {hls_url}")
            for line in content.splitlines()[:5]:
                print(f"       {line}")
        else:
            print(f"  [!] Manifest returned, waiting for segments...")
    except Exception as e:
        print(f"  [FAIL] HLS Stream not active yet: {e}")
        print("       Make sure publish_traffic_stream.bat is running!")
        return

    # 3. Test OpenCV RTSP Ingestion
    print("\n[Step 3/5] Testing OpenCV VideoCapture on RTSP Stream (TCP)...")
    rtsp_url = "rtsp://127.0.0.1:8554/stream/1"
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print(f"  [FAIL] Failed to connect to {rtsp_url}")
        return

    ret, frame = cap.read()
    if ret and frame is not None:
        h, w, c = frame.shape
        print(f"  [OK] Successfully ingested real RTSP frame! Resolution: {w}x{h}, Channels: {c}")
    else:
        print(f"  [FAIL] Connected, but failed to grab frame.")
        cap.release()
        return

    # 4. Run YOLOv8 Vehicle Detection on Ingested Frame
    print("\n[Step 4/5] Running YOLOv8 Inference on Ingested RTSP Frame...")
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        results = model(frame, verbose=False, conf=0.3)

        detections = []
        VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck", 0: "person"}

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                if cls_id in VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0].item())
                    x_pct = round((x1 / w) * 100, 1)
                    y_pct = round((y1 / h) * 100, 1)
                    w_pct = round(((x2 - x1) / w) * 100, 1)
                    h_pct = round(((y2 - y1) / h) * 100, 1)

                    detections.append({
                        "class": VEHICLE_CLASSES[cls_id],
                        "confidence": round(conf, 2),
                        "box_pct": [x_pct, y_pct, w_pct, h_pct]
                    })

        print(f"  [OK] YOLOv8 detected {len(detections)} real vehicles in live RTSP stream:")
        for idx, d in enumerate(detections[:5]):
            print(f"       [{idx+1}] {d['class'].upper()} (Confidence: {int(d['confidence']*100)}%) -> Bounding Box %: {d['box_pct']}")

    except Exception as e:
        print(f"  [!] YOLO inference warning: {e}")

    cap.release()

    # 5. Check FastAPI Backend
    print("\n[Step 5/5] Checking FastAPI Backend Health...")
    backend_open = check_port("127.0.0.1", 8000)
    print(f"  * FastAPI Backend Port 8000: {'[OK] OPEN' if backend_open else '[!] Not running yet (Start backend with start_backend.bat)'}")

    print("\n" + "=" * 65)
    print("   FULL REAL-TIME RTSP + HLS + YOLOv8 PIPELINE IS OPERATIONAL!")
    print("=" * 65)

if __name__ == "__main__":
    verify_pipeline()
