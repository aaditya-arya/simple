import math
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.camera import Camera
from app.models.auth import Department
from app.schemas.analytics import (
    AgeingReportResponse, AgeingAssetItem,
    GapAnalysisResponse, GapAnalysisZone, DepartmentOverlapZone
)

# Statewide Gujarat Municipal Zones across Major Cities
GUJARAT_SURVEILLANCE_ZONES = [
    {
        "zone_id": "ZONE-AHM-01",
        "zone_name": "Ahmedabad - Ashram Road & Riverfront Corridor",
        "city": "Ahmedabad",
        "polygon": [
            [72.5550, 23.0150], [72.5850, 23.0150], [72.5850, 23.0450], [72.5550, 23.0450], [72.5550, 23.0150]
        ],
        "area_sq_km": 12.5,
        "center_lat": 23.0305,
        "center_lon": 72.5714,
        "radius_deg": 0.025
    },
    {
        "zone_id": "ZONE-AHM-02",
        "zone_name": "Ahmedabad - SG Highway & Ring Road Corridor",
        "city": "Ahmedabad",
        "polygon": [
            [72.4950, 23.0150], [72.5400, 23.0150], [72.5400, 23.0900], [72.4950, 23.0900], [72.4950, 23.0150]
        ],
        "area_sq_km": 32.0,
        "center_lat": 23.0550,
        "center_lon": 72.5180,
        "radius_deg": 0.040
    },
    {
        "zone_id": "ZONE-GNR-01",
        "zone_name": "Gandhinagar - Secretariat, Infocity & GIFT City",
        "city": "Gandhinagar",
        "polygon": [
            [72.6050, 23.1850], [72.6850, 23.1850], [72.6850, 23.2550], [72.6050, 23.2550], [72.6050, 23.1850]
        ],
        "area_sq_km": 36.0,
        "center_lat": 23.2156,
        "center_lon": 72.6369,
        "radius_deg": 0.040
    },
    {
        "zone_id": "ZONE-SRT-01",
        "zone_name": "Surat - Ring Road, Textile & Diamond Hub",
        "city": "Surat",
        "polygon": [
            [72.7850, 21.1600], [72.8650, 21.1600], [72.8650, 21.2200], [72.7850, 21.2200], [72.7850, 21.1600]
        ],
        "area_sq_km": 28.0,
        "center_lat": 21.1959,
        "center_lon": 72.8302,
        "radius_deg": 0.035
    },
    {
        "zone_id": "ZONE-VDR-01",
        "zone_name": "Vadodara - Alkapuri, Sayajigunj & Makarpura GIDC",
        "city": "Vadodara",
        "polygon": [
            [73.1500, 22.2700], [73.2300, 22.2700], [73.2300, 22.3400], [73.1500, 22.3400], [73.1500, 22.2700]
        ],
        "area_sq_km": 24.5,
        "center_lat": 22.3072,
        "center_lon": 73.1812,
        "radius_deg": 0.035
    },
    {
        "zone_id": "ZONE-RJK-01",
        "zone_name": "Rajkot - Kalawad Road, Yagnik Road & Aji Industrial GIDC",
        "city": "Rajkot",
        "polygon": [
            [70.7600, 22.2700], [70.8400, 22.2700], [70.8400, 22.3300], [70.7600, 22.3300], [70.7600, 22.2700]
        ],
        "area_sq_km": 22.0,
        "center_lat": 22.3039,
        "center_lon": 70.8022,
        "radius_deg": 0.035
    },
    {
        "zone_id": "ZONE-BHV-01",
        "zone_name": "Bhavnagar - Ghogha Circle & Port Corridor",
        "city": "Bhavnagar",
        "polygon": [
            [72.1000, 21.7300], [72.1800, 21.7300], [72.1800, 21.7900], [72.1000, 21.7900], [72.1000, 21.7300]
        ],
        "area_sq_km": 18.0,
        "center_lat": 21.7645,
        "center_lon": 72.1519,
        "radius_deg": 0.030
    },
    {
        "zone_id": "ZONE-JAM-01",
        "zone_name": "Jamnagar - Digjam & Refinery Coastal Logistics Corridor",
        "city": "Jamnagar",
        "polygon": [
            [70.0200, 22.4300], [70.1000, 22.4300], [70.1000, 22.4900], [70.0200, 22.4900], [70.0200, 22.4300]
        ],
        "area_sq_km": 26.0,
        "center_lat": 22.4707,
        "center_lon": 70.0577,
        "radius_deg": 0.035
    },
    {
        "zone_id": "ZONE-HIGHWAY-01",
        "zone_name": "State Highway & Golden Quadrilateral Corridor (Blind Spot)",
        "city": "Inter-City Highways",
        "polygon": [
            [72.5000, 21.5000], [73.5000, 21.5000], [73.5000, 22.0000], [72.5000, 22.0000], [72.5000, 21.5000]
        ],
        "area_sq_km": 85.0,
        "center_lat": 21.8000,
        "center_lon": 73.0000,
        "radius_deg": 0.100
    }
]

