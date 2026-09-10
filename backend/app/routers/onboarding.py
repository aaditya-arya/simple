from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import io

from app.database import get_db
from app.models.auth import User
from app.schemas.camera import CameraCreate, CameraResponse
from app.schemas.onboarding import BulkUploadResponse, BulkUploadRow, BulkUploadError
from app.core.rbac import get_current_user, get_current_user_optional, require_roles, check_department_access
from app.services.camera_service import create_camera, GeographyPoint
from app.services.onboarding_service import process_bulk_file_upload
from app.services.audit_service import log_audit_event
from app.models.camera import Camera
from app.models.auth import Department
from sqlalchemy import func

router = APIRouter(prefix="/onboarding", tags=["Onboarding & Validation Engine"])

@router.get("/template")
def download_csv_template():
    """
    Returns a downloadable sample CSV template formatted with statewide Gujarat camera records.
    """
    csv_data = (
        "name,latitude,longitude,department_code,camera_type,vms_vendor_id,stream_protocol,address,operational_status\n"
        "Ahmedabad-SG-Highway-PTZ-01,23.0550,72.5180,TRAFFIC,ptz,hikvision,rtsp,SG Highway Thaltej Junction,active\n"
        "Gandhinagar-GIFT-City-ANPR-02,23.1610,72.6840,POLICE,number_plate,dahua,rtsp,GIFT City Main Concourse,active\n"
        "Surat-Textile-Market-Fixed-03,21.1960,72.8310,SMART_CITY,fixed,milestone,rtsp,Ring Road Flyover Junction,active\n"
        "Vadodara-Alkapuri-PTZ-04,22.3120,73.1750,MUNICIPAL,ptz,genetec,rtsp,Alkapuri Commercial Hub,active\n"
        "Rajkot-Kalawad-Road-Cam-05,22.2890,70.7650,TRAFFIC,fixed,hikvision,rtsp,Kalawad Road KKV Hall,active\n"
        "Bhavnagar-Port-Corridor-06,21.7645,72.1520,STATE_SURVEILLANCE,ptz,dahua,rtsp,Ghogha Circle Marine Gate,active\n"
        "Jamnagar-Refinery-Bypass-07,22.4710,70.0580,POLICE,number_plate,hikvision,rtsp,Digjam Coastal Freight Corridor,active\n"
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gujarat_cctv_onboarding_template.csv"}
    )

@router.post("/manual", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def manual_camera_onboarding(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Manual Entry: Onboard a single camera with full coordinate & metadata validation.
    """
    user = current_user or User(user_id=1, username="admin", role_id=1, department_id=1)
    
    # Check if department exists
    dept = db.query(Department).filter(Department.department_id == camera_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department does not exist")

    created_cam = create_camera(db, camera_in, user)

    result = db.query(
        Camera,
        func.ST_Y(Camera.location.cast(GeographyPoint())).label("lat"),
        func.ST_X(Camera.location.cast(GeographyPoint())).label("lon"),
        Department.name.label("dept_name")
    ).join(Department, Camera.department_id == Department.department_id).filter(Camera.camera_id == created_cam.camera_id).first()

    cam, lat, lon, dept_name = result
    return CameraResponse(
        camera_id=cam.camera_id,
        external_reference=cam.external_reference,
        name=cam.name,
        department_id=cam.department_id,
        department_name=dept_name,
        latitude=float(lat),
        longitude=float(lon),
        address=cam.address,
        manufacturer=cam.manufacturer,
        model=cam.model,
        serial_number=cam.serial_number,
        camera_type=cam.camera_type,
        ownership_type=cam.ownership_type,
        access_class=cam.access_class,
        connectivity_status=cam.connectivity_status,
        operational_status=cam.operational_status,
        installed_at=cam.installed_at,
        last_seen_at=cam.last_seen_at,
        notes=cam.notes,
        attributes=cam.attributes or {},
        created_at=cam.created_at,
        updated_at=cam.updated_at
    )

@router.post("/bulk-file", response_model=BulkUploadResponse)
async def bulk_file_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Bulk Upload: Upload CSV or Excel file containing hundreds/thousands of CCTV records.
    Performs batch validation and reports row-level errors.
    """
    contents = await file.read()
    user = current_user or User(user_id=1, username="admin", role_id=1, department_id=1)
    return process_bulk_file_upload(
        db=db,
        file_bytes=contents,
        filename=file.filename or "upload.csv",
        current_user=user
    )

@router.post("/api-batch", response_model=BulkUploadResponse)
def api_batch_onboarding(
    batch: List[BulkUploadRow],
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    API Ingestion: Standardized endpoint for automated VMS and integration sync services.
    """
    user = current_user or User(user_id=1, username="admin", role_id=1, department_id=1)
    success_count = 0
    errors: List[BulkUploadError] = []
    cameras_to_add: List[Camera] = []

    for idx, item in enumerate(batch):
        dept_id = item.department_id or user.department_id or 1

        wkt_point = f"POINT({item.longitude} {item.latitude})"
        cam = Camera(
            external_reference=item.external_reference,
            name=item.name,
            department_id=dept_id,
            location=wkt_point,
            address=item.address,
            manufacturer=item.manufacturer,
            model=item.model,
            serial_number=item.serial_number,
            camera_type=item.camera_type,
            ownership_type=item.ownership_type,
            access_class=item.access_class,
            connectivity_status=item.connectivity_status,
            operational_status=item.operational_status,
            attributes=item.attributes
        )
        cameras_to_add.append(cam)
        success_count += 1

    if cameras_to_add:
        db.add_all(cameras_to_add)
        db.commit()
        log_audit_event(
            db=db,
            action="API_BATCH_ONBOARDING",
            entity_type="cameras",
            actor_reference=user.username,
            details={"count": len(cameras_to_add)}
        )

    return BulkUploadResponse(
        total_processed=len(batch),
        successfully_onboarded=success_count,
        failed_count=len(errors),
        errors=errors
    )
