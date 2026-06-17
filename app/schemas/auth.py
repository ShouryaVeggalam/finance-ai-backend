from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.roles import UserRole


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseSchema):
    refresh_token: str


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str


class RegisterRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    company_name: str
    role: UserRole = UserRole.FOUNDER


class UserResponse(BaseSchema):
    id: UUID
    email: str
    full_name: str
    role: str
    company_id: UUID
    is_active: bool
    created_at: datetime


class CompanyResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    currency: str
    is_active: bool
    created_at: datetime
