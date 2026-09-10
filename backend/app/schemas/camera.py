from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date, datetime

class CameraBase(BaseModel):
    external_reference: Optional[str] = None
    name: str
    department_id: int
    address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    camera_type: str = "fixed"
    ownership_type: str = "department_owned"
    access_class: str = "restricted"
    connectivity_status: str = "unknown"
    operational_status: str = "active"
    installed_at: Optional[date] = None
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    # Model 3 VMS Federation Primitives
    vms_vendor_id: str = "hikvision"
    vms_stream_protocol: str = "rtsp"
    external_camera_id: Optional[str] = None
    adapter_channel: Optional[str] = None
    coverage_radius_meters: float = 75.0
    coverage_angle_degrees: float = 120.0


class CameraCreate(CameraBase):
    latitude: float = Field(..., ge=-90, le=90, description="WGS84 Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="WGS84 Longitude")


class CameraUpdate(BaseModel):
    external_reference: Optional[str] = None
    name: Optional[str] = None
    department_id: Optional[int] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    camera_type: Optional[str] = None
    ownership_type: Optional[str] = None
    access_class: Optional[str] = None
    connectivity_status: Optional[str] = None
    operational_status: Optional[str] = None
    installed_at: Optional[date] = None
    notes: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    
    vms_vendor_id: Optional[str] = None
    vms_stream_protocol: Optional[str] = None
    external_camera_id: Optional[str] = None
    adapter_channel: Optional[str] = None
    coverage_radius_meters: Optional[float] = None
    coverage_angle_degrees: Optional[float] = None


class CameraResponse(CameraBase):
    camera_id: int
    latitude: float
    longitude: float
    department_name: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Leaflet-compatible GeoJSON Schemas (RFC 7946)
class GeoJSONGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJSONProperties(BaseModel):
    camera_id: int
    name: str
    external_reference: Optional[str] = None
    department_id: int
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    camera_type: str
    operational_status: str
    connectivity_status: str
    ownership_type: str
    access_class: str
    installed_at: Optional[str] = None
    address: Optional[str] = None
    city: str = "Ahmedabad"
    
    # Model 3 VMS Federation Metadata
    vms_vendor_id: str
    vms_stream_protocol: str
    external_camera_id: Optional[str] = None
    adapter_channel: Optional[str] = None
    coverage_radius_meters: float
    coverage_angle_degrees: float
    
    # Real Sentinel Sandbox Grid Live Stream Metadata
    is_sentinel_live: bool = False
    sentinel_id: Optional[int] = None
    sentinel_rtsp_url: Optional[str] = None
    sentinel_webrtc_url: Optional[str] = None
    sentinel_hls_url: Optional[str] = None
    stream_codec: Optional[str] = "H.264"
    
    age_years: Optional[float] = None
    is_ageing_alert: bool = False
    attributes: Dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: GeoJSONProperties


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]
    total_count: int
    sentinel_live_count: int = 0


# Model 3 Middleware Telemetry Event Schemas
class MiddlewareEventCreate(BaseModel):
    camera_id: Optional[int] = None
    external_camera_id: Optional[str] = None
    vms_vendor_id: str
    event_type: str
    severity: str = "medium"
    new_status: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class MiddlewareEventResponse(BaseModel):
    event_id: int
    camera_id: Optional[int] = None
    vms_vendor_id: str
    event_type: str
    severity: str
    received_at: datetime
    status_updated: bool = False

    class Config:
        from_attributes = True
