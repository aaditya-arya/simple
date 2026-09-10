import io
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.auth import Department, User
from app.schemas.onboarding import BulkUploadRow, BulkUploadResponse, BulkUploadError
from app.services.audit_service import log_audit_event

VALID_CAMERA_TYPES = {'fixed', 'ptz', 'thermal', 'number_plate', 'body_worn', 'mobile', 'unknown'}
VALID_OWNERSHIP_TYPES = {'department_owned', 'shared', 'private_contractor', 'other'}
VALID_ACCESS_CLASSES = {'government_internal', 'government_public', 'partner_shared', 'restricted'}
VALID_CONNECTIVITY = {'online', 'offline', 'intermittent', 'unknown'}
VALID_OPERATIONAL = {'active', 'maintenance', 'retired', 'planned', 'unknown'}
VALID_VMS_VENDORS = {'hikvision', 'dahua', 'milestone', 'genetec', 'axis_companion', 'custom_rtsp'}

# Gujarat State Bounding Box: Lat [19.8, 24.9], Lon [68.0, 74.6]
GUJARAT_BOUNDS = {
    "min_lat": 19.8,
    "max_lat": 24.9,
    "min_lon": 68.0,
    "max_lon": 74.6
}

def find_column_value(row_dict: dict, aliases: List[str]) -> Optional[Any]:
    """Finds first matching value for list of possible column alias names, case-insensitively."""
    lower_dict = {str(k).strip().lower(): v for k, v in row_dict.items()}
    for alias in aliases:
        if alias.lower() in lower_dict and not pd.isna(lower_dict[alias.lower()]):
            return lower_dict[alias.lower()]
    return None

