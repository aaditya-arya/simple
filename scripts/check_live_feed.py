import os, sys, time, socket
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

def check_port(host, port, timeout=2.0):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except:
        return False

def diagnose():
    print('=' * 65)
    print('       GUJARAT CCTV LIVE FEED DIAGNOSTIC & VERIFICATION')
    print('=' * 65)

    camera_url = os.getenv('CAMERA_RTSP_URL', '')
    sentinel_host = os.getenv('SENTINEL_HOST', '127.0.0.1')

    print('\n[Step 1/3] Checking .env Configuration...')
    print('  * SENTINEL_HOST:    ' + sentinel_host)
    print('  * CAMERA_RTSP_URL:  ' + (camera_url if camera_url else '(Not set)'))

    if camera_url and camera_url.startswith(('rtsp://', 'rtsps://', 'http://', 'https://')):
        print('\n[Step 2/3] Probing Live Camera Feed...')
        clean = camera_url.split('@')[-1] if '@' in camera_url else camera_url
        clean = clean.replace('rtsp://', '').replace('rtsps://', '').replace('http://', '').replace('https://', '')
        hp = clean.split('/')[0]
        host = hp.split(':')[0]
        default_port = 80 if camera_url.startswith('http://') else 554
        port = int(hp.split(':')[1]) if ':' in hp else default_port

        print(f'  * Probing network route to {host}:{port}...')
        if check_port(host, port, timeout=3.0):
            print(f'  [OK] Port {port} is OPEN on {host}!')
            try:
                import cv2
                if camera_url.startswith('rtsp'):
                    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp'
                cap = cv2.VideoCapture(camera_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                t0 = time.time()
                grabbed, frame = cap.read()
                cap.release()
                if grabbed and frame is not None:
                    h, w, _ = frame.shape
                    print(f'  [SUCCESS] Live camera frame acquired! Resolution: {w}x{h} ({round((time.time()-t0)*1000)}ms)')
                else:
                    print('  [FAIL] Port open, but stream path or authentication invalid.')
            except Exception as e:
                print(f'  [ERROR] Frame decode error: {e}')
        else:
            print(f'  [FAIL] Connection to {host}:{port} timed out or refused.')
            print('         Possible reasons:')
            print(f'         1. Camera at {host} is offline / on a different Wi-Fi subnet.')
            print(f'         2. Port {port} is wrong (for Android IP Webcam use port 8080: http://{host}:8080/video).')
    else:
        print('\n[Step 2/3] Checking Default Video Source...')
        v = ROOT_DIR / 'videos' / 'traffic_sample.mp4'
        print('  * Sample video: ' + ('Found' if v.exists() else 'Synthetic fallback will be used'))

    print('\n[Step 3/3] Checking Local Gateway & Streaming Servers...')
    p_rtsp = check_port('127.0.0.1', 8554)
    p_hls = check_port('127.0.0.1', 8888)
    p_webrtc = check_port('127.0.0.1', 8889)
    p_back = check_port('127.0.0.1', 8005)
    p_front = check_port('127.0.0.1', 5180)

    print('  * MediaMTX RTSP (:8554):     ' + ('[OK] RUNNING' if p_rtsp else '[STOPPED]'))
    print('  * MediaMTX HLS  (:8888):     ' + ('[OK] RUNNING' if p_hls else '[STOPPED]'))
    print('  * MediaMTX WebRTC (:8889):  ' + ('[OK] RUNNING' if p_webrtc else '[STOPPED]'))
    print('  * FastAPI Backend (:8005):   ' + ('[OK] RUNNING' if p_back else '[STOPPED]'))
    print('  * React Frontend  (:5180):   ' + ('[OK] RUNNING' if p_front else '[STOPPED]'))

    print('\n' + '=' * 65)
    if not (p_rtsp and p_back and p_front):
        print(' [ACTION NEEDED] Start all services in one click with: .\\run_all.bat')
    else:
        print(' [STATUS] All services running! Open http://localhost:5180 in browser.')
    print('=' * 65)

if __name__ == '__main__':
    diagnose()
