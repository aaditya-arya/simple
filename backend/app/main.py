import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    auth_router,
    cameras_router,
    onboarding_router,
    gis_router,
    health_router,
    analytics_router,
    ws_router,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Centralized CCTV Asset Registry & GIS Management Backend.\n\n"
        "Features:\n"
        "- Department-wise Role-Based Access Control (RBAC)\n"
        "- Bulk (CSV/Excel), Manual, and API Onboarding\n"
        "- Leaflet-ready PostGIS GeoJSON Spatial Endpoints\n"
        "- Real-time Telemetry & Health Monitoring\n"
        "- Gap Analysis & Ageing Infrastructure Reports\n"
        "- RTSP & YOLOv8 Computer Vision Inference WebSockets"
    )
)

# Enable CORS for React.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount videos folder if present for offline/demo playback
videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos")
if not os.path.exists(videos_dir):
    # Check project root
    videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "videos")

if os.path.exists(videos_dir):
    app.mount("/videos", StaticFiles(directory=videos_dir), name="videos")

# Register API & WebSocket Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(cameras_router, prefix=settings.API_V1_STR)
app.include_router(onboarding_router, prefix=settings.API_V1_STR)
app.include_router(gis_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/healthz", tags=["System"])
def health_check():
    return {"status": "healthy"}
