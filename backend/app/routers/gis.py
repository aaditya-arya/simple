from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.auth import User
from app.schemas.camera import GeoJSONFeatureCollection
from app.core.rbac import get_current_user_optional
from app.services.camera_service import get_cameras_geojson

router = APIRouter(prefix="/gis", tags=["GIS & Leaflet Map Services"])

@router.get("/geojson", response_model=GeoJSONFeatureCollection)
def get_cameras_as_geojson(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    camera_type: Optional[str] = Query(None, description="fixed, ptz, thermal, etc."),
    operational_status: Optional[str] = Query(None, description="active, maintenance, retired, planned"),
    connectivity_status: Optional[str] = Query(None, description="online, offline, intermittent"),
    vms_vendor_id: Optional[str] = Query(None, description="hikvision, dahua, sentinel, etc."),
    city: Optional[str] = Query(None, description="Filter by Gujarat city"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Main endpoint for Leaflet React.js frontend:
    Returns cameras as an RFC 7946 GeoJSON FeatureCollection formatted with Model 3 VMS attributes,
    coverage radii, Sentinel sandbox live feeds, and city clusters.
    """
    scoped_dept_id = department_id
    if current_user and current_user.role and current_user.role.name not in ["super_admin", "auditor"]:
        scoped_dept_id = current_user.department_id

    return get_cameras_geojson(
        db=db,
        department_id=scoped_dept_id,
        camera_type=camera_type,
        operational_status=operational_status,
        connectivity_status=connectivity_status,
        vms_vendor_id=vms_vendor_id,
        city=city
    )


@router.get("/bbox", response_model=GeoJSONFeatureCollection)
def get_cameras_by_bounding_box(
    min_lon: float = Query(..., description="West Longitude"),
    min_lat: float = Query(..., description="South Latitude"),
    max_lon: float = Query(..., description="East Longitude"),
    max_lat: float = Query(..., description="North Latitude"),
    department_id: Optional[int] = Query(None),
    camera_type: Optional[str] = Query(None),
    operational_status: Optional[str] = Query(None),
    connectivity_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Viewport-based Spatial Query:
    Returns cameras inside the Leaflet map's current bounding box.
    """
    scoped_dept_id = department_id
    if current_user and current_user.role and current_user.role.name not in ["super_admin", "auditor"]:
        scoped_dept_id = current_user.department_id

    return get_cameras_geojson(
        db=db,
        department_id=scoped_dept_id,
        camera_type=camera_type,
        operational_status=operational_status,
        connectivity_status=connectivity_status,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat
    )


@router.get("/nearby", response_model=GeoJSONFeatureCollection)
def get_cameras_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: float = Query(500.0, gt=0, le=50000),
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Radius Query:
    Find all cameras within X meters of a given GPS coordinate using PostGIS ST_DWithin.
    """
    scoped_dept_id = department_id
    if current_user and current_user.role and current_user.role.name not in ["super_admin", "auditor"]:
        scoped_dept_id = current_user.department_id

    return get_cameras_geojson(
        db=db,
        department_id=scoped_dept_id,
        center_lat=latitude,
        center_lon=longitude,
        radius_meters=radius_meters
    )
