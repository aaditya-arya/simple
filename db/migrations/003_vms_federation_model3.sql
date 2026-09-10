-- Migration: 003_vms_federation_model3.sql
-- Hardens schema for Model 3 (VMS Federation & Middleware Integration)
-- Adds first-class VMS connector primitives, stream protocols, adapter channels, and spatial coverage properties.

ALTER TABLE registry.cameras
    ADD COLUMN IF NOT EXISTS vms_vendor_id text DEFAULT 'hikvision',
    ADD COLUMN IF NOT EXISTS vms_stream_protocol text DEFAULT 'rtsp',
    ADD COLUMN IF NOT EXISTS external_camera_id text,
    ADD COLUMN IF NOT EXISTS adapter_channel text,
    ADD COLUMN IF NOT EXISTS coverage_radius_meters numeric(6, 2) DEFAULT 75.0,
    ADD COLUMN IF NOT EXISTS coverage_angle_degrees numeric(5, 2) DEFAULT 120.0;

-- Indexes for high-speed federation routing and adapter lookups
CREATE INDEX IF NOT EXISTS cameras_vms_vendor_idx ON registry.cameras (vms_vendor_id);
CREATE INDEX IF NOT EXISTS cameras_adapter_channel_idx ON registry.cameras (adapter_channel);
CREATE INDEX IF NOT EXISTS cameras_vms_ext_id_idx ON registry.cameras (vms_vendor_id, external_camera_id);

-- Create a dedicated table for Model 3 Middleware Events (Event & Metadata Bus)
CREATE TABLE IF NOT EXISTS registry.vms_middleware_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    camera_id bigint REFERENCES registry.cameras(camera_id) ON DELETE CASCADE,
    vms_vendor_id text NOT NULL,
    external_camera_id text,
    event_type text NOT NULL, -- 'status_change', 'motion_detected', 'tamper_alarm', 'anpr_hit', 'crowd_anomaly'
    severity text NOT NULL DEFAULT 'medium',
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    received_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS vms_events_cam_time_idx ON registry.vms_middleware_events (camera_id, received_at DESC);
CREATE INDEX IF NOT EXISTS vms_events_vendor_time_idx ON registry.vms_middleware_events (vms_vendor_id, received_at DESC);