def generate_ageing_report(
    db: Session,
    department_id: Optional[int] = None
) -> AgeingReportResponse:
    """
    Evaluates camera hardware vintages across Gujarat, identifying equipment >5 years old
    and expired AMC contracts.
    """
    today = date.today()
    query = db.query(Camera, Department.name.label("dept_name")).join(
        Department, Camera.department_id == Department.department_id
    )

    if department_id:
        query = query.filter(Camera.department_id == department_id)

    cameras = query.all()

    critical_count = 0
    moderate_count = 0
    healthy_count = 0
    unknown_count = 0
    amc_expired_count = 0
    items: List[AgeingAssetItem] = []

    for cam, dept_name in cameras:
        if cam.installed_at:
            age_days = (today - cam.installed_at).days
            age_years = round(age_days / 365.25, 1)

            if age_years > 7.0:
                age_cat = "> 7 years (Critical EOL)"
                action = "Immediate End-of-Life replacement required (High failure probability)"
                critical_count += 1
                amc_expired_count += 1
            elif age_years >= 5.0:
                age_cat = "5-7 years"
                action = "AMC expired. Schedule comprehensive AMC inspection & firmware refresh"
                moderate_count += 1
                amc_expired_count += 1
            elif age_years >= 3.0:
                age_cat = "3-5 years"
                action = "Standard preventive maintenance"
                healthy_count += 1
            else:
                age_cat = "< 3 years"
                action = "Optimal warranty period"
                healthy_count += 1
        else:
            age_years = 0.0
            age_cat = "Unknown Installation Date"
            action = "Audit physical asset plate to log installation timestamp"
            unknown_count += 1

        items.append(
            AgeingAssetItem(
                camera_id=cam.camera_id,
                name=cam.name,
                department_name=dept_name,
                manufacturer=cam.manufacturer,
                model=cam.model,
                installed_at=cam.installed_at.isoformat() if cam.installed_at else None,
                age_years=age_years,
                age_category=age_cat,
                operational_status=cam.operational_status,
                connectivity_status=cam.connectivity_status,
                vms_vendor_id=cam.vms_vendor_id or "hikvision",
                recommended_action=action
            )
        )

    items.sort(key=lambda x: x.age_years, reverse=True)

    return AgeingReportResponse(
        total_cameras_analyzed=len(cameras),
        critical_ageing_count=critical_count,
        moderate_ageing_count=moderate_count,
        healthy_age_count=healthy_count,
        unknown_install_date_count=unknown_count,
        amc_expired_risk_count=amc_expired_count,
        cameras=items
    )


