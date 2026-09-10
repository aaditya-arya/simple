from app.routers.auth import router as auth_router
from app.routers.cameras import router as cameras_router
from app.routers.onboarding import router as onboarding_router
from app.routers.gis import router as gis_router
from app.routers.health import router as health_router
from app.routers.analytics import router as analytics_router
from app.routers.websocket_stream import router as ws_router

__all__ = [
    "auth_router",
    "cameras_router",
    "onboarding_router",
    "gis_router",
    "health_router",
    "analytics_router",
    "ws_router",
]
