# CCTV Central Registry & GIS Backend

Python (FastAPI) backend integrated with PostgreSQL and PostGIS to power the Central CCTV Registry, Onboarding pipeline, and React.js + Leaflet GIS Dashboards.

---

## 🏗️ Architecture & Data Flow

Following the end-to-end system flow:
1. **Department CCTV Assets**: Metadata, GPS coordinates (WGS84), and ownership attributes from various departments (Traffic Police, Municipal Corporations, Transit, Institutions).
2. **Onboarding & Validation Engine**: Validates inputs via Manual Entry form, Bulk File upload (CSV/Excel), or direct JSON API synchronization.
3. **Central Registry & Security**: Normalizes CCTV metadata, enforces department-scoped Role-Based Access Control (RBAC), and generates immutable audit trails in `registry.audit_log`.
4. **PostgreSQL + PostGIS**: Persists spatial coordinates (`geography(Point, 4326)`), GiST spatial indexes, time-series telemetry snapshots, and JSONB dynamic attributes.
5. **GIS Dashboard & APIs**: Serves RFC 7946 GeoJSON collections, spatial bounding-box viewports, proximity queries, health metrics, and gap analysis directly to the React.js + Leaflet frontend.

---

## 📁 Directory Structure & File Overview

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entry point, CORS middleware, route registration
│   ├── config.py                # Environment configurations (DATABASE_URL, JWT secret, CORS origins)
│   ├── database.py              # PostgreSQL/PostGIS connection engine and session dependency (get_db)
│   ├── models/
│   │   ├── __init__.py          # Model exports
│   │   ├── auth.py              # SQLAlchemy models: Department, Role, User
│   │   ├── camera.py            # SQLAlchemy models: Camera (PostGIS geography point), Storage, Sources, Bindings
│   │   ├── health.py            # SQLAlchemy model: CameraHealthSnapshot (telemetry history)
│   │   └── audit.py             # SQLAlchemy model: AuditLog (audit trail)
│   ├── schemas/
│   │   ├── __init__.py          # Pydantic schema exports
│   │   ├── auth.py              # Auth schemas: UserLogin, UserCreate, Token, UserResponse
│   │   ├── camera.py            # Camera schemas + RFC 7946 Leaflet GeoJSON FeatureCollection schemas
│   │   ├── onboarding.py        # Bulk CSV/Excel parsing and row-level error reporting schemas
│   │   ├── health.py            # Telemetry ingestion and system health summary schemas
│   │   └── analytics.py         # Gap Analysis & Ageing Infrastructure report schemas
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py          # Password hashing (bcrypt) and JWT encode/decode
│   │   └── rbac.py              # Department-scoped RBAC dependency injection (Super Admin vs Dept Admin/Operator)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_service.py     # Centralized audit logger function
│   │   ├── camera_service.py    # PostGIS spatial queries, bounding-box filters, GeoJSON builder
│   │   ├── onboarding_service.py# CSV/Excel parsing, row validation, coordinate bounding checks
│   │   └── analytics_service.py # Spatial coverage gap computation and hardware ageing categorization
│   └── routers/
│       ├── __init__.py
│       ├── auth.py              # /api/v1/auth - Login, Token, Users, Roles, Departments
│       ├── cameras.py           # /api/v1/cameras - Search, filter, CRUD, CSV Export
│       ├── onboarding.py        # /api/v1/onboarding - Manual entry, Bulk CSV/Excel, API batch
│       ├── gis.py               # /api/v1/gis - Leaflet GeoJSON, Bounding-box (bbox), Proximity (nearby)
│       ├── health.py            # /api/v1/health - Telemetry ingestion, health snapshots, uptime SLAs
│       └── analytics.py         # /api/v1/analytics - Ageing assets report & spatial gap analysis
├── seed_data.py                 # Seeds roles, departments, test users, and sample GIS cameras
├── requirements.txt             # Python dependencies
└── README.md                    # Backend documentation
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.10+
- PostgreSQL 14+ with PostGIS 3+

### 2. Setup Database
Apply the SQL migrations located in `db/migrations/`:
```bash
psql "$DATABASE_URL" -f db/migrations/001_universal_camera_schema.sql
psql "$DATABASE_URL" -f db/migrations/002_auth_and_rbac_schema.sql
```

### 3. Install Python Dependencies
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure Environment Variables
Set your database connection:
```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/cctv_registry_db"
$env:SECRET_KEY="your-secret-key-for-jwt"

# Linux / macOS
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/cctv_registry_db"
export SECRET_KEY="your-secret-key-for-jwt"
```

### 5. Seed Initial Data
```bash
python seed_data.py
```
Default accounts created:
- `admin` (super_admin) / `Admin@123`
- `traffic_admin` (dept_admin - Traffic Police) / `Admin@123`
- `amc_admin` (dept_admin - Municipal Corp) / `Admin@123`
- `auditor_user` (auditor) / `Admin@123`

### 6. Run the API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8005
```
Interactive Swagger API docs will be available at: **`http://localhost:8005/docs`**

---

## 🗺️ React.js & Leaflet GIS Integration Example

To render cameras on a Leaflet map in React:

```jsx
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export function CCTVMap() {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8005/api/v1/gis/geojson', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => res.json())
      .then(data => setGeoData(data));
  }, []);

  const pointToLayer = (feature, latlng) => {
    // Green for online, Red for offline
    const isOnline = feature.properties.connectivity_status === 'online';
    return L.circleMarker(latlng, {
      radius: 8,
      fillColor: isOnline ? '#10B981' : '#EF4444',
      color: '#fff',
      weight: 2,
      fillOpacity: 0.9
    });
  };

  const onEachFeature = (feature, layer) => {
    layer.bindPopup(`
      <strong>${feature.properties.name}</strong><br/>
      Department: ${feature.properties.department_name}<br/>
      Status: ${feature.properties.connectivity_status}<br/>
      Type: ${feature.properties.camera_type}
    `);
  };

  return (
    <MapContainer center={[23.0225, 72.5714]} zoom={12} style={{ height: '100vh', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {geoData && (
        <GeoJSON
          data={geoData}
          pointToLayer={pointToLayer}
          onEachFeature={onEachFeature}
        />
      )}
    </MapContainer>
  );
}
```
