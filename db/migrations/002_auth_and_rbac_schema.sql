-- Migration: 002_auth_and_rbac_schema.sql
-- Adds department-wise Role-Based Access Control (RBAC) tables to the registry schema.

CREATE TABLE IF NOT EXISTS registry.roles (
    role_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE,
    description text,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Insert standard roles
INSERT INTO registry.roles (name, description) VALUES
    ('super_admin', 'Full system-wide access to all departments, cameras, settings, and audits'),
    ('dept_admin', 'Administrative access to manage cameras and users within their department'),
    ('dept_operator', 'Operator access to view, monitor, and update health/status within their department'),
    ('auditor', 'Read-only access to view logs, reports, gap analysis, and camera registries')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS registry.users (
    user_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE,
    email text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    full_name text NOT NULL,
    department_id bigint REFERENCES registry.departments(department_id) ON DELETE SET NULL,
    role_id bigint NOT NULL REFERENCES registry.roles(role_id),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT users_username_not_blank CHECK (btrim(username) <> ''),
    CONSTRAINT users_email_not_blank CHECK (btrim(email) <> '')
);

CREATE INDEX IF NOT EXISTS users_dept_idx ON registry.users (department_id);
CREATE INDEX IF NOT EXISTS users_role_idx ON registry.users (role_id);

CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON registry.users
FOR EACH ROW EXECUTE FUNCTION registry.set_updated_at();
