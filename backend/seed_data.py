"""
High-Fidelity Statewide Gujarat Seed Script for CCTV Central Registry & Model 3 VMS Federation.
Generates 650+ realistic camera assets across 7 major Gujarat cities:
- Ahmedabad
- Gandhinagar
- Surat
- Vadodara
- Rajkot
- Bhavnagar
- Jamnagar
Includes 30 Dedicated Real Sentinel Sandbox Grid Live Streams (Rendered as White Markers).
Run with: python seed_data.py
"""

import random
from datetime import date, timedelta
from app.database import SessionLocal, Base, engine
from app.models.auth import Department, Role, User
from app.models.camera import Camera
from app.core.security import get_password_hash

# Geographic cluster anchors across all major cities of Gujarat
STATEWIDE_CITY_ZONES = [
    # 1. Ahmedabad
    {
        "city": "Ahmedabad",
        "zone_name": "Ahmedabad Central & Riverfront Corridor",
        "center_lat": 23.0305,
        "center_lon": 72.5714,
        "radius_spread": 0.025,
        "count": 120,
        "primary_depts": ["TRAFFIC_POLICE", "AMC_SMARTCITY"],
        "default_vendor": "hikvision"
    },
    {
        "city": "Ahmedabad",
        "zone_name": "Ahmedabad SG Highway & Ring Road Corridor",
        "center_lat": 23.0550,
        "center_lon": 72.5180,
        "radius_spread": 0.035,
        "count": 100,
        "primary_depts": ["TRAFFIC_POLICE", "STATE_TRANSIT"],
        "default_vendor": "dahua"
    },
    # 2. Gandhinagar
    {
        "city": "Gandhinagar",
        "zone_name": "Gandhinagar Secretariat & GIFT City Smart Corridor",
        "center_lat": 23.2156,
        "center_lon": 72.6369,
        "radius_spread": 0.030,
        "count": 85,
        "primary_depts": ["POLICE_SURVEILLANCE", "GUDA_GANDHINAGAR"],
        "default_vendor": "genetec"
    },
    # 3. Surat
    {
        "city": "Surat",
        "zone_name": "Surat Ring Road & Diamond Textile Hub",
        "center_lat": 21.1959,
        "center_lon": 72.8302,
        "radius_spread": 0.030,
        "count": 95,
        "primary_depts": ["TRAFFIC_POLICE", "POLICE_SURVEILLANCE"],
        "default_vendor": "hikvision"
    },
    # 4. Vadodara
    {
        "city": "Vadodara",
        "zone_name": "Vadodara Sayajigunj & GIDC Industrial Corridor",
        "center_lat": 22.3072,
        "center_lon": 73.1812,
        "radius_spread": 0.025,
        "count": 80,
        "primary_depts": ["AMC_SMARTCITY", "STATE_TRANSIT"],
        "default_vendor": "dahua"
    },
    # 5. Rajkot
    {
        "city": "Rajkot",
        "zone_name": "Rajkot Kalawad Road & Aji Industrial Belt",
        "center_lat": 22.3039,
        "center_lon": 70.8022,
        "radius_spread": 0.025,
        "count": 75,
        "primary_depts": ["TRAFFIC_POLICE", "POLICE_SURVEILLANCE"],
        "default_vendor": "milestone"
    },
    # 6. Bhavnagar
    {
        "city": "Bhavnagar",
        "zone_name": "Bhavnagar Ghogha Circle & Port Area",
        "center_lat": 21.7645,
        "center_lon": 72.1519,
        "radius_spread": 0.020,
        "count": 45,
        "primary_depts": ["STATE_TRANSIT", "POLICE_SURVEILLANCE"],
        "default_vendor": "bosch"
    },
    # 7. Jamnagar
    {
        "city": "Jamnagar",
        "zone_name": "Jamnagar Digjam & Refinery Coastal Hub",
        "center_lat": 22.4707,
        "center_lon": 70.0577,
        "radius_spread": 0.025,
        "count": 50,
        "primary_depts": ["POLICE_SURVEILLANCE", "TRAFFIC_POLICE"],
        "default_vendor": "axis"
    }
]

