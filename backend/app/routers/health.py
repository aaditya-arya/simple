from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.camera import Camera, VMSMiddlewareEvent
from app.models.health import CameraHealthSnapshot
from app.models.auth import Department, User
from app.schemas.health import (
    HealthTelemetryCreate, HealthSnapshotResponse,
    SystemHealthSummaryResponse, DepartmentHealthSummary
)
from app.schemas.camera import MiddlewareEventCreate, MiddlewareEventResponse
from app.core.rbac import get_current_user, require_roles, check_department_access

router = APIRouter(prefix="/health", tags=["Camera Health & Model 3 Middleware Events"])

@router.post("/telemetry", response_model=HealthSnapshotResponse, status_code=status.HTTP_201_CREATED)
def record_health_telemetry(
    telemetry_in: HealthTelemetryCreate,
    db: Session = Depends(get_db)
):
    """
    Ingest connectivity, latency, and packet loss telemetry snapshot.
    Updates the camera's live status and appends a historical snapshot.
    """
    camera = db.query(Camera).filter(Camera.camera_id == telemetry_in.camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    camera.connectivity_status = telemetry_in.connectivity_status
    camera.last_seen_at = datetime.utcnow()

    snapshot = CameraHealthSnapshot(
        camera_id=telemetry_in.camera_id,
        connectivity_status=telemetry_in.connectivity_status,
        latency_ms=telemetry_in.latency_ms,
        packet_loss_percent=telemetry_in.packet_loss_percent,
        details=telemetry_in.details
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot


@router.post("/event", response_model=MiddlewareEventResponse, status_code=status.HTTP_201_CREATED)
def ingest_model3_middleware_event(
    event_in: MiddlewareEventCreate,
    db: Session = Depends(get_db)
):
    """
    Model 3 Event Hook:
    Allows external VMS adapters (Hikvision ISAPI, Dahua DHOP, Milestone MIP SDK, Genetec Webhooks)
    or message brokers (Kafka/RabbitMQ consumers) to stream status changes and detection events.
    """
    # Locate camera either by internal ID or by external VMS camera ID
    camera = None
    if event_in.camera_id:
        camera = db.query(Camera).filter(Camera.camera_id == event_in.camera_id).first()
    elif event_in.external_camera_id:
        camera = db.query(Camera).filter(
            Camera.vms_vendor_id == event_in.vms_vendor_id,
            Camera.external_camera_id == event_in.external_camera_id
        ).first()

    status_changed = False
    if camera:
        camera.last_seen_at = datetime.utcnow()
        if event_in.new_status and event_in.new_status in ["online", "offline", "intermittent"]:
            camera.connectivity_status = event_in.new_status
            status_changed = True

    event_record = VMSMiddlewareEvent(
        camera_id=camera.camera_id if camera else None,
        vms_vendor_id=event_in.vms_vendor_id,
        external_camera_id=event_in.external_camera_id,
        event_type=event_in.event_type,
        severity=event_in.severity,
        payload=event_in.payload
    )
    db.add(event_record)
    db.commit()
    db.refresh(event_record)

    return MiddlewareEventResponse(
        event_id=event_record.event_id,
        camera_id=event_record.camera_id,
        vms_vendor_id=event_record.vms_vendor_id,
        event_type=event_record.event_type,
        severity=event_record.severity,
        received_at=event_record.received_at,
        status_updated=status_changed
    )


@router.get("/summary", response_model=SystemHealthSummaryResponse)
def get_system_health_summary(
    db: Session = Depends(get_db)
):
    """
    Returns aggregated health status (online, offline, intermittent, SLA percentage)
    system-wide and broken down by department.
    """
    departments = db.query(Department).filter(Department.is_active == True).all()
    dept_summaries: List[DepartmentHealthSummary] = []

    total_all = 0
    online_all = 0
    offline_all = 0
    intermittent_all = 0
    unknown_all = 0

    for d in departments:
        cameras = db.query(Camera).filter(Camera.department_id == d.department_id).all()
        d_total = len(cameras)
        d_online = sum(1 for c in cameras if c.connectivity_status == "online")
        d_offline = sum(1 for c in cameras if c.connectivity_status == "offline")
        d_intermittent = sum(1 for c in cameras if c.connectivity_status == "intermittent")
        d_unknown = sum(1 for c in cameras if c.connectivity_status == "unknown")
        
        uptime = round((d_online / d_total * 100), 1) if d_total > 0 else 100.0

        dept_summaries.append(
            DepartmentHealthSummary(
                department_id=d.department_id,
                department_name=d.name,
                total_cameras=d_total,
                online_count=d_online,
                offline_count=d_offline,
                intermittent_count=d_intermittent,
                unknown_count=d_unknown,
                uptime_percentage=uptime
            )
        )

        total_all += d_total
        online_all += d_online
        offline_all += d_offline
        intermittent_all += d_intermittent
        unknown_all += d_unknown

    overall_uptime = round((online_all / total_all * 100), 1) if total_all > 0 else 100.0

    return SystemHealthSummaryResponse(
        total_cameras=total_all,
        online_count=online_all,
        offline_count=offline_all,
        intermittent_count=intermittent_all,
        unknown_count=unknown_all,
        overall_health_percentage=overall_uptime,
        by_department=dept_summaries
    )


@router.get("/camera/{camera_id}/history", response_model=List[HealthSnapshotResponse])
def get_camera_health_history(
    camera_id: int,
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve time-series health snapshots for a specific camera."""
    cam = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    snapshots = db.query(CameraHealthSnapshot).filter(
        CameraHealthSnapshot.camera_id == camera_id
    ).order_by(CameraHealthSnapshot.observed_at.desc()).limit(limit).all()

    return snapshots
