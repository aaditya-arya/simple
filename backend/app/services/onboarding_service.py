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

def process_bulk_file_upload(
    db: Session,
    file_bytes: bytes,
    filename: str,
    current_user: User
) -> BulkUploadResponse:
    """
    Parses CSV or Excel file, validates rows against registry schema rules,
    persists valid cameras with PostGIS geometry, and returns detailed error diagnostics.
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return BulkUploadResponse(
                total_processed=0,
                successfully_onboarded=0,
                failed_count=1,
                errors=[BulkUploadError(row_number=0, error_message="Unsupported file format. Please upload .csv or .xlsx")]
            )
    except Exception as e:
        return BulkUploadResponse(
            total_processed=0,
            successfully_onboarded=0,
            failed_count=1,
            errors=[BulkUploadError(row_number=0, error_message=f"Failed to parse file: {str(e)}")]
        )

    # Cache departments by code and ID
    departments_by_code = {d.code.upper(): d.department_id for d in db.query(Department).all()}
    departments_by_id = {d.department_id: d for d in db.query(Department).all()}

    success_count = 0
    errors: List[BulkUploadError] = []
    cameras_to_add: List[Camera] = []

    for index, row in df.iterrows():
        row_num = int(index) + 2  # 1-indexed, accounting for header
        row_dict = row.to_dict()

        # Extract & validate camera name
        name = str(row_dict.get("name", "")).strip()
        if not name or name == "nan":
            errors.append(BulkUploadError(row_number=row_num, error_message="Missing required field: 'name'"))
            continue

        # Extract & validate coordinates
        try:
            lat = float(row_dict.get("latitude"))
            lon = float(row_dict.get("longitude"))
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                errors.append(BulkUploadError(row_number=row_num, camera_name=name, error_message="Coordinates out of bounds (-90 to 90 for Lat, -180 to 180 for Lon)"))
                continue
        except (ValueError, TypeError):
            errors.append(BulkUploadError(row_number=row_num, camera_name=name, error_message="Invalid latitude or longitude format"))
            continue

        # Department resolution & RBAC enforcement
        dept_id = None
        if "department_id" in row_dict and not pd.isna(row_dict["department_id"]):
            try:
                dept_id = int(row_dict["department_id"])
            except ValueError:
                pass
        
        if not dept_id and "department_code" in row_dict and not pd.isna(row_dict["department_code"]):
            code = str(row_dict["department_code"]).strip().upper()
            dept_id = departments_by_code.get(code)

        # Fallback for dept-admin: assign their own department if not specified
        if not dept_id and current_user.department_id:
            dept_id = current_user.department_id

        if not dept_id or dept_id not in departments_by_id:
            errors.append(BulkUploadError(row_number=row_num, camera_name=name, error_message="Valid department_id or department_code is required"))
            continue

        # Enforce department scoping for non-superadmins
        if current_user.role.name != "super_admin" and current_user.department_id != dept_id:
            errors.append(BulkUploadError(row_number=row_num, camera_name=name, error_message="Unauthorized to onboard cameras for another department"))
            continue

        # Validations of enums
        cam_type = str(row_dict.get("camera_type", "fixed")).lower().strip()
        if cam_type not in VALID_CAMERA_TYPES:
            cam_type = "unknown"

        ownership = str(row_dict.get("ownership_type", "department_owned")).lower().strip()
        if ownership not in VALID_OWNERSHIP_TYPES:
            ownership = "department_owned"

        access = str(row_dict.get("access_class", "restricted")).lower().strip()
        if access not in VALID_ACCESS_CLASSES:
            access = "restricted"

        op_status = str(row_dict.get("operational_status", "active")).lower().strip()
        if op_status not in VALID_OPERATIONAL:
            op_status = "active"

        conn_status = str(row_dict.get("connectivity_status", "unknown")).lower().strip()
        if conn_status not in VALID_CONNECTIVITY:
            conn_status = "unknown"

        # Date parsing
        install_date = None
        if "installed_at" in row_dict and not pd.isna(row_dict["installed_at"]):
            try:
                install_date = pd.to_datetime(row_dict["installed_at"]).date()
            except Exception:
                install_date = None

        ext_ref = str(row_dict.get("external_reference", "")).strip()
        if not ext_ref or ext_ref == "nan":
            ext_ref = None

        addr = str(row_dict.get("address", "")).strip()
        if not addr or addr == "nan":
            addr = None

        mfg = str(row_dict.get("manufacturer", "")).strip()
        if not mfg or mfg == "nan":
            mfg = None

        model_name = str(row_dict.get("model", "")).strip()
        if not model_name or model_name == "nan":
            model_name = None

        serial_num = str(row_dict.get("serial_number", "")).strip()
        if not serial_num or serial_num == "nan":
            serial_num = None

        wkt_point = f"POINT({lon} {lat})"

        camera_obj = Camera(
            external_reference=ext_ref,
            name=name,
            department_id=dept_id,
            location=wkt_point,
            address=addr,
            manufacturer=mfg,
            model=model_name,
            serial_number=serial_num,
            camera_type=cam_type,
            ownership_type=ownership,
            access_class=access,
            connectivity_status=conn_status,
            operational_status=op_status,
            installed_at=install_date,
            attributes={"bulk_import": True, "source_file": filename}
        )
        cameras_to_add.append(camera_obj)
        success_count += 1

    if cameras_to_add:
        try:
            db.add_all(cameras_to_add)
            db.commit()

            log_audit_event(
                db=db,
                action="BULK_ONBOARDING",
                entity_type="cameras",
                actor_reference=current_user.username,
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
                errors=[BulkUploadError(row_number=0, error_message=f"Database commit error: {str(e)}")]
            )

    return BulkUploadResponse(
        total_processed=len(df),
        successfully_onboarded=success_count,
        failed_count=len(errors),
        errors=errors
    )
