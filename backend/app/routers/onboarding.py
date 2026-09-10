from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.auth import User
from app.schemas.camera import CameraCreate, CameraResponse
from app.schemas.onboarding import BulkUploadResponse, BulkUploadRow, BulkUploadError
from app.core.rbac import get_current_user, require_roles, check_department_access
from app.services.camera_service import create_camera, GeographyPoint
from app.services.onboarding_service import process_bulk_file_upload
from app.services.audit_service import log_audit_event
from app.models.camera import Camera
from app.models.auth import Department
from sqlalchemy import func

router = APIRouter(prefix="/onboarding", tags=["Onboarding & Validation Engine"])

@router.post("/manual", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def manual_camera_onboarding(
    camera_in: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """
    Manual Entry: Onboard a single camera with full coordinate & metadata validation.
    """
    if not check_department_access(current_user, camera_in.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot onboard camera to another department"
        )

    # Check if department exists
    dept = db.query(Department).filter(Department.department_id == camera_in.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department does not exist")

    created_cam = create_camera(db, camera_in, current_user)

    # Return full response
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
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """
    Bulk Upload: Upload CSV or Excel file containing hundreds/thousands of CCTV records.
    Performs batch validation and reports row-level errors.
    """
    contents = await file.read()
    return process_bulk_file_upload(
        db=db,
        file_bytes=contents,
        filename=file.filename or "upload.csv",
        current_user=current_user
    )


@router.post("/api-batch", response_model=BulkUploadResponse)
def api_batch_onboarding(
    batch: List[BulkUploadRow],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """
    API Ingestion: Standardized endpoint for automated VMS and integration sync services.
    """
    success_count = 0
    errors: List[BulkUploadError] = []
    cameras_to_add: List[Camera] = []

    for idx, item in enumerate(batch):
        dept_id = item.department_id or current_user.department_id
        if not dept_id:
            errors.append(BulkUploadError(row_number=idx, camera_name=item.name, error_message="department_id required"))
            continue

        if not check_department_access(current_user, dept_id):
            errors.append(BulkUploadError(row_number=idx, camera_name=item.name, error_message="Unauthorized department"))
            continue

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
            actor_reference=current_user.username,
            details={"count": len(cameras_to_add)}
        )

    return BulkUploadResponse(
        total_processed=len(batch),
        successfully_onboarded=success_count,
        failed_count=len(errors),
        errors=errors
    )