# 30 Real Sentinel Sandbox Grid Live Streams (Rendered as White Markers)
SENTINEL_REAL_CAMERAS = [
    {"id": 1, "name": "Sentinel Live Feed #01 (Ashram Traffic Junction)", "lat": 23.0325, "lon": 72.5724, "city": "Ahmedabad", "codec": "H.264"},
    {"id": 2, "name": "Sentinel Live Feed #02 (SG Highway Iscon Cross)", "lat": 23.0285, "lon": 72.5080, "city": "Ahmedabad", "codec": "H.265"},
    {"id": 3, "name": "Sentinel Live Feed #03 (Kalupur Concourse Gate 1)", "lat": 23.0260, "lon": 72.6015, "city": "Ahmedabad", "codec": "H.264"},
    {"id": 4, "name": "Sentinel Live Feed #04 (Riverfront West Promenade)", "lat": 23.0390, "lon": 72.5700, "city": "Ahmedabad", "codec": "H.264"},
    {"id": 5, "name": "Sentinel Live Feed #05 (Kankaria Main Entry Gate)", "lat": 23.0070, "lon": 72.6035, "city": "Ahmedabad", "codec": "H.265"},
    {"id": 6, "name": "Sentinel Live Feed #06 (GIFT City Grand Central Gate)", "lat": 23.1610, "lon": 72.6850, "city": "Gandhinagar", "codec": "H.264"},
    {"id": 7, "name": "Sentinel Live Feed #07 (Infocity Tech Park Access)", "lat": 23.1920, "lon": 72.6280, "city": "Gandhinagar", "codec": "H.264"},
    {"id": 8, "name": "Sentinel Live Feed #08 (Gujarat Secretariat VIP Gate)", "lat": 23.2160, "lon": 72.6375, "city": "Gandhinagar", "codec": "H.265"},
    {"id": 9, "name": "Sentinel Live Feed #09 (Surat Textile Ring Road Flyover)", "lat": 21.1965, "lon": 72.8310, "city": "Surat", "codec": "H.264"},
    {"id": 10, "name": "Sentinel Live Feed #10 (Surat Dumas Seafront Concourse)", "lat": 21.0850, "lon": 72.7120, "city": "Surat", "codec": "H.264"},
    {"id": 11, "name": "Sentinel Live Feed #11 (Surat Railway Station Plaza)", "lat": 21.2050, "lon": 72.8410, "city": "Surat", "codec": "H.265"},
    {"id": 12, "name": "Sentinel Live Feed #12 (Vadodara Alkapuri Express Junction)", "lat": 22.3120, "lon": 73.1750, "city": "Vadodara", "codec": "H.264"},
    {"id": 13, "name": "Sentinel Live Feed #13 (Vadodara Sayaji Garden North)", "lat": 22.3150, "lon": 73.1900, "city": "Vadodara", "codec": "H.264"},
    {"id": 14, "name": "Sentinel Live Feed #14 (Vadodara Makarpura GIDC Toll)", "lat": 22.2510, "lon": 73.1950, "city": "Vadodara", "codec": "H.265"},
    {"id": 15, "name": "Sentinel Live Feed #15 (Rajkot Yagnik Road Center)", "lat": 22.3045, "lon": 70.8030, "city": "Rajkot", "codec": "H.264"},
    {"id": 16, "name": "Sentinel Live Feed #16 (Rajkot Kalawad Junction ANPR)", "lat": 22.2890, "lon": 70.7650, "city": "Rajkot", "codec": "H.264"},
    {"id": 17, "name": "Sentinel Live Feed #17 (Rajkot Aji GIDC Heavy Freight)", "lat": 22.2700, "lon": 70.8350, "city": "Rajkot", "codec": "H.265"},
    {"id": 18, "name": "Sentinel Live Feed #18 (Bhavnagar Ghogha Port Gate)", "lat": 21.7650, "lon": 72.1525, "city": "Bhavnagar", "codec": "H.264"},
    {"id": 19, "name": "Sentinel Live Feed #19 (Bhavnagar Victoria Park North)", "lat": 21.7450, "lon": 72.1380, "city": "Bhavnagar", "codec": "H.264"},
    {"id": 20, "name": "Sentinel Live Feed #20 (Jamnagar Digjam Circle West)", "lat": 22.4715, "lon": 70.0585, "city": "Jamnagar", "codec": "H.264"},
    {"id": 21, "name": "Sentinel Live Feed #21 (Jamnagar Reliance Highway Gate)", "lat": 22.4150, "lon": 69.9500, "city": "Jamnagar", "codec": "H.265"},
    {"id": 22, "name": "Sentinel Live Feed #22 (Ahmedabad Airport T2 Approach)", "lat": 23.0720, "lon": 72.6300, "city": "Ahmedabad", "codec": "H.264"},
    {"id": 23, "name": "Sentinel Live Feed #23 (Ahmedabad Vastrapur Lake Entry)", "lat": 23.0360, "lon": 72.5290, "city": "Ahmedabad", "codec": "H.264"},
    {"id": 24, "name": "Sentinel Live Feed #24 (Gandhinagar CH-3 Circle North)", "lat": 23.2300, "lon": 72.6500, "city": "Gandhinagar", "codec": "H.264"},
    {"id": 25, "name": "Sentinel Live Feed #25 (Surat Athwa Lines VIP Gate)", "lat": 21.1750, "lon": 72.8050, "city": "Surat", "codec": "H.265"},
    {"id": 26, "name": "Sentinel Live Feed #26 (Vadodara Mandvi Heritage Gate)", "lat": 22.3000, "lon": 73.2080, "city": "Vadodara", "codec": "H.264"},
    {"id": 27, "name": "Sentinel Live Feed #27 (Rajkot Race Course Ring PTZ)", "lat": 22.3080, "lon": 70.7950, "city": "Rajkot", "codec": "H.264"},
    {"id": 28, "name": "Sentinel Live Feed #28 (National Highway 48 Toll Plaza)", "lat": 21.5500, "lon": 72.9800, "city": "Inter-City", "codec": "H.265"},
    {"id": 29, "name": "Sentinel Live Feed #29 (Expressway Ahmedabad-Vadodara Entry)", "lat": 22.8500, "lon": 72.8200, "city": "Inter-City", "codec": "H.264"},
    {"id": 30, "name": "Sentinel Live Feed #30 (State Surveillance Control Grid)", "lat": 23.2200, "lon": 72.6450, "city": "Gandhinagar", "codec": "H.264"}
]

