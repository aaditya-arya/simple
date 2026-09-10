from sqlalchemy import Column, BigInteger, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "registry"}

    audit_id = Column(BigInteger, primary_key=True, autoincrement=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actor_reference = Column(Text, nullable=True)
    action = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(BigInteger, nullable=True)
    request_reference = Column(Text, nullable=True)
    details = Column(JSONB, nullable=False, default=dict)