def process_bulk_file_upload(
    db: Session,
    file_bytes: bytes,
    filename: str,
    current_user: Optional[User] = None
) -> BulkUploadResponse:
    """
    Parses CSV or Excel file, validates coordinates and metadata against registry schema rules,
    persists valid cameras with PostGIS geometry (SRID 4326), and returns comprehensive diagnostics.
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            # Attempt to parse as CSV by default
            df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return BulkUploadResponse(
            total_processed=0,
            successfully_onboarded=0,
            failed_count=1,
            errors=[BulkUploadError(row_number=0, error_message=f"Failed to parse CSV/Excel table: {str(e)}")]
        )

    # Cache departments by code and ID
    all_depts = db.query(Department).all()
    departments_by_code = {d.code.upper(): d.department_id for d in all_depts}
    departments_by_id = {d.department_id: d for d in all_depts}
    default_dept_id = all_depts[0].department_id if all_depts else 1

    success_count = 0
    errors: List[BulkUploadError] = []
    cameras_to_add: List[Camera] = []

    for index, row in df.iterrows():
        row_num = int(index) + 2  # 1-indexed, accounting for header row
        row_dict = row.to_dict()

        # 1. Camera Name
        raw_name = find_column_value(row_dict, ["name", "camera_name", "device_name", "camera", "title", "id"])
        name = str(raw_name).strip() if raw_name else f"Gujarat-CCTV-Cam-{row_num}"
        if not name or name == "nan":
            name = f"Gujarat-CCTV-Cam-{row_num}"

        # 2. Coordinates (Lat / Lon)
        raw_lat = find_column_value(row_dict, ["latitude", "lat", "lat_deg", "y", "y_coord", "lat_dd"])
        raw_lon = find_column_value(row_dict, ["longitude", "long", "lon", "lng", "x", "x_coord", "lon_dd"])

        if raw_lat is None or raw_lon is None:
            errors.append(BulkUploadError(
                row_number=row_num,
                camera_name=name,
                error_message="Missing latitude or longitude coordinate column"
            ))
            continue

        try:
            lat = float(str(raw_lat).strip())
            lon = float(str(raw_lon).strip())
        except (ValueError, TypeError):
            errors.append(BulkUploadError(
                row_number=row_num,
                camera_name=name,
                error_message=f"Invalid coordinate numbers (lat: {raw_lat}, lon: {raw_lon})"
            ))
            continue

        # Check global bounds
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            errors.append(BulkUploadError(
                row_number=row_num,
                camera_name=name,
                error_message=f"Coordinates out of bounds: ({lat}, {lon})"
            ))
            continue

        # 3. Department Resolution
        dept_id = None
        raw_dept = find_column_value(row_dict, ["department_id", "dept_id", "department_code", "dept_code", "department", "dept"])
        if raw_dept is not None:
            dept_str = str(raw_dept).strip()
            if dept_str.isdigit():
                d_cand = int(dept_str)
                if d_cand in departments_by_id:
                    dept_id = d_cand
            elif dept_str.upper() in departments_by_code:
                dept_id = departments_by_code[dept_str.upper()]

        if not dept_id:
            if current_user and current_user.department_id:
                dept_id = current_user.department_id
            else:
                dept_id = default_dept_id

        # 4. Enums & Metadata
        raw_cam_type = find_column_value(row_dict, ["camera_type", "type", "camera_model_type"])
        cam_type = str(raw_cam_type).lower().strip() if raw_cam_type else "fixed"
        if cam_type not in VALID_CAMERA_TYPES:
            cam_type = "fixed"

        raw_vms = find_column_value(row_dict, ["vms_vendor_id", "vms_vendor", "vms", "vendor"])
        vms_vendor = str(raw_vms).lower().strip() if raw_vms else "hikvision"
        if vms_vendor not in VALID_VMS_VENDORS:
            vms_vendor = "hikvision"

        raw_protocol = find_column_value(row_dict, ["stream_protocol", "vms_stream_protocol", "protocol"])
        stream_protocol = str(raw_protocol).lower().strip() if raw_protocol else "rtsp"

        raw_ownership = find_column_value(row_dict, ["ownership_type", "ownership"])
        ownership = str(raw_ownership).lower().strip() if raw_ownership else "department_owned"
        if ownership not in VALID_OWNERSHIP_TYPES:
            ownership = "department_owned"

        raw_access = find_column_value(row_dict, ["access_class", "access"])
        access = str(raw_access).lower().strip() if raw_access else "restricted"
        if access not in VALID_ACCESS_CLASSES:
            access = "restricted"

        raw_op_status = find_column_value(row_dict, ["operational_status", "status"])
        op_status = str(raw_op_status).lower().strip() if raw_op_status else "active"
        if op_status not in VALID_OPERATIONAL:
            op_status = "active"

        raw_conn_status = find_column_value(row_dict, ["connectivity_status", "connectivity"])
        conn_status = str(raw_conn_status).lower().strip() if raw_conn_status else "online"
        if conn_status not in VALID_CONNECTIVITY:
            conn_status = "online"

        addr = find_column_value(row_dict, ["address", "location_name", "street", "junction", "landmark"])
        address_str = str(addr).strip() if addr else f"Lat: {lat:.4f}, Lon: {lon:.4f}"

        mfg = find_column_value(row_dict, ["manufacturer", "brand", "make"])
        mfg_str = str(mfg).strip() if mfg else "Hikvision Digital"

        model_name = find_column_value(row_dict, ["model", "model_number"])
        model_str = str(model_name).strip() if model_name else "DS-2CD2043G2-I"

        serial_num = find_column_value(row_dict, ["serial_number", "serial", "sr_no"])
        serial_str = str(serial_num).strip() if serial_num else f"SN-GJ-{row_num}-{int(lat*1000)%10000}"

        ext_ref = find_column_value(row_dict, ["external_reference", "external_id", "asset_id"])
        ext_ref_str = str(ext_ref).strip() if ext_ref else f"GJ-ASSET-{1000 + row_num}"

        # PostGIS WKT Point
        wkt_point = f"POINT({lon} {lat})"

        camera_obj = Camera(
            external_reference=ext_ref_str,
            name=name,
            department_id=dept_id,
            location=wkt_point,
            address=address_str,
            manufacturer=mfg_str,
            model=model_str,
            serial_number=serial_str,
            camera_type=cam_type,
            ownership_type=ownership,
            access_class=access,
            connectivity_status=conn_status,
            operational_status=op_status,
            vms_vendor_id=vms_vendor,
            vms_stream_protocol=stream_protocol,
            attributes={
                "bulk_import": True,
                "source_file": filename,
                "imported_at": datetime.utcnow().isoformat(),
                "city": "Gujarat Statewide"
            }
        )
        cameras_to_add.append(camera_obj)
        success_count += 1

    # Bulk insert valid camera entities into PostgreSQL/PostGIS
    if cameras_to_add:
        try:
            db.add_all(cameras_to_add)
            db.commit()

            username = current_user.username if current_user else "admin_system"
            log_audit_event(
                db=db,
                action="BULK_ONBOARDING",
                entity_type="cameras",
                actor_reference=username,
                details={
                    "filename": filename,
                    "count": len(cameras_to_add),
                    "failed_count": len(errors)
                }
            )
        except Exception as e:
            db.rollback()
            return BulkUploadResponse(
                total_processed=len(df),
                successfully_onboarded=0,
                failed_count=len(df),
                errors=[BulkUploadError(row_number=0, error_message=f"Database PostGIS commit error: {str(e)}")]
            )

    return BulkUploadResponse(
        total_processed=len(df),
        successfully_onboarded=success_count,
        failed_count=len(errors),
        errors=errors
    )
