"""
Authentication endpoints for XAUUSD Gold Trading System.

Provides secure login, logout, token refresh, and user management
with proper rate limiting and security controls.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, EmailStr
import logging

from ..auth import jwt_handler, require_permission, require_role
from ..config import get_settings
from ..database.repositories import ConfigRepository


# Pydantic models for authentication
class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    remember_me: bool = Field(
        default=False, description="Remember me for longer session"
    )


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_info: Dict[str, Any] = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LogoutRequest(BaseModel):
    """Logout request model."""

    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")


class PasswordChangeRequest(BaseModel):
    """Password change request model."""

    current_password: str = Field(
        ..., min_length=8, max_length=100, description="Current password"
    )
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password"
    )
    confirm_password: str = Field(
        ..., min_length=8, max_length=100, description="Confirm new password"
    )


class UserRegistrationRequest(BaseModel):
    """User registration request model."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    confirm_password: str = Field(
        ..., min_length=8, max_length=100, description="Confirm password"
    )
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")


# Router
router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)
settings = get_settings()


# Mock user database (in production, use real database with proper hashing)
MOCK_USERS = {
    "admin": {
        "user_id": "admin_001",
        "username": "admin",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm",  # "admin123"
        "email": "admin@trading.com",
        "role": "admin",
        "permissions": ["read", "write", "delete", "admin"],
        "full_name": "System Administrator",
        "is_active": True,
        "created_at": datetime.utcnow() - timedelta(days=365),
    },
    "trader": {
        "user_id": "trader_001",
        "username": "trader",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpm",  # "trader123"
        "email": "trader@trading.com",
        "role": "trader",
        "permissions": ["read", "write"],
        "full_name": "Professional Trader",
        "is_active": True,
        "created_at": datetime.utcnow() - timedelta(days=30),
    },
}


async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user credentials.

    Args:
        username: Username
        password: Plain text password

    Returns:
        User data or None if authentication fails
    """
    user = MOCK_USERS.get(username)
    if not user:
        return None

    if not user.get("is_active", False):
        return None

    # Verify password (in production, use secure password verification)
    if not jwt_handler._verify_password(password, user["password_hash"]):
        return None

    # Remove sensitive data
    user_data = {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "permissions": user["permissions"],
        "full_name": user["full_name"],
    }

    return user_data


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    Rate limited: 5 attempts per minute per IP
    """
    # Apply rate limiting
    await jwt_handler.check_rate_limit(request, limit=5, window=60)

    # Authenticate user
    user_data = await authenticate_user(login_data.username, login_data.password)
    if not user_data:
        logger.warning(f"Failed login attempt for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token, jti, expiry = await jwt_handler.create_access_token(user_data)

    # Create refresh token if enabled
    refresh_token = None
    if settings.jwt_refresh_token_enabled or login_data.remember_me:
        refresh_token, _, _ = await jwt_handler.create_refresh_token(
            user_data["user_id"]
        )

    # Calculate expires in seconds
    expires_in = int((expiry - datetime.utcnow()).total_seconds())

    logger.info(f"User {login_data.username} logged in successfully")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user_info=user_data,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: Request, refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    Rate limited: 10 requests per minute per IP
    """
    # Apply rate limiting
    await jwt_handler.check_rate_limit(request, limit=10, window=60)

    # Validate refresh token
    new_token = await jwt_handler.refresh_access_token(refresh_data.refresh_token)
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token, jti, expiry = new_token
    expires_in = int((expiry - datetime.utcnow()).total_seconds())

    return RefreshTokenResponse(
        access_token=access_token, token_type="bearer", expires_in=expires_in
    )


@router.post("/logout")
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    credentials: HTTPBearer = Depends(HTTPBearer()),
):
    """
    Logout user and revoke tokens.

    Rate limited: 20 requests per minute per IP
    """
    # Apply rate limiting
    await jwt_handler.check_rate_limit(request, limit=20, window=60)

    # Revoke access token
    if credentials:
        await jwt_handler.revoke_token(credentials.credentials)

    # Revoke refresh token if provided
    if logout_data.refresh_token:
        await jwt_handler.revoke_token(logout_data.refresh_token)

    logger.info("User logged out successfully")

    return {"message": "Logged out successfully"}


@router.post("/change-password")
@require_permission("write")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    credentials: HTTPBearer = Depends(HTTPBearer()),
):
    """
    Change user password.

    Requires authentication and 'write' permission.
    Rate limited: 3 attempts per minute per user
    """
    # Apply rate limiting
    await jwt_handler.check_rate_limit(request, limit=3, window=60)

    # Verify current password
    user = jwt_handler.get_current_user(credentials)
    user_data = MOCK_USERS.get(user["username"])

    if not jwt_handler._verify_password(
        password_data.current_password, user_data["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match"
        )

    # Update password (in production, update in database)
    new_hash = jwt_handler._hash_password(password_data.new_password)
    user_data["password_hash"] = new_hash

    logger.info(f"Password changed for user: {user['username']}")

    return {"message": "Password changed successfully"}


@router.post("/register", response_model=LoginResponse)
async def register(request: Request, registration_data: UserRegistrationRequest):
    """
    Register new user account.

    Rate limited: 2 registrations per minute per IP
    """
    # Apply rate limiting
    await jwt_handler.check_rate_limit(request, limit=2, window=60)

    # Validate passwords match
    if registration_data.password != registration_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    # Check if user already exists
    if registration_data.username in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )

    # Create new user (in production, save to database)
    new_user = {
        "user_id": f"user_{datetime.utcnow().timestamp()}",
        "username": registration_data.username,
        "password_hash": jwt_handler._hash_password(registration_data.password),
        "email": registration_data.email,
        "role": "user",
        "permissions": ["read"],
        "full_name": registration_data.full_name or registration_data.username,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }

    MOCK_USERS[registration_data.username] = new_user

    # Create tokens for new user
    user_data = {
        "user_id": new_user["user_id"],
        "username": new_user["username"],
        "email": new_user["email"],
        "role": new_user["role"],
        "permissions": new_user["permissions"],
        "full_name": new_user["full_name"],
    }

    access_token, jti, expiry = await jwt_handler.create_access_token(user_data)
    refresh_token, _, _ = await jwt_handler.create_refresh_token(user_data["user_id"])
    expires_in = int((expiry - datetime.utcnow()).total_seconds())

    logger.info(f"New user registered: {registration_data.username}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
        user_info=user_data,
    )


@router.get("/me")
@require_permission("read")
async def get_current_user_info(credentials: HTTPBearer = Depends(HTTPBearer())):
    """
    Get current user information.

    Requires authentication and 'read' permission.
    """
    user = jwt_handler.get_current_user(credentials)

    # Get full user data
    user_data = MOCK_USERS.get(user["username"], {})

    return {
        "user_id": user["sub"],
        "username": user["username"],
        "email": user_data.get("email"),
        "role": user["role"],
        "permissions": user["permissions"],
        "full_name": user_data.get("full_name"),
        "created_at": user_data.get("created_at"),
        "last_activity": datetime.utcnow().isoformat(),
    }


@router.post("/verify-token")
async def verify_token(token: str):
    """
    Verify JWT token validity.

    Rate limited: 100 requests per minute per IP
    """
    payload = await jwt_handler.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return {
        "valid": True,
        "payload": payload,
        "expires_at": datetime.fromtimestamp(payload["exp"]).isoformat(),
    }
