from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    UserProfileUpdateRequest,
    UserProfileResponse,
    AuthResponse
)
from app.services.auth_service import AuthService
from app.routers.deps import get_current_user, get_client_ip
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: UserRegisterRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    try:
        user = AuthService.register_user(db, req, ip_address=ip)
        _, token = AuthService.authenticate_user(db, UserLoginRequest(email=req.email, password=req.password), ip_address=ip)
        
        # Set HTTP-only secure cookie
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_MINUTES * 60,
            path="/"
        )
        return AuthResponse(
            message="User registered and logged in successfully.",
            user=UserProfileResponse.model_validate(user),
            token=token
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=AuthResponse)
def login(
    req: UserLoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    try:
        user, token = AuthService.authenticate_user(db, req, ip_address=ip)
        response.set_cookie(
            key=settings.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.SESSION_EXPIRE_MINUTES * 60,
            path="/"
        )
        return AuthResponse(
            message="Logged in successfully.",
            user=UserProfileResponse.model_validate(user),
            token=token
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        samesite=settings.COOKIE_SAMESITE
    )
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfileResponse.model_validate(current_user)

@router.post("/change-password")
def change_password(
    req: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    try:
        AuthService.change_password(db, current_user, req, ip_address=ip)
        return {"message": "Password changed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.patch("/profile", response_model=UserProfileResponse)
def update_profile(
    req: UserProfileUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    updated_user = AuthService.update_profile(db, current_user, req, ip_address=ip)
    return UserProfileResponse.model_validate(updated_user)
