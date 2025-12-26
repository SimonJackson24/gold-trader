"""
Authentication module for XAUUSD Gold Trading System.

Provides secure authentication, authorization, and session management
with JWT tokens, rate limiting, and role-based access control.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .jwt_handler import (
    JWTHandler,
    UserSession,
    RateLimiter,
    jwt_handler,
    require_permission,
    require_role,
)

__all__ = [
    "JWTHandler",
    "UserSession",
    "RateLimiter",
    "jwt_handler",
    "require_permission",
    "require_role",
]
