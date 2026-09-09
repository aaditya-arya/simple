-- Universal CCTV registry schema.
-- Requires PostgreSQL 14+ and PostGIS 3+.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS registry;

CREATE TABLE registry.departments (
    department_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    code text NOT NULL,
    department_type text NOT NULL DEFAULT 'other',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT departments_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT departments_code_not_blank CHECK (btrim(code) <> ''),
    CONSTRAINT departments_code_unique UNIQUE (code),
    CONSTRAINT departments_type_check CHECK (
        department_type IN ('municipal_corporation', 'transport', 'police', 'institution', 'other')
    )
);

CREATE TABLE registry.cameras (
    camera_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_reference text,
    name text NOT NULL,
    department_id bigint NOT NULL REFERENCES registry.departments(department_id),
    location geography(Point, 4326) NOT NULL,
    address text,
    camera_type text NOT NULL DEFAULT 'unknown',
    ownership_type text NOT NULL DEFAULT 'department_owned',
    connectivity_status text NOT NULL DEFAULT 'unknown',
    operational_status text NOT NULL DEFAULT 'unknown',
    installed_at date,
    last_seen_at timestamptz,
    notes text,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT cameras_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT cameras_external_reference_unique UNIQUE (department_id, external_reference),
    CONSTRAINT cameras_type_check CHECK (
        camera_type IN ('fixed', 'ptz', 'thermal', 'number_plate', 'body_worn', 'mobile', 'unknown')
    ),
    CONSTRAINT cameras_ownership_check CHECK (
        ownership_type IN ('department_owned', 'shared', 'private_contractor', 'other')
    ),
    CONSTRAINT cameras_connectivity_check CHECK (
        connectivity_status IN ('online', 'offline', 'intermittent', 'unknown')
    ),
    CONSTRAINT cameras_operational_check CHECK (
        operational_status IN ('active', 'maintenance', 'retired', 'planned', 'unknown')
    )
);

CREATE TABLE registry.camera_storage_locations (
    storage_location_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    storage_type text NOT NULL,
    label text NOT NULL,
    provider text,
    endpoint text,
    bucket_or_path text,
    retention_days integer,
    is_primary boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT storage_label_not_blank CHECK (btrim(label) <> ''),
    CONSTRAINT storage_type_check CHECK (
        storage_type IN ('local_nvr', 'local_dvr', 'edge_device', 'cloud', 'hybrid', 'unknown')
    ),
    CONSTRAINT storage_retention_check CHECK (
        retention_days IS NULL OR retention_days >= 0
    )
);

CREATE UNIQUE INDEX camera_one_primary_storage
    ON registry.camera_storage_locations (camera_id)
    WHERE is_primary;

CREATE TABLE registry.camera_sources (
    source_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    source_type text NOT NULL,
    protocol text,
    stream_reference text,
    is_primary boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT source_type_check CHECK (
        source_type IN ('rtsp', 'onvif', 'http', 'vendor_api', 'file_export', 'unknown')
    )
);

CREATE UNIQUE INDEX camera_one_primary_source
    ON registry.camera_sources (camera_id)
    WHERE is_primary;

CREATE INDEX cameras_location_gist
    ON registry.cameras USING gist (location);

CREATE INDEX cameras_department_status_idx
    ON registry.cameras (department_id, operational_status, connectivity_status);

CREATE INDEX cameras_attributes_gin
    ON registry.cameras USING gin (attributes);

CREATE INDEX storage_camera_idx
    ON registry.camera_storage_locations (camera_id, is_active);

CREATE INDEX sources_camera_idx
    ON registry.camera_sources (camera_id, is_active);

CREATE OR REPLACE FUNCTION registry.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER cameras_set_updated_at
BEFORE UPDATE ON registry.cameras
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();

CREATE TRIGGER storage_set_updated_at
BEFORE UPDATE ON registry.camera_storage_locations
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();