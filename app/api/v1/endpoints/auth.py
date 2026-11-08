from datetime import datetime, timedelta, timezone
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, require_roles
from app.core.security import (
    create_access_token,
    generate_session_token,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.auth_model import User, UserRole, UserSession
from app.schemas.auth_schema import (
    AdminPasswordResetRequest,
    AdminUserCreateRequest,
    PasswordResetPendingResponse,
    PasswordResetSubmitRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticates users, initializes a persistent session, and issues a Bearer JWT."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact Admin.",
        )

    # Register active session
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    user_session = UserSession(
        user_id=user.id,
        session_token=generate_session_token(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=expires_at,
    )
    db.add(user_session)
    await db.flush()

    token = create_access_token(
        subject=str(user.id),
        session_id=str(user_session.id),
        role=user.role.value,
    )
    await db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Returns the profile and RBAC role of the authenticated user."""
    return current_user


@router.post("/request-password-reset")
async def request_password_reset(
    payload: PasswordResetSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Users submit a request to the Admin for a password reset."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        # Prevent user enumeration
        return {
            "message": "If the account exists, the reset request has been logged for Admin review."
        }

    user.password_reset_pending = True
    user.reset_request_note = payload.note or "Password reset requested by user."
    await db.commit()
    return {
        "message": "Reset request submitted successfully. Please contact your Admin to obtain your new password."
    }


# ==========================================
# ADMIN-ONLY PROVISIONING & CREDENTIALS
# ==========================================

@router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def admin_create_user(
    payload: AdminUserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin provisions an account, assigns an RBAC role, and sets the initial password."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    new_user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.get(
    "/admin/password-resets",
    response_model=list[PasswordResetPendingResponse],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def list_pending_password_resets(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin inspects all users currently awaiting a password reset."""
    result = await db.execute(
        select(User).where(User.password_reset_pending.is_(True))
    )
    return result.scalars().all()


@router.post(
    "/admin/users/{user_id}/reset-password",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def admin_reset_user_password(
    user_id: uuid.UUID,
    payload: AdminPasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin assigns a new password and revokes any open sessions."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    user.hashed_password = get_password_hash(payload.new_password)
    user.password_reset_pending = False
    user.reset_request_note = None

    # Invalidate all prior sessions for security
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id)
        .values(is_revoked=True)
    )

    await db.commit()
    return {"message": f"Password reset successfully for user {user.email}."}