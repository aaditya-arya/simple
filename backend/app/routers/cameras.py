from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import pandas as pd
import io

from app.database import get_db
from app.models.camera import Camera
from app.models.auth import Department, User
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from app.core.rbac import get_current_user, require_roles, check_department_access
from app.services.camera_service import create_camera, update_camera, GeographyPoint
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/cameras", tags=["Cameras Management"])

@router.get("", response_model=List[CameraResponse])
def list_cameras(
    department_id: Optional[int] = Query(None),
    camera_type: Optional[str] = Query(None),
    operational_status: Optional[str] = Query(None),
    connectivity_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by name, address, or serial"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search and filter cameras with department-wise scoping.
    """
    query = db.query(
        Camera,
        func.ST_Y(Camera.location.cast(GeographyPoint())).label("lat"),
        func.ST_X(Camera.location.cast(GeographyPoint())).label("lon"),
        Department.name.label("dept_name")
    ).join(Department, Camera.department_id == Department.department_id)

    # Department RBAC enforcement
    if current_user.role.name not in ["super_admin", "auditor"]:
        query = query.filter(Camera.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Camera.department_id == department_id)

    if camera_type:
        query = query.filter(Camera.camera_type == camera_type)
    if operational_status:
        query = query.filter(Camera.operational_status == operational_status)
    if connectivity_status:
        query = query.filter(Camera.connectivity_status == connectivity_status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Camera.name.ilike(search_pattern)) |
            (Camera.address.ilike(search_pattern)) |
            (Camera.serial_number.ilike(search_pattern))
        )

    results = query.offset(offset).limit(limit).all()
    
    responses = []
    for cam, lat, lon, dept_name in results:
        res = CameraResponse(
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
        responses.append(res)
    return responses


@router.get("/export/csv")
def export_cameras_csv(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export camera registry to CSV for reporting and audits.
    """
    query = db.query(
        Camera.camera_id,
        Camera.name,
        Department.name.label("department"),
        func.ST_Y(Camera.location.cast(GeographyPoint())).label("latitude"),
        func.ST_X(Camera.location.cast(GeographyPoint())).label("longitude"),
        Camera.camera_type,
        Camera.operational_status,
        Camera.connectivity_status,
        Camera.installed_at,
        Camera.manufacturer,
        Camera.model,
        Camera.address
    ).join(Department, Camera.department_id == Department.department_id)

    if current_user.role.name not in ["super_admin", "auditor"]:
        query = query.filter(Camera.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Camera.department_id == department_id)

    df = pd.DataFrame(query.all())
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    log_audit_event(
        db=db,
        action="EXPORT_CAMERAS_CSV",
        entity_type="cameras",
        actor_reference=current_user.username,
        details={"record_count": len(df)}
    )

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cctv_camera_registry.csv"}
    )


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera_detail(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete metadata for a single camera."""
    result = db.query(
        Camera,
        func.ST_Y(Camera.location.cast(GeographyPoint())).label("lat"),
        func.ST_X(Camera.location.cast(GeographyPoint())).label("lon"),
        Department.name.label("dept_name")
    ).join(Department, Camera.department_id == Department.department_id).filter(Camera.camera_id == camera_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Camera not found")

    cam, lat, lon, dept_name = result
    if not check_department_access(current_user, cam.department_id):
        raise HTTPException(status_code=403, detail="Access denied to camera from another department")

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


@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera_endpoint(
    camera_id: int,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """Update camera metadata with RBAC verification."""
    existing_cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not existing_cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    if not check_department_access(current_user, existing_cam.department_id):
        raise HTTPException(status_code=403, detail="Unauthorized to edit camera belonging to another department")

    updated = update_camera(db, camera_id, camera_in, current_user)
    return get_camera_detail(camera_id, db, current_user)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """Delete a camera from the registry."""
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    if not check_department_access(current_user, cam.department_id):
        raise HTTPException(status_code=403, detail="Unauthorized to delete camera belonging to another department")

    cam_name = cam.name
    dept_id = cam.department_id
    db.delete(cam)
    db.commit()

    log_audit_event(
        db=db,
        action="DELETE_CAMERA",
        entity_type="cameras",
        entity_id=camera_id,
        actor_reference=current_user.username,
        details={"deleted_camera_name": cam_name, "department_id": dept_id}
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