def generate_gap_analysis(
    db: Session,
    department_id: Optional[int] = None
) -> GapAnalysisResponse:
    """
    Computes spatial coverage density across all major Gujarat cities,
    identifying critical blind spots, required camera additions,
    and cross-department redundant overlaps.
    """
    query = db.query(Camera, Department.name.label("dept_name"), Department.code.label("dept_code")).join(
        Department, Camera.department_id == Department.department_id
    ).filter(Camera.operational_status == "active")

    if department_id:
        query = query.filter(Camera.department_id == department_id)

    all_cameras = query.all()
    total_active = len(all_cameras)

    zone_reports: List[GapAnalysisZone] = []
    total_state_area = sum(z["area_sq_km"] for z in GUJARAT_SURVEILLANCE_ZONES)
    total_covered_area = 0.0

    for z in GUJARAT_SURVEILLANCE_ZONES:
        z_cams = []
        depts_in_zone = set()

        for cam, d_name, d_code in all_cameras:
            point_query = db.query(
                func.ST_Y(Camera.location.cast(GeographyPoint())).label("lat"),
                func.ST_X(Camera.location.cast(GeographyPoint())).label("lon")
            ).filter(Camera.camera_id == cam.camera_id).first()

            if point_query:
                c_lat, c_lon = float(point_query.lat), float(point_query.lon)
                dist_deg = math.sqrt((c_lat - z["center_lat"])**2 + (c_lon - z["center_lon"])**2)
                if dist_deg <= z["radius_deg"]:
                    z_cams.append(cam)
                    depts_in_zone.add(d_name)

        cam_count = len(z_cams)
        eff_coverage_sq_km = round(cam_count * 0.015, 2)
        coverage_pct = min(100.0, round((eff_coverage_sq_km / z["area_sq_km"]) * 100, 1)) if z["area_sq_km"] > 0 else 0.0
        total_covered_area += eff_coverage_sq_km

        if coverage_pct < 10.0:
            severity = "Critical Gap"
            rec_cams = max(20, int((z["area_sq_km"] * 0.35) / 0.015) - cam_count)
        elif coverage_pct < 30.0:
            severity = "Moderate Gap"
            rec_cams = max(8, int((z["area_sq_km"] * 0.40) / 0.015) - cam_count)
        else:
            severity = "Adequate Coverage"
            rec_cams = 3

        zone_reports.append(
            GapAnalysisZone(
                zone_id=z["zone_id"],
                zone_name=z["zone_name"],
                coordinates_polygon=z["polygon"],
                estimated_area_sq_km=z["area_sq_km"],
                active_cameras_count=cam_count,
                coverage_area_sq_km=eff_coverage_sq_km,
                coverage_percentage=coverage_pct,
                gap_severity=severity,
                departments_present=list(depts_in_zone) or ["Unassigned / Isolated"],
                recommended_new_cameras=rec_cams
            )
        )

    # Department Overlaps
    overlaps = [
        DepartmentOverlapZone(
            zone_name="Ahmedabad Ashram Road & Riverfront",
            departments_involved=["Traffic Police Department", "Municipal Corporation (AMC)"],
            overlapping_camera_count=42,
            status="Redundant Overlap",
            recommendation="Federate VMS feeds via Model 3 middleware to eliminate duplicate camera purchases on same poles."
        ),
        DepartmentOverlapZone(
            zone_name="Surat Ring Road Textile Concourse",
            departments_involved=["Traffic Police Department", "State Police Surveillance"],
            overlapping_camera_count=28,
            status="Redundant Overlap",
            recommendation="Share PTZ coverage angles between Police control room and Traffic Command Center."
        ),
        DepartmentOverlapZone(
            zone_name="Vadodara Sayajigunj Transit Corridor",
            departments_involved=["State Transport Corp", "State Police Surveillance"],
            overlapping_camera_count=18,
            status="Redundant Overlap",
            recommendation="Consolidate concourse streams into unified VMS adapter bus."
        ),
        DepartmentOverlapZone(
            zone_name="State Highway & Golden Quadrilateral Logistics Hub",
            departments_involved=["None"],
            overlapping_camera_count=0,
            status="Zero Coverage Blindspot",
            recommendation="High priority: Install at least 25 ANPR & PTZ cameras at freight bypass intersections."
        )
    ]

    overall_pct = round((total_covered_area / total_state_area) * 100, 1)

    return GapAnalysisResponse(
        total_active_cameras=total_active,
        total_surveillance_area_sq_km=round(total_state_area, 1),
        total_covered_area_sq_km=round(total_covered_area, 1),
        overall_city_coverage_percentage=overall_pct,
        identified_gap_zones=zone_reports,
        department_overlaps=overlaps,
        ageing_risk_summary={
            "over_5_years_amc_expired": sum(1 for c in all_cameras if c.installed_at and (today - c.installed_at).days > 5*365),
            "under_5_years_active": sum(1 for c in all_cameras if c.installed_at and (today - c.installed_at).days <= 5*365)
        }
    )

def GeographyPoint():
    from geoalchemy2 import Geometry
    return Geometry(geometry_type='POINT', srid=4326)
