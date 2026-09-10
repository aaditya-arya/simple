-- Universal CCTV registry schema.
-- Requires PostgreSQL 14+ and PostGIS 3+.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS registry;

CREATE TABLE registry.departments (
    department_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    code text NOT NULL,
    department_type text NOT NULL DEFAULT 'other',
    jurisdiction text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT departments_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT departments_code_not_blank CHECK (btrim(code) <> ''),
    CONSTRAINT departments_jurisdiction_not_blank CHECK (
        jurisdiction IS NULL OR btrim(jurisdiction) <> ''
    ),
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
    manufacturer text,
    model text,
    serial_number text,
    camera_type text NOT NULL DEFAULT 'unknown',
    ownership_type text NOT NULL DEFAULT 'department_owned',
    access_class text NOT NULL DEFAULT 'restricted',
    connectivity_status text NOT NULL DEFAULT 'unknown',
    operational_status text NOT NULL DEFAULT 'unknown',
    installed_at date,
    last_seen_at timestamptz,
    notes text,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT cameras_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT cameras_manufacturer_not_blank CHECK (
        manufacturer IS NULL OR btrim(manufacturer) <> ''
    ),
    CONSTRAINT cameras_model_not_blank CHECK (
        model IS NULL OR btrim(model) <> ''
    ),
    CONSTRAINT cameras_serial_not_blank CHECK (
        serial_number IS NULL OR btrim(serial_number) <> ''
    ),
    CONSTRAINT cameras_external_reference_unique UNIQUE (department_id, external_reference),
    CONSTRAINT cameras_type_check CHECK (
        camera_type IN ('fixed', 'ptz', 'thermal', 'number_plate', 'body_worn', 'mobile', 'unknown')
    ),
    CONSTRAINT cameras_ownership_check CHECK (
        ownership_type IN ('department_owned', 'shared', 'private_contractor', 'other')
    ),
    CONSTRAINT cameras_access_class_check CHECK (
        access_class IN ('government_internal', 'government_public', 'partner_shared', 'restricted')
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
    ),
    CONSTRAINT storage_endpoint_not_blank CHECK (
        endpoint IS NULL OR btrim(endpoint) <> ''
    ),
    CONSTRAINT storage_bucket_not_blank CHECK (
        bucket_or_path IS NULL OR btrim(bucket_or_path) <> ''
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
    ),
    CONSTRAINT source_protocol_not_blank CHECK (
        protocol IS NULL OR btrim(protocol) <> ''
    ),
    CONSTRAINT source_reference_not_blank CHECK (
        stream_reference IS NULL OR btrim(stream_reference) <> ''
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

CREATE TABLE registry.integration_systems (
    system_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    system_type text NOT NULL,
    owner_department_id bigint REFERENCES registry.departments(department_id),
    base_url text,
    credential_reference text,
    is_active boolean NOT NULL DEFAULT true,
    capabilities jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT integration_systems_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT integration_systems_type_check CHECK (
        system_type IN ('vahan', 'sarthi', 'egujcop', 'afis', 'nafis', 'vms', 'analytics', 'other')
    ),
    CONSTRAINT integration_systems_url_not_blank CHECK (
        base_url IS NULL OR btrim(base_url) <> ''
    ),
    CONSTRAINT integration_systems_credential_ref_not_blank CHECK (
        credential_reference IS NULL OR btrim(credential_reference) <> ''
    )
);

CREATE TABLE registry.camera_integration_bindings (
    binding_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    system_id bigint NOT NULL REFERENCES registry.integration_systems(system_id) ON DELETE CASCADE,
    external_camera_reference text NOT NULL,
    binding_status text NOT NULL DEFAULT 'active',
    last_synchronised_at timestamptz,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT binding_reference_not_blank CHECK (btrim(external_camera_reference) <> ''),
    CONSTRAINT binding_status_check CHECK (
        binding_status IN ('active', 'paused', 'failed', 'retired')
    ),
    CONSTRAINT camera_system_reference_unique UNIQUE (system_id, external_camera_reference)
);

CREATE TABLE registry.analytics_rules (
    rule_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    rule_type text NOT NULL,
    description text,
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    severity text NOT NULL DEFAULT 'medium',
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT analytics_rules_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT analytics_rules_severity_check CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    )
);

CREATE TABLE registry.camera_analytics_rules (
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    rule_id bigint NOT NULL REFERENCES registry.analytics_rules(rule_id) ON DELETE CASCADE,
    enabled_at timestamptz NOT NULL DEFAULT now(),
    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (camera_id, rule_id)
);

CREATE TABLE registry.video_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE RESTRICT,
    rule_id bigint REFERENCES registry.analytics_rules(rule_id) ON DELETE SET NULL,
    source_system_id bigint REFERENCES registry.integration_systems(system_id) ON DELETE SET NULL,
    event_type text NOT NULL,
    severity text NOT NULL DEFAULT 'medium',
    occurred_at timestamptz NOT NULL,
    ended_at timestamptz,
    track_reference text,
    object_type text,
    object_reference text,
    location geography(Point, 4326),
    confidence numeric(5, 4),
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT video_events_type_not_blank CHECK (btrim(event_type) <> ''),
    CONSTRAINT video_events_severity_check CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT video_events_time_check CHECK (
        ended_at IS NULL OR ended_at >= occurred_at
    ),
    CONSTRAINT video_events_confidence_check CHECK (
        confidence IS NULL OR confidence BETWEEN 0 AND 1
    ),
    CONSTRAINT video_events_track_not_blank CHECK (
        track_reference IS NULL OR btrim(track_reference) <> ''
    ),
    CONSTRAINT video_events_object_reference_not_blank CHECK (
        object_reference IS NULL OR btrim(object_reference) <> ''
    )
);

