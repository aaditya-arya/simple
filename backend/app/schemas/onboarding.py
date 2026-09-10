from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class BulkUploadRow(BaseModel):
    external_reference: Optional[str] = None
    name: str
    department_id: Optional[int] = None
    department_code: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    camera_type: str = "fixed"
    ownership_type: str = "department_owned"
    access_class: str = "restricted"
    operational_status: str = "active"
    connectivity_status: str = "unknown"
    installed_at: Optional[str] = None
    notes: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class BulkUploadError(BaseModel):
    row_number: int
    camera_name: Optional[str] = None
    error_message: str


class BulkUploadResponse(BaseModel):
    total_processed: int
    successfully_onboarded: int
    failed_count: int
    errors: List[BulkUploadError] = []
