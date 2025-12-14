"""
JWT authentication handler for XAUUSD Gold Trading System.

Provides secure JWT token generation, validation, and management
with proper security controls and rate limiting.
"""

import jwt
import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from functools import wraps
import asyncio
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config import get_settings
from ..database.repositories import ConfigRepository


@dataclass
class UserSession:
    """User session data."""
    user_id: str
    username: str
    role: str
    permissions: list
    created_at: datetime
    last_activity: datetime
    token_jti: str


class RateLimiter:
    """
    Advanced rate limiter with sliding window and user-specific limits.
    """
    
    def __init__(self):
        """Initialize rate limiter."""
        self.requests = defaultdict(lambda: deque())
        self.lock = asyncio.Lock()
    
    async def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Rate limit key (IP, user_id, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        async with self.lock:
            now = datetime.utcnow()
            request_queue = self.requests[key]
            
            # Remove old requests outside window
            while request_queue and (now - request_queue[0]).total_seconds() > window:
                request_queue.popleft()
            
            # Check if limit exceeded
            if len(request_queue) >= limit:
                return False, {
                    'limit': limit,
                    'window': window,
                    'current': len(request_queue),
                    'reset_time': (request_queue[0] + timedelta(seconds=window)).isoformat()
                }
            
            # Add current request
            request_queue.append(now)
            
            return True, {
                'limit': limit,
                'window': window,
                'current': len(request_queue),
                'remaining': limit - len(request_queue)
            }


class JWTHandler:
    """
    JWT token handler with secure implementation.
    """
    
    def __init__(self):
        """Initialize JWT handler."""
        self.settings = get_settings()
        self.rate_limiter = RateLimiter()
        self.blacklisted_tokens = set()
        self.user_sessions = {}  # In production, use Redis
        self.security = HTTPBearer()
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Hashed password
            
        Returns:
            True if password matches
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _generate_jti(self) -> str:
        """
        Generate unique JWT ID.
        
        Returns:
            Unique JWT identifier
        """
        return secrets.token_urlsafe(32)
    
    def _get_token_expiry(self, token_type: str = "access") -> datetime:
        """
        Get token expiry time.
        
        Args:
            token_type: Type of token (access/refresh)
            
        Returns:
            Expiry datetime
        """
        minutes = (
            self.settings.jwt_expire_minutes 
            if token_type == "access" 
            else self.settings.jwt_refresh_expire_minutes
        )
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    async def create_access_token(self, user_data: Dict[str, Any]) -> Tuple[str, str, datetime]:
        """
        Create JWT access token.
        
        Args:
            user_data: User information
            
        Returns:
            Tuple of (token, jti, expiry)
        """
        jti = self._generate_jti()
        expiry = self._get_token_expiry("access")
        
        # Create session
        session = UserSession(
            user_id=user_data['user_id'],
            username=user_data['username'],
            role=user_data.get('role', 'user'),
            permissions=user_data.get('permissions', []),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            token_jti=jti
        )
        
        # Store session
        self.user_sessions[jti] = session
        
        # Create JWT payload
        payload = {
            'jti': jti,
            'sub': user_data['user_id'],
            'username': user_data['username'],
            'role': user_data.get('role', 'user'),
            'permissions': user_data.get('permissions', []),
            'iat': datetime.utcnow(),
            'exp': expiry,
            'type': 'access'
        }
        
        # Sign token
        token = jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        return token, jti, expiry
    
    async def create_refresh_token(self, user_id: str) -> Tuple[str, str, datetime]:
        """
        Create JWT refresh token.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (token, jti, expiry)
        """
        jti = self._generate_jti()
        expiry = self._get_token_expiry("refresh")
        
        payload = {
            'jti': jti,
            'sub': user_id,
            'iat': datetime.utcnow(),
            'exp': expiry,
            'type': 'refresh'
        }
        
        token = jwt.encode(
            payload,
            self.settings.secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        return token, jti, expiry
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti in self.blacklisted_tokens:
                return None
            
            # Check session exists and is valid
            if payload.get('type') == 'access':
                session = self.user_sessions.get(jti)
                if not session:
                    return None
                
                # Update last activity
                session.last_activity = datetime.utcnow()
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke JWT token by adding to blacklist.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if revoked successfully
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm],
                options={"verify_exp": False}
            )
            
            jti = payload.get('jti')
            if jti:
                self.blacklisted_tokens.add(jti)
                
                # Remove session if access token
                if payload.get('type') == 'access':
                    self.user_sessions.pop(jti, None)
                
                return True
            
            return False
            
        except jwt.InvalidTokenError:
            return False
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str, datetime]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token tuple or None
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            if payload.get('type') != 'refresh':
                return None
            
            # Get user data (in production, fetch from database)
            user_id = payload['sub']
            user_data = {
                'user_id': user_id,
                'username': f"user_{user_id}",  # In production, fetch from DB
                'role': 'user',
                'permissions': ['read']
            }
            
            return await self.create_access_token(user_data)
            
        except jwt.InvalidTokenError:
            return None
    
    async def check_rate_limit(self, request: Request, limit: int = None, window: int = None) -> bool:
        """
        Check rate limit for request.
        
        Args:
            request: FastAPI request
            limit: Request limit (default from settings)
            window: Time window in seconds (default from settings)
            
        Returns:
            True if request is allowed
        """
        if limit is None:
            limit = self.settings.rate_limit_per_minute
        if window is None:
            window = 60  # 1 minute default
        
        # Use IP address as rate limit key
        key = get_remote_address(request)
        
        allowed, info = await self.rate_limiter.is_allowed(key, limit, window)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": info['limit'],
                    "window": info['window'],
                    "reset_time": info['reset_time']
                },
                headers={"Retry-After": str(window)}
            )
        
        return True
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """
        Get current user from JWT credentials.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            User payload
            
        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        
        # This should be awaited in async context
        # For now, we'll use sync verification
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            if payload.get('jti') in self.blacklisted_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


# Global JWT handler instance
jwt_handler = JWTHandler()


def require_permission(permission: str):
    """
    Decorator to require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from request
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No request context"
                )
            
            user = getattr(request.state, 'user', None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permission
            permissions = user.get('permissions', [])
            if permission not in permissions and 'admin' not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role.
    
    Args:
        role: Required role
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No request context"
                )
            
            user = getattr(request.state, 'user', None)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check role
            user_role = user.get('role')
            if user_role != role and user_role != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator