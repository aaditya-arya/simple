import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import SessionLocal
from app.models.camera import Camera
from app.services.rtsp_inference_service import rtsp_engine
from app.config import settings

router = APIRouter(tags=["Real-time RTSP AI Inference WebSockets"])

@router.websocket("/ws/inference/{camera_id}")
async def websocket_rtsp_inference_stream(websocket: WebSocket, camera_id: int):
    """
    WebSocket endpoint for real-time YOLOv8 AI inference streaming.
    Pipes dynamic bounding box coordinates (x, y, w, h in percentages),
    confidence scores, vehicle plate numbers, and PTS timestamps at 30 FPS.
    """
    await websocket.accept()
    
    # Priority 1: User-defined custom RTSP URL in .env
    if settings.CAMERA_RTSP_URL:
        rtsp_url = settings.CAMERA_RTSP_URL
    else:
        # Priority 2: Channel mapping (local vs remote Sentinel)
        is_local = settings.SENTINEL_HOST in {"localhost", "127.0.0.1"}
        effective_channel = 1 if is_local else (camera_id if 1 <= camera_id <= 30 else 1)
        rtsp_url = f"rtsp://{settings.SENTINEL_HOST}:8554/stream/{effective_channel}"

        db = SessionLocal()
        try:
            camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
            if camera and camera.attributes and not is_local:
                rtsp_url = camera.attributes.get("sentinel_rtsp_url", rtsp_url)
                rtsp_url = rtsp_url.replace("sentinel-grid.internal", settings.SENTINEL_HOST)
        except Exception:
            pass
        finally:
            db.close()

    try:
        async for frame_data in rtsp_engine.stream_inference(camera_id, rtsp_url):
            await websocket.send_json(frame_data)
    except WebSocketDisconnect:
        # Client closed modal
        pass
    except Exception as e:
        print(f"WebSocket streaming notice for camera {camera_id}: {e}")
