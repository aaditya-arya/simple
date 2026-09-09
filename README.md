# CCTV Registry: Step 1

This repository starts with the universal database schema for a centralized CCTV metadata registry. It stores metadata and infrastructure references only; it does not store or stream video.

## Requirements

- PostgreSQL 14 or newer
- PostGIS 3 or newer

## Apply the schema

```bash
psql "$DATABASE_URL" -f db/migrations/001_universal_camera_schema.sql
```

The schema is contained in the `registry` schema so it can coexist with other database objects.

## Model

- `departments` identifies the department or institution responsible for a camera.
- `cameras` contains the stable, queryable camera metadata and a PostGIS point in WGS 84.
- `camera_storage_locations` supports one or more local, cloud, edge, or hybrid storage locations per camera. `retention_days` is nullable for unknown retention and accepts values such as 7, 15, or more.
- `camera_sources` records future integration references such as RTSP, ONVIF, or a vendor API. It contains no credentials.
- `attributes` and `details` hold provider-specific fields without changing the core schema for every department.

The two partial unique indexes enforce at most one primary storage location and one primary source per camera. The GIS and JSONB indexes cover the first map, filtering, and metadata-search use cases.

## Deliberate boundaries

- No live video, recordings, passwords, or secrets are stored.
- Retention is represented as data, not as a fixed 7/15-day rule.
- Controlled fields use checks for predictable filtering, while provider-specific camera and infrastructure variations use JSONB.