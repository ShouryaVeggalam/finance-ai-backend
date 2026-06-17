from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_id, get_current_user
from app.database.session import get_db
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenRefreshRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    _, access, refresh = await service.register(data)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    _, access, refresh = await service.login(data.email, data.password)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    access, refresh_token = await service.refresh_tokens(data.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
