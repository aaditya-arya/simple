from datetime import datetime
from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "registry"}

    department_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False, unique=True)
    department_type = Column(Text, nullable=False, default="other")
    jurisdiction = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    cameras = relationship("Camera", back_populates="department")
    users = relationship("User", back_populates="department")


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "registry"}

    role_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "registry"}

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)
    department_id = Column(BigInteger, ForeignKey("registry.departments.department_id", ondelete="SET NULL"), nullable=True)
    role_id = Column(BigInteger, ForeignKey("registry.roles.role_id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="users")
    role = relationship("Role", back_populates="users")
