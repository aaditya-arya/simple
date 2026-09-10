from sqlalchemy import (
    Column, BigInteger, Text, Boolean, Integer, Numeric, Date, DateTime, 
    ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from app.database import Base

class Camera(Base):
    __tablename__ = "cameras"
    __table_args__ = (
        UniqueConstraint("department_id", "external_reference", name="cameras_external_reference_unique"),
        {"schema": "registry"}
    )

    camera_id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_reference = Column(Text, nullable=True)
    name = Column(Text, nullable=False)
    department_id = Column(BigInteger, ForeignKey("registry.departments.department_id"), nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False)
    address = Column(Text, nullable=True)
    manufacturer = Column(Text, nullable=True)
    model = Column(Text, nullable=True)
    serial_number = Column(Text, nullable=True)
    camera_type = Column(Text, nullable=False, default="fixed")
    ownership_type = Column(Text, nullable=False, default="department_owned")
    access_class = Column(Text, nullable=False, default="restricted")
    connectivity_status = Column(Text, nullable=False, default="unknown")
    operational_status = Column(Text, nullable=False, default="active")
    installed_at = Column(Date, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    attributes = Column(JSONB, nullable=False, default=dict)
    
    # Model 3 VMS Federation & Middleware Integration Primitives
    vms_vendor_id = Column(Text, nullable=False, default="hikvision")
    vms_stream_protocol = Column(Text, nullable=False, default="rtsp")
    external_camera_id = Column(Text, nullable=True)
    adapter_channel = Column(Text, nullable=True)
    coverage_radius_meters = Column(Numeric(6, 2), nullable=False, default=75.0)
    coverage_angle_degrees = Column(Numeric(5, 2), nullable=False, default=120.0)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="cameras")
    storage_locations = relationship("CameraStorageLocation", back_populates="camera", cascade="all, delete-orphan")
    sources = relationship("CameraSource", back_populates="camera", cascade="all, delete-orphan")
    bindings = relationship("CameraIntegrationBinding", back_populates="camera", cascade="all, delete-orphan")
    health_snapshots = relationship("CameraHealthSnapshot", back_populates="camera", cascade="all, delete-orphan")
    middleware_events = relationship("VMSMiddlewareEvent", back_populates="camera", cascade="all, delete-orphan")


class VMSMiddlewareEvent(Base):
    __tablename__ = "vms_middleware_events"
    __table_args__ = {"schema": "registry"}

    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(BigInteger, ForeignKey("registry.cameras.camera_id", ondelete="CASCADE"), nullable=True)
    vms_vendor_id = Column(Text, nullable=False)
    external_camera_id = Column(Text, nullable=True)
    event_type = Column(Text, nullable=False)
    severity = Column(Text, nullable=False, default="medium")
    payload = Column(JSONB, nullable=False, default=dict)
    received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    camera = relationship("Camera", back_populates="middleware_events")


class CameraStorageLocation(Base):
    __tablename__ = "camera_storage_locations"
    __table_args__ = {"schema": "registry"}

    storage_location_id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(BigInteger, ForeignKey("registry.cameras.camera_id", ondelete="CASCADE"), nullable=False)
    storage_type = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    provider = Column(Text, nullable=True)
    endpoint = Column(Text, nullable=True)
    bucket_or_path = Column(Text, nullable=True)
    retention_days = Column(Integer, nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    details = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    camera = relationship("Camera", back_populates="storage_locations")


class CameraSource(Base):
    __tablename__ = "camera_sources"
    __table_args__ = {"schema": "registry"}

    source_id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(BigInteger, ForeignKey("registry.cameras.camera_id", ondelete="CASCADE"), nullable=False)
    source_type = Column(Text, nullable=False)
    protocol = Column(Text, nullable=True)
    stream_reference = Column(Text, nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    details = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    camera = relationship("Camera", back_populates="sources")


class IntegrationSystem(Base):
    __tablename__ = "integration_systems"
    __table_args__ = {"schema": "registry"}

    system_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    system_type = Column(Text, nullable=False)
    owner_department_id = Column(BigInteger, ForeignKey("registry.departments.department_id"), nullable=True)
    base_url = Column(Text, nullable=True)
    credential_reference = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    capabilities = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    bindings = relationship("CameraIntegrationBinding", back_populates="system")


class CameraIntegrationBinding(Base):
    __tablename__ = "camera_integration_bindings"
    __table_args__ = (
        UniqueConstraint("system_id", "external_camera_reference", name="camera_system_reference_unique"),
        {"schema": "registry"}
    )

    binding_id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(BigInteger, ForeignKey("registry.cameras.camera_id", ondelete="CASCADE"), nullable=False)
    system_id = Column(BigInteger, ForeignKey("registry.integration_systems.system_id", ondelete="CASCADE"), nullable=False)
    external_camera_reference = Column(Text, nullable=False)
    binding_status = Column(Text, nullable=False, default="active")
    last_synchronised_at = Column(DateTime(timezone=True), nullable=True)
    details = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    camera = relationship("Camera", back_populates="bindings")
    system = relationship("IntegrationSystem", back_populates="bindings")