CREATE TABLE registry.event_observations (
    observation_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id bigint NOT NULL REFERENCES registry.video_events(event_id) ON DELETE CASCADE,
    observed_at timestamptz NOT NULL,
    location geography(Point, 4326),
    object_type text,
    object_reference text,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT observation_object_reference_not_blank CHECK (
        object_reference IS NULL OR btrim(object_reference) <> ''
    )
);

CREATE TABLE registry.alerts (
    alert_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id bigint REFERENCES registry.video_events(event_id) ON DELETE SET NULL,
    rule_id bigint REFERENCES registry.analytics_rules(rule_id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'open',
    priority text NOT NULL DEFAULT 'medium',
    assigned_to text,
    opened_at timestamptz NOT NULL DEFAULT now(),
    acknowledged_at timestamptz,
    resolved_at timestamptz,
    resolution_notes text,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT alerts_status_check CHECK (
        status IN ('open', 'acknowledged', 'resolved', 'dismissed')
    ),
    CONSTRAINT alerts_priority_check CHECK (
        priority IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT alerts_resolution_time_check CHECK (
        resolved_at IS NULL OR resolved_at >= opened_at
    )
);

CREATE TABLE registry.camera_health_snapshots (
    snapshot_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint NOT NULL REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    observed_at timestamptz NOT NULL DEFAULT now(),
    connectivity_status text NOT NULL,
    latency_ms integer,
    packet_loss_percent numeric(5, 2),
    source_system_id bigint REFERENCES registry.integration_systems(system_id) ON DELETE SET NULL,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT health_status_check CHECK (
        connectivity_status IN ('online', 'offline', 'intermittent', 'unknown')
    ),
    CONSTRAINT health_latency_check CHECK (latency_ms IS NULL OR latency_ms >= 0),
    CONSTRAINT health_packet_loss_check CHECK (
        packet_loss_percent IS NULL OR packet_loss_percent BETWEEN 0 AND 100
    )
);

CREATE TABLE registry.audit_log (
    audit_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    actor_reference text,
    action text NOT NULL,
    entity_type text NOT NULL,
    entity_id bigint,
    request_reference text,
    details jsonb NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT audit_action_not_blank CHECK (btrim(action) <> ''),
    CONSTRAINT audit_entity_type_not_blank CHECK (btrim(entity_type) <> '')
);

CREATE INDEX camera_bindings_camera_idx
    ON registry.camera_integration_bindings (camera_id, binding_status);

CREATE INDEX video_events_camera_time_idx
    ON registry.video_events (camera_id, occurred_at DESC);

CREATE INDEX video_events_object_time_idx
    ON registry.video_events (object_type, object_reference, occurred_at DESC);

CREATE INDEX video_events_location_gist
    ON registry.video_events USING gist (location);

CREATE INDEX event_observations_event_time_idx
    ON registry.event_observations (event_id, observed_at);

CREATE INDEX alerts_status_priority_idx
    ON registry.alerts (status, priority, opened_at DESC);

CREATE INDEX camera_health_camera_time_idx
    ON registry.camera_health_snapshots (camera_id, observed_at DESC);

CREATE INDEX audit_log_entity_idx
    ON registry.audit_log (entity_type, entity_id, occurred_at DESC);

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

CREATE TRIGGER integration_systems_set_updated_at
BEFORE UPDATE ON registry.integration_systems
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();

CREATE TRIGGER camera_bindings_set_updated_at
BEFORE UPDATE ON registry.camera_integration_bindings
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();

CREATE TRIGGER analytics_rules_set_updated_at
BEFORE UPDATE ON registry.analytics_rules
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();