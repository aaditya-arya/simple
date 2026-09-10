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
    Streams dynamic bounding box coordinates (x, y, w, h in percentages),
    confidence scores, vehicle plate numbers, and PTS timestamps at 30 FPS.
    """
    await websocket.accept()
    
    # Resolve RTSP endpoint for this camera
    db = SessionLocal()
    rtsp_url = f"rtsp://{settings.SENTINEL_HOST}:8554/stream/{camera_id}"
    try:
        camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
        if camera and camera.attributes:
            rtsp_url = camera.attributes.get("sentinel_rtsp_url", rtsp_url)
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
        print(f"WebSocket streaming interrupted for camera {camera_id}: {e}")
