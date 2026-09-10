from app.schemas.auth import (
    DepartmentBase, DepartmentCreate, DepartmentResponse,
    RoleResponse, UserLogin, UserCreate, UserResponse,
    Token, TokenPayload
)
from app.schemas.camera import (
    CameraBase, CameraCreate, CameraUpdate, CameraResponse,
    GeoJSONGeometry, GeoJSONProperties, GeoJSONFeature, GeoJSONFeatureCollection,
    MiddlewareEventCreate, MiddlewareEventResponse
)
from app.schemas.onboarding import (
    BulkUploadRow, BulkUploadError, BulkUploadResponse
)
from app.schemas.health import (
    HealthTelemetryCreate, HealthSnapshotResponse,
    DepartmentHealthSummary, SystemHealthSummaryResponse
)
from app.schemas.analytics import (
    AgeingAssetItem, AgeingReportResponse,
    DepartmentOverlapZone, GapAnalysisZone, GapAnalysisResponse
)

__all__ = [
    "DepartmentBase", "DepartmentCreate", "DepartmentResponse",
    "RoleResponse", "UserLogin", "UserCreate", "UserResponse",
    "Token", "TokenPayload",
    "CameraBase", "CameraCreate", "CameraUpdate", "CameraResponse",
    "GeoJSONGeometry", "GeoJSONProperties", "GeoJSONFeature", "GeoJSONFeatureCollection",
    "MiddlewareEventCreate", "MiddlewareEventResponse",
    "BulkUploadRow", "BulkUploadError", "BulkUploadResponse",
    "HealthTelemetryCreate", "HealthSnapshotResponse",
    "DepartmentHealthSummary", "SystemHealthSummaryResponse",
    "AgeingAssetItem", "AgeingReportResponse",
    "DepartmentOverlapZone", "GapAnalysisZone", "GapAnalysisResponse"
]
