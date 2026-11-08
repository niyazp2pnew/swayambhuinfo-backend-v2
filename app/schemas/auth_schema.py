import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.auth_model import UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


# Admin-only user creation schema
class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole


# Admin-only password assignment / overwrite
class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


# Employee request to Admin for password reset
class PasswordResetSubmitRequest(BaseModel):
    email: EmailStr
    note: str | None = Field(None, max_length=255)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    password_reset_pending: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordResetPendingResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    reset_request_note: str | None

    model_config = ConfigDict(from_attributes=True)