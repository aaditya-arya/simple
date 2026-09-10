from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AgeingAssetItem(BaseModel):
    camera_id: int
    name: str
    department_name: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    installed_at: Optional[str] = None
    age_years: float
    age_category: str  # "< 3 years", "3-5 years", "5-7 years", "> 7 years (Critical EOL)"
    operational_status: str
    connectivity_status: str
    vms_vendor_id: str
    recommended_action: str


class AgeingReportResponse(BaseModel):
    total_cameras_analyzed: int
    critical_ageing_count: int  # > 7 years
    moderate_ageing_count: int  # 5-7 years
    healthy_age_count: int      # < 5 years
    unknown_install_date_count: int
    amc_expired_risk_count: int
    cameras: List[AgeingAssetItem]


class DepartmentOverlapZone(BaseModel):
    zone_name: str
    departments_involved: List[str]
    overlapping_camera_count: int
    status: str  # "Redundant Overlap", "Single Dept Coverage", "Zero Coverage Blindspot"
    recommendation: str


class GapAnalysisZone(BaseModel):
    zone_id: str
    zone_name: str
    coordinates_polygon: List[List[float]] = []  # [[lon, lat], ...] polygon boundary
    estimated_area_sq_km: float
    active_cameras_count: int
    coverage_area_sq_km: float
    coverage_percentage: float
    gap_severity: str  # "Critical Gap", "Moderate Gap", "Adequate Coverage"
    departments_present: List[str]
    recommended_new_cameras: int


class GapAnalysisResponse(BaseModel):
    total_active_cameras: int
    total_surveillance_area_sq_km: float
    total_covered_area_sq_km: float
    overall_city_coverage_percentage: float
    identified_gap_zones: List[GapAnalysisZone]
    department_overlaps: List[DepartmentOverlapZone]
    ageing_risk_summary: Dict[str, int]
