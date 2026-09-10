from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    code: str
    department_type: str = "other"
    jurisdiction: Optional[str] = None
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    department_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    role_id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    department_id: Optional[int] = None
    role_id: int


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    full_name: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    role_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenPayload(BaseModel):
    sub: str  # username
    user_id: int
    role_name: str
    department_id: Optional[int] = None