VMS_VENDORS = ["hikvision", "dahua", "milestone", "genetec", "bosch", "axis"]
PROTOCOLS = ["rtsp", "onvif", "webrtc", "http-flv"]
CAMERA_TYPES = ["fixed", "ptz", "number_plate", "thermal"]

def seed_database():
    db = SessionLocal()
    try:
        # 1. Roles
        roles_data = [
            ("super_admin", "Full system-wide access across all departments"),
            ("dept_admin", "Department-specific administrator"),
            ("dept_operator", "Department-specific operator"),
            ("auditor", "Read-only auditor with access to reports and audit logs")
        ]
        role_map = {}
        for r_name, r_desc in roles_data:
            role_obj = db.query(Role).filter(Role.name == r_name).first()
            if not role_obj:
                role_obj = Role(name=r_name, description=r_desc)
                db.add(role_obj)
                db.commit()
                db.refresh(role_obj)
            role_map[r_name] = role_obj

        # 2. Departments
        depts_data = [
            ("Traffic Police Department", "TRAFFIC_POLICE", "police", "Gujarat State Traffic Grid"),
            ("Municipal Corporation Smart City", "AMC_SMARTCITY", "municipal_corporation", "Municipal Urban Bodies"),
            ("State Transport & Transit Corp", "STATE_TRANSIT", "transport", "Gujarat State Highways & Metro"),
            ("State Police Surveillance", "POLICE_SURVEILLANCE", "police", "State Law & Order Grid"),
            ("Gandhinagar Urban Development Authority", "GUDA_GANDHINAGAR", "institution", "Gandhinagar Capital District")
        ]
        dept_map = {}
        for name, code, dtype, juris in depts_data:
            dept_obj = db.query(Department).filter(Department.code == code).first()
            if not dept_obj:
                dept_obj = Department(
                    name=name,
                    code=code,
                    department_type=dtype,
                    jurisdiction=juris,
                    is_active=True
                )
                db.add(dept_obj)
                db.commit()
                db.refresh(dept_obj)
            dept_map[code] = dept_obj

        # 3. Users
        users_data = [
            ("admin", "admin@cctv.gov.in", "State Surveillance Commissioner", None, "super_admin"),
            ("traffic_admin", "traffic.admin@cctv.gov.in", "ACP Traffic (Gujarat)", dept_map["TRAFFIC_POLICE"].department_id, "dept_admin"),
            ("amc_admin", "amc.admin@cctv.gov.in", "Chief City Engineer (Municipal)", dept_map["AMC_SMARTCITY"].department_id, "dept_admin"),
            ("police_admin", "police.admin@cctv.gov.in", "Superintendent of Police", dept_map["POLICE_SURVEILLANCE"].department_id, "dept_admin"),
            ("auditor_user", "auditor@cctv.gov.in", "State CAG Audit Officer", None, "auditor"),
        ]
        for username, email, full_name, dept_id, role_name in users_data:
            user_obj = db.query(User).filter(User.username == username).first()
            if not user_obj:
                user_obj = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    department_id=dept_id,
                    role_id=role_map[role_name].role_id,
                    password_hash=get_password_hash("Admin@123"),
                    is_active=True
                )
                db.add(user_obj)
        db.commit()

        # 4. First, Seed the 30 REAL Sentinel Sandbox Live Streams (Rendered White)
        print("🌱 Seeding 30 Real Sentinel Sandbox Grid Live Stream Cameras (White Markers)...")
        for s in SENTINEL_REAL_CAMERAS:
            s_id = s["id"]
            ext_ref = f"SENTINEL-LIVE-{s_id:02d}"
            dept = dept_map["POLICE_SURVEILLANCE"] if s_id % 2 == 0 else dept_map["TRAFFIC_POLICE"]

            existing = db.query(Camera).filter(Camera.external_reference == ext_ref).first()
            if not existing:
                cam_obj = Camera(
                    name=s["name"],
                    external_reference=ext_ref,
                    department_id=dept.department_id,
                    location=f"POINT({s['lon']} {s['lat']})",
                    address=f"Sentinel Sandbox Live Grid Pole #{s_id:02d}, {s['city']}, Gujarat",
                    manufacturer="Sentinel Grid Edge AI",
                    model="SENTINEL-NX4K",
                    serial_number=f"SN-SNTL-{1000 + s_id}",
                    camera_type="ptz" if s_id % 3 == 0 else "fixed",
                    ownership_type="department_owned",
                    access_class="government_internal",
                    connectivity_status="online",
                    operational_status="active",
                    installed_at=date(2023, 6, 1),
                    
                    vms_vendor_id="sentinel",
                    vms_stream_protocol="rtsp",
                    external_camera_id=str(s_id),
                    adapter_channel=f"sentinel-stream-{s_id:02d}",
                    coverage_radius_meters=100.0,
                    coverage_angle_degrees=180.0,
                    
                    attributes={
                        "is_sentinel_live": True,
                        "sentinel_id": s_id,
                        "sentinel_rtsp_url": f"rtsp://sentinel-grid.internal:8554/stream/{s_id}",
                        "sentinel_webrtc_url": f"http://sentinel-grid.internal:8889/stream/{s_id}/whep",
                        "sentinel_hls_url": f"http://sentinel-grid.internal/live/stream/{s_id}/index.m3u8",
                        "codec": s["codec"],
                        "city": s["city"],
                        "fps": 30,
                        "resolution": "4K Ultra-HD Stream",
                        "pts_sync_active": True
                    }
                )
                db.add(cam_obj)
        db.commit()

        # 5. Generate 600+ Realistic Statewide Cameras across 7 Gujarat Cities
        print("🌱 Seeding 600+ Statewide Cameras across Ahmedabad, Surat, Vadodara, Rajkot, Bhavnagar, Jamnagar...")
        random.seed(42)
        today = date.today()
        id_counter = 30

        for zone in STATEWIDE_CITY_ZONES:
            zone_count = zone["count"]
            for i in range(zone_count):
                id_counter += 1
                dept_code = random.choice(zone["primary_depts"])
                dept = dept_map[dept_code]

                lat = round(zone["center_lat"] + random.uniform(-zone["radius_spread"], zone["radius_spread"]), 6)
                lon = round(zone["center_lon"] + random.uniform(-zone["radius_spread"], zone["radius_spread"]), 6)

                age_years = random.choices([1, 2, 3, 4, 5, 6, 7, 8], weights=[15, 20, 25, 15, 10, 8, 5, 2])[0]
                installed_date = today - timedelta(days=int(age_years * 365.25 + random.randint(0, 180)))

                op_status = random.choices(["active", "maintenance", "retired"], weights=[88, 8, 4])[0]
                conn_status = "online" if op_status == "active" else "offline" if op_status == "retired" else "intermittent"

                cam_type = random.choices(CAMERA_TYPES, weights=[50, 25, 20, 5])[0]
                vendor = random.choices(VMS_VENDORS, weights=[35, 25, 15, 15, 5, 5])[0]
                protocol = random.choice(PROTOCOLS)

                ext_id = f"VMS-{vendor[:3].upper()}-{zone['city'][:3].upper()}-{id_counter:04d}"
                cam_name = f"{zone['city']} {cam_type.upper()} Pole #{i+1:02d}"

                existing = db.query(Camera).filter(Camera.external_reference == ext_id).first()
                if not existing:
                    cam_obj = Camera(
                        name=cam_name,
                        external_reference=ext_id,
                        department_id=dept.department_id,
                        location=f"POINT({lon} {lat})",
                        address=f"Pole #{i+1:02d}, {zone['zone_name']}, {zone['city']}, Gujarat",
                        manufacturer=vendor.capitalize(),
                        model=f"{vendor.upper()}-PRO-{random.randint(100, 999)}",
                        serial_number=f"SN-{vendor[:3].upper()}-{random.randint(100000, 999999)}",
                        camera_type=cam_type,
                        ownership_type="department_owned",
                        access_class="government_internal",
                        connectivity_status=conn_status,
                        operational_status=op_status,
                        installed_at=installed_date,
                        
                        vms_vendor_id=vendor,
                        vms_stream_protocol=protocol,
                        external_camera_id=ext_id,
                        adapter_channel=f"adapter-{vendor}-ch{random.randint(1, 16):02d}",
                        coverage_radius_meters=120.0 if cam_type == "ptz" else 60.0 if cam_type == "number_plate" else 75.0,
                        coverage_angle_degrees=360.0 if cam_type == "ptz" else 120.0,
                        
                        attributes={
                            "city": zone["city"],
                            "zone_cluster": zone["zone_name"],
                            "is_sentinel_live": False,
                            "amc_contract_active": age_years <= 5,
                            "resolution": "4K Ultra-HD" if age_years < 4 else "1080p Full-HD"
                        }
                    )
                    db.add(cam_obj)

        db.commit()
        print("✅ Successfully seeded 650+ Statewide Cameras across Gujarat & 30 Real Live Sentinel Streams!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
