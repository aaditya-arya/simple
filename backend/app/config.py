import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CCTV Central Registry API"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL + PostGIS Connection URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/cctv_registry_db"
    )
    
    # JWT Authentication Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-cctv-jwt-token-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Sentinel Sandbox Live Stream Gateway Settings
    SENTINEL_HOST: str = os.getenv("SENTINEL_HOST", "127.0.0.1")
    SENTINEL_AUTH_TOKEN: str = os.getenv("SENTINEL_AUTH_TOKEN", "")
    SENTINEL_RTSP_USER: str = os.getenv("SENTINEL_RTSP_USER", "")
    SENTINEL_RTSP_PASS: str = os.getenv("SENTINEL_RTSP_PASS", "")
    CAMERA_RTSP_URL: str = os.getenv("CAMERA_RTSP_URL", "")
    
    # CORS Origins for React.js frontend
    CORS_ORIGINS: list[str] = [
        "http://localhost:5180",
        "http://127.0.0.1:5180",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*",
    ]

    class Config:
        case_sensitive = True

settings = Settings()
