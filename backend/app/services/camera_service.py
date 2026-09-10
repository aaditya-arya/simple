from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from geoalchemy2.functions import ST_X, ST_Y, ST_DWithin, ST_MakeEnvelope, ST_Intersects, ST_SetSRID, ST_Point
from geoalchemy2 import Geometry

from app.models.camera import Camera, CameraStorageLocation, CameraSource
from app.models.auth import Department, User
from app.schemas.camera import (
    CameraCreate, CameraUpdate, CameraResponse,
    GeoJSONFeature, GeoJSONProperties, GeoJSONGeometry, GeoJSONFeatureCollection
)
from app.services.audit_service import log_audit_event

def GeographyPoint():
    """Helper for casting geography to geometry in PostGIS queries."""
    return Geometry(geometry_type='POINT', srid=4326)

def create_camera(
    db: Session,
    camera_in: CameraCreate,
    current_user: Optional[User] = None
) -> Camera:
    """
    Creates a new Camera with PostGIS geography point and Model 3 VMS primitives.
    """
    wkt_point = f"POINT({camera_in.longitude} {camera_in.latitude})"
    
    db_camera = Camera(
        external_reference=camera_in.external_reference,
        name=camera_in.name,
        department_id=camera_in.department_id,
        location=wkt_point,
        address=camera_in.address,
        manufacturer=camera_in.manufacturer,
        model=camera_in.model,
        serial_number=camera_in.serial_number,
        camera_type=camera_in.camera_type,
        ownership_type=camera_in.ownership_type,
        access_class=camera_in.access_class,
        connectivity_status=camera_in.connectivity_status,
        operational_status=camera_in.operational_status,
        installed_at=camera_in.installed_at,
        notes=camera_in.notes,
        attributes=camera_in.attributes,
        
        # Model 3 VMS Primitives
        vms_vendor_id=camera_in.vms_vendor_id,
        vms_stream_protocol=camera_in.vms_stream_protocol,
        external_camera_id=camera_in.external_camera_id or camera_in.external_reference,
        adapter_channel=camera_in.adapter_channel,
        coverage_radius_meters=camera_in.coverage_radius_meters,
        coverage_angle_degrees=camera_in.coverage_angle_degrees
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)

    log_audit_event(
        db=db,
        action="CREATE_CAMERA",
        entity_type="cameras",
        entity_id=db_camera.camera_id,
        actor_reference=current_user.username if current_user else "system",
        details={"name": db_camera.name, "vms_vendor": db_camera.vms_vendor_id}
    )
    return db_camera


def update_camera(
    db: Session,
    camera_id: int,
    camera_in: CameraUpdate,
    current_user: Optional[User] = None
) -> Optional[Camera]:
    """
    Updates camera metadata, coordinates, or Model 3 VMS settings.
    """
    db_camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not db_camera:
        return None

    update_data = camera_in.dict(exclude_unset=True)

    if "latitude" in update_data or "longitude" in update_data:
        lat = update_data.pop("latitude", None)
        lon = update_data.pop("longitude", None)
        if lat is not None and lon is not None:
            db_camera.location = f"POINT({lon} {lat})"

    for field, value in update_data.items():
        setattr(db_camera, field, value)

    db.commit()
    db.refresh(db_camera)

    log_audit_event(
        db=db,
        action="UPDATE_CAMERA",
        entity_type="cameras",
        entity_id=db_camera.camera_id,
        actor_reference=current_user.username if current_user else "system",
        details={"updated_fields": list(update_data.keys())}
    )
    return db_camera


