# CCTV Registry: Foundation

This repository contains the full end-to-end platform for the Centralized Gujarat CCTV Registry & AI Video Analytics Platform (Model 1 + Model 3 VMS Federation).

---

## ⚡ Quick Start (1-Click Unified Launcher)

To launch the entire platform (MediaMTX RTSP Server + Continuous Video Publisher + FastAPI YOLOv8 AI Backend + React GIS Leaflet Frontend) in a single command:

```powershell
# Method 1: Double-click or run batch script
.\run_all.bat

# Method 2: Run python orchestrator directly
python run_all.py
```

- **Dashboard UI**: `http://localhost:5180` (opens automatically in browser)
- **FastAPI Docs**: `http://localhost:8005/docs`
- **RTSP Stream**: `rtsp://127.0.0.1:8554/stream/1`
- **HLS Web Stream**: `http://127.0.0.1:8888/stream/1/index.m3u8`
- **WebSocket AI Stream**: `ws://127.0.0.1:8005/api/v1/ws/inference/{camera_id}`
- **Verification Suite**: `.\verify_pipeline.bat` (validates RTSP ingestion & YOLOv8 bounding boxes)
- **Stop All Services**: Press `Ctrl+C` in the launcher terminal or run `.\stop_all.bat`

---

## Requirements

- PostgreSQL 14 or newer
- PostGIS 3 or newer

## Apply the schema

```bash
psql "$DATABASE_URL" -f db/migrations/001_universal_camera_schema.sql
```

For Neon, the connection string only tells the application where the database is. Neon does not read files from this repository automatically. Apply each migration in order by either pasting the contents of `001_universal_camera_schema.sql`, `002_auth_and_rbac_schema.sql`, and `003_vms_federation_model3.sql` into the Neon SQL Editor and running them one at a time, or by running the `psql` commands above from a machine with the PostgreSQL client installed.

After the migrations finish, verify the database before seeding:

```sql
SELECT PostGIS_Version();
SELECT to_regclass('registry.cameras');
SELECT to_regclass('registry.users');
```

Only after those checks succeed should you run `python seed_data.py`. The seed script connects to the database named in `DATABASE_URL`; it does not create the tables or upload migration files.

The schema is contained in the `registry` schema so it can coexist with other database objects.

## Model

- `departments` identifies the department or institution responsible for a camera.
- `cameras` contains the stable, queryable camera metadata and a PostGIS point in WGS 84.
- `camera_storage_locations` supports one or more local, cloud, edge, or hybrid storage locations per camera. `retention_days` is nullable for unknown retention and accepts values such as 7, 15, or more.
- `camera_sources` records integration references such as RTSP, ONVIF, or a vendor API. It contains no credentials.
- `integration_systems` registers systems such as VAHAN, SARTHI, eGujCop, AFIS, NAFIS, VMS platforms, and analytics services. `credential_reference` points to an external secrets manager; secrets are never stored here.
- `camera_integration_bindings` maps a local camera to its identifier in a department VMS or external system.
- `analytics_rules` and `camera_analytics_rules` define reusable detection rules and their camera assignments.
- `video_events` stores searchable analytics events, including event time, camera, object reference, confidence, and optional GIS location. `event_observations` stores time-series points for vehicle or person movement history.
- `alerts` stores the operational lifecycle of an event requiring attention: open, acknowledged, resolved, or dismissed.
- `camera_health_snapshots` stores connectivity and quality telemetry for dashboards and SLA reporting.
- `audit_log` provides an append-only application audit target for access, configuration, and integration actions.
- `attributes` and `details` hold provider-specific fields without changing the core schema for every department.

The two partial unique indexes enforce at most one primary storage location and one primary source per camera. The GIS and JSONB indexes cover the first map, filtering, and metadata-search use cases.

## Deliberate boundaries

- No live video, recordings, passwords, or secrets are stored.
- Retention is represented as data, not as a fixed 7/15-day rule.
- Controlled fields use checks for predictable filtering, while provider-specific camera and infrastructure variations use JSONB.

## Platform boundaries

This schema is suitable as the registry and operational metadata layer for all four proposed models. It is not a replacement for:

- A VMS or media gateway for RTSP, ONVIF, recording, transcoding, and federation.
- Object or archive storage for video evidence and retention enforcement.
- A message broker for reliable feed, event, and alert delivery between districts and the state platform.
- An analytics service or GPU platform for detection, license plate recognition, re-identification, and tracking.
- An API and identity layer for RBAC, department tenancy, consent, rate limiting, and secure access to VAHAN, SARTHI, eGujCop, AFIS, and NAFIS.

For the initial approximately 50-camera PoC, this schema supports live-feed metadata, GIS visualization, event history, movement observations, alert workflows, and integration mappings. At statewide scale, partition `video_events`, `event_observations`, `camera_health_snapshots`, and `audit_log` by time, archive old event data, and use a queue-backed ingestion service rather than writing directly from every camera or analytics process.

The migration is a baseline and is intended to run once through a migration tool or `psql`; it is not designed to be safely executed repeatedly.