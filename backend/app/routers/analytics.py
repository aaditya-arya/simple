from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.auth import User
from app.schemas.analytics import AgeingReportResponse, GapAnalysisResponse
from app.core.rbac import get_current_user_optional
from app.services.analytics_service import generate_ageing_report, generate_gap_analysis

router = APIRouter(prefix="/analytics", tags=["Gap Analysis & Ageing Reports"])

@router.get("/ageing-assets", response_model=AgeingReportResponse)
def get_ageing_assets_report(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Ageing Infrastructure Report:
    Identifies cameras exceeding warranty / operational lifespan (>5 years, >7 years)
    for proactive maintenance and replacement budgeting across Gujarat cities.
    """
    scoped_dept_id = department_id
    if current_user and current_user.role and current_user.role.name not in ["super_admin", "auditor"]:
        scoped_dept_id = current_user.department_id

    return generate_ageing_report(db=db, department_id=scoped_dept_id)


@router.get("/gap-analysis", response_model=GapAnalysisResponse)
def get_gap_analysis_report(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Gap-Analysis Report:
    Evaluates geographical surveillance density across major municipal corporations in Gujarat
    (Ahmedabad, Gandhinagar, Surat, Vadodara, Rajkot, Bhavnagar, Jamnagar).
    """
    scoped_dept_id = department_id
    if current_user and current_user.role and current_user.role.name not in ["super_admin", "auditor"]:
        scoped_dept_id = current_user.department_id

    return generate_gap_analysis(db=db, department_id=scoped_dept_id)
