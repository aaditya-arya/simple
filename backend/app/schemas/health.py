from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class HealthTelemetryCreate(BaseModel):
    camera_id: int
    connectivity_status: str = Field(..., pattern="^(online|offline|intermittent|unknown)$")
    latency_ms: Optional[int] = Field(None, ge=0)
    packet_loss_percent: Optional[float] = Field(None, ge=0, le=100)
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthSnapshotResponse(BaseModel):
    snapshot_id: int
    camera_id: int
    observed_at: datetime
    connectivity_status: str
    latency_ms: Optional[int] = None
    packet_loss_percent: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class DepartmentHealthSummary(BaseModel):
    department_id: int
    department_name: str
    total_cameras: int
    online_count: int
    offline_count: int
    intermittent_count: int
    unknown_count: int
    uptime_percentage: float


class SystemHealthSummaryResponse(BaseModel):
    total_cameras: int
    online_count: int
    offline_count: int
    intermittent_count: int
    unknown_count: int
    overall_health_percentage: float
    by_department: List[DepartmentHealthSummary]
