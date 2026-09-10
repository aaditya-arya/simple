from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.auth import User, Role, Department
from app.schemas.auth import (
    UserLogin, UserCreate, UserResponse, Token,
    DepartmentResponse, RoleResponse
)
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.rbac import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login for Swagger UI and client authentication."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    role_name = user.role.name if user.role else "dept_operator"
    token_claims = {
        "user_id": user.user_id,
        "role_name": role_name,
        "department_id": user.department_id
    }
    access_token = create_access_token(subject=user.username, claims=token_claims)

    user_resp = UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role_name=role_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

    return Token(access_token=access_token, token_type="bearer", user=user_resp)


@router.post("/login", response_model=Token)
def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """JSON body login endpoint for React.js frontend."""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")

    role_name = user.role.name if user.role else "dept_operator"
    token_claims = {
        "user_id": user.user_id,
        "role_name": role_name,
        "department_id": user.department_id
    }
    access_token = create_access_token(subject=user.username, claims=token_claims)

    user_resp = UserResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        department_name=user.department.name if user.department else None,
        role_name=role_name,
        is_active=user.is_active,
        created_at=user.created_at
    )

    return Token(access_token=access_token, token_type="bearer", user=user_resp)


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Retrieve logged in user profile with role and department tenancy."""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        department_id=current_user.department_id,
        department_name=current_user.department.name if current_user.department else None,
        role_name=current_user.role.name if current_user.role else "unknown",
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/users", response_model=UserResponse)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin", "dept_admin"]))
):
    """Create a new user with department assignment and role assignment."""
    if current_user.role.name == "dept_admin":
        if user_in.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department Admin can only create users within their own department"
            )

    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    role = db.query(Role).filter(Role.role_id == user_in.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        department_id=user_in.department_id,
        role_id=user_in.role_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        user_id=new_user.user_id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        department_id=new_user.department_id,
        department_name=new_user.department.name if new_user.department else None,
        role_name=role.name,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered departments."""
    return db.query(Department).filter(Department.is_active == True).all()


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["super_admin"]))
):
    """List all RBAC system roles."""
    return db.query(Role).all()