def get_cameras_geojson(
    db: Session,
    department_id: Optional[int] = None,
    camera_type: Optional[str] = None,
    operational_status: Optional[str] = None,
    connectivity_status: Optional[str] = None,
    vms_vendor_id: Optional[str] = None,
    city: Optional[str] = None,
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    center_lat: Optional[float] = None,
    center_lon: Optional[float] = None,
    radius_meters: Optional[float] = None,
) -> GeoJSONFeatureCollection:
    """
    Query cameras across Gujarat and return RFC 7946 GeoJSON FeatureCollection
    containing Model 3 VMS federation parameters, Sentinel sandbox live feeds, and coverage radii.
    """
    query = db.query(
        Camera,
        func.ST_Y(Camera.location.cast(GeographyPoint())).label("latitude"),
        func.ST_X(Camera.location.cast(GeographyPoint())).label("longitude"),
        Department.name.label("department_name"),
        Department.code.label("department_code")
    ).join(Department, Camera.department_id == Department.department_id)

    if department_id:
        query = query.filter(Camera.department_id == department_id)

    if camera_type:
        query = query.filter(Camera.camera_type == camera_type)
    if operational_status:
        query = query.filter(Camera.operational_status == operational_status)
    if connectivity_status:
        query = query.filter(Camera.connectivity_status == connectivity_status)
    if vms_vendor_id:
        query = query.filter(Camera.vms_vendor_id == vms_vendor_id)

    # Spatial Filters
    if all(v is not None for v in [min_lon, min_lat, max_lon, max_lat]):
        envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        query = query.filter(func.ST_Intersects(Camera.location, envelope))

    if all(v is not None for v in [center_lat, center_lon, radius_meters]):
        center_point = func.ST_SetSRID(func.ST_Point(center_lon, center_lat), 4326)
        query = query.filter(func.ST_DWithin(Camera.location, center_point, radius_meters))

    results = query.all()
    today = date.today()
    features: List[GeoJSONFeature] = []
    sentinel_count = 0

    for cam, lat, lon, dept_name, dept_code in results:
        attrs = cam.attributes or {}
        cam_city = attrs.get("city", "Ahmedabad")

        if city and city != "all" and cam_city.lower() != city.lower():
            continue
        
        # Check if Sentinel Sandbox live stream camera
        is_sentinel = attrs.get("is_sentinel_live", False) or cam.vms_vendor_id == "sentinel"
        if is_sentinel:
            sentinel_count += 1
            sentinel_id = attrs.get("sentinel_id", cam.camera_id)
            rtsp_url = attrs.get("sentinel_rtsp_url", f"rtsp://sentinel-grid.internal:8554/stream/{sentinel_id}")
            webrtc_url = attrs.get("sentinel_webrtc_url", f"http://sentinel-grid.internal:8889/stream/{sentinel_id}/whep")
            hls_url = attrs.get("sentinel_hls_url", f"http://sentinel-grid.internal/live/stream/{sentinel_id}/index.m3u8")
            codec = attrs.get("codec", "H.264")
        else:
            sentinel_id = None
            rtsp_url = None
            webrtc_url = None
            hls_url = None
            codec = "H.264"

        # Calculate Age
        age_years = None
        is_ageing = False
        if cam.installed_at:
            age_years = round((today - cam.installed_at).days / 365.25, 1)
            is_ageing = age_years >= 5.0

        feature = GeoJSONFeature(
            type="Feature",
            geometry=GeoJSONGeometry(
                type="Point",
                coordinates=[float(lon), float(lat)]
            ),
            properties=GeoJSONProperties(
                camera_id=cam.camera_id,
                name=cam.name,
                external_reference=cam.external_reference,
                department_id=cam.department_id,
                department_name=dept_name,
                department_code=dept_code,
                camera_type=cam.camera_type,
                operational_status=cam.operational_status,
                connectivity_status=cam.connectivity_status,
                ownership_type=cam.ownership_type,
                access_class=cam.access_class,
                installed_at=cam.installed_at.isoformat() if cam.installed_at else None,
                address=cam.address,
                city=cam_city,
                
                # Model 3 VMS Federation Primitives
                vms_vendor_id=cam.vms_vendor_id or "hikvision",
                vms_stream_protocol=cam.vms_stream_protocol or "rtsp",
                external_camera_id=cam.external_camera_id or cam.external_reference,
                adapter_channel=cam.adapter_channel or f"ch-{cam.camera_id}",
                coverage_radius_meters=float(cam.coverage_radius_meters or 75.0),
                coverage_angle_degrees=float(cam.coverage_angle_degrees or 120.0),
                
                # Sentinel Live Stream Primitives
                is_sentinel_live=is_sentinel,
                sentinel_id=sentinel_id,
                sentinel_rtsp_url=rtsp_url,
                sentinel_webrtc_url=webrtc_url,
                sentinel_hls_url=hls_url,
                stream_codec=codec,
                
                age_years=age_years,
                is_ageing_alert=is_ageing,
                attributes=attrs
            )
        )
        features.append(feature)

    return GeoJSONFeatureCollection(
        type="FeatureCollection",
        features=features,
        total_count=len(features),
        sentinel_live_count=sentinel_count
    )
