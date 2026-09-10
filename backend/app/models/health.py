from sqlalchemy import Column, BigInteger, Text, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class CameraHealthSnapshot(Base):
    __tablename__ = "camera_health_snapshots"
    __table_args__ = {"schema": "registry"}

    snapshot_id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(BigInteger, ForeignKey("registry.cameras.camera_id", ondelete="CASCADE"), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    connectivity_status = Column(Text, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    packet_loss_percent = Column(Numeric(5, 2), nullable=True)
    source_system_id = Column(BigInteger, ForeignKey("registry.integration_systems.system_id", ondelete="SET NULL"), nullable=True)
    details = Column(JSONB, nullable=False, default=dict)

    camera = relationship("Camera", back_populates="health_snapshots")
