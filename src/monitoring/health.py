"""
Health check system for XAUUSD Gold Trading System.

Provides comprehensive health monitoring for all system components
including external dependencies and internal services.
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..logging_config import get_logger
from ..database import get_database
from ..config import get_settings


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    check_func: Callable
    timeout: float = 5.0
    critical: bool = True
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class HealthResult:
    """Health check result."""
    name: str
    status: HealthStatus
    message: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


class HealthChecker:
    """Health checker implementation."""
    
    def __init__(self):
        self.logger = get_logger("health")
        self.checks: List[HealthCheck] = []
        self.results: Dict[str, HealthResult] = {}
        self._last_check: Optional[datetime] = None
    
    def add_check(self, check: HealthCheck):
        """Add health check."""
        self.checks.append(check)
        self.logger.info(f"Added health check: {check.name}")
    
    def remove_check(self, name: str):
        """Remove health check."""
        self.checks = [c for c in self.checks if c.name != name]
        if name in self.results:
            del self.results[name]
        self.logger.info(f"Removed health check: {name}")
    
    async def check_health(self, check_name: str = None) -> Dict[str, HealthResult]:
        """Run health checks."""
        if check_name:
            checks = [c for c in self.checks if c.name == check_name]
            if not checks:
                raise ValueError(f"Health check not found: {check_name}")
        else:
            checks = self.checks
        
        results = {}
        
        for check in checks:
            try:
                start_time = time.time()
                
                # Run check with timeout
                result = await asyncio.wait_for(
                    self._run_check(check),
                    timeout=check.timeout
                )
                
                duration = time.time() - start_time
                result.duration = duration
                
                results[check.name] = result
                self.logger.debug(f"Health check {check.name}: {result.status.value} ({duration:.3f}s)")
                
            except asyncio.TimeoutError:
                results[check.name] = HealthResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timed out after {check.timeout}s",
                    duration=check.timeout
                )
                self.logger.warning(f"Health check {check.name} timed out")
                
            except Exception as e:
                results[check.name] = HealthResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(e)}",
                    duration=0.0
                )
                self.logger.error(f"Health check {check.name} failed: {e}")
        
        # Update stored results
        self.results.update(results)
        self._last_check = datetime.utcnow()
        
        return results
    
    async def _run_check(self, check: HealthCheck) -> HealthResult:
        """Run individual health check."""
        try:
            # Call check function
            result = await check.check_func()
            
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "Check passed" if result else "Check failed"
            elif isinstance(result, dict):
                status = HealthStatus(result.get('status', HealthStatus.UNKNOWN.value))
                message = result.get('message', 'No message')
            else:
                status = HealthStatus.HEALTHY
                message = str(result)
            
            return HealthResult(
                name=check.name,
                status=status,
                message=message,
                duration=0.0
            )
            
        except Exception as e:
            return HealthResult(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration=0.0
            )
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.results:
            return HealthStatus.UNKNOWN
        
        # Check for critical failures
        critical_checks = [c for c in self.checks if c.critical]
        critical_results = [r for r in self.results.values() 
                         if r.name in [c.name for c in critical_checks]]
        
        if critical_results:
            critical_statuses = [r.status for r in critical_results]
            if HealthStatus.UNHEALTHY in critical_statuses:
                return HealthStatus.UNHEALTHY
            elif HealthStatus.DEGRADED in critical_statuses:
                return HealthStatus.DEGRADED
        
        # Check all results
        all_statuses = [r.status for r in self.results.values()]
        if HealthStatus.UNHEALTHY in all_statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in all_statuses:
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in all_statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_summary(self) -> Dict[str, Any]:
        """Get health summary."""
        overall_status = self.get_overall_status()
        
        return {
            'status': overall_status.value,
            'timestamp': self._last_check.isoformat() if self._last_check else None,
            'checks': {name: {
                'status': result.status.value,
                'message': result.message,
                'duration': result.duration,
                'timestamp': result.timestamp.isoformat(),
                'details': result.details
            } for name, result in self.results.items()},
            'total_checks': len(self.checks),
            'passed_checks': len([r for r in self.results.values() 
                               if r.status == HealthStatus.HEALTHY]),
            'failed_checks': len([r for r in self.results.values() 
                               if r.status == HealthStatus.UNHEALTHY])
        }


# Built-in health checks
class DatabaseHealthCheck:
    """Database health check."""
    
    def __init__(self):
        self.logger = get_logger("health.database")
    
    async def check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            db = get_database()
            
            # Test connection
            await db.execute("SELECT 1")
            
            # Get connection info
            pool_info = await db.get_pool_info()
            
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'Database connection successful',
                'details': {
                    'pool_size': pool_info.get('size'),
                    'active_connections': pool_info.get('active')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Database connection failed: {str(e)}'
            }


class RedisHealthCheck:
    """Redis health check."""
    
    def __init__(self):
        self.logger = get_logger("health.redis")
    
    async def check(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            import redis
            settings = get_settings()
            
            # Connect to Redis
            r = redis.from_url(settings.redis_url)
            
            # Test connection
            await r.ping()
            
            # Get info
            info = await r.info()
            
            return {
                'status': HealthStatus.HEALTHY.value,
                'message': 'Redis connection successful',
                'details': {
                    'version': info.get('redis_version'),
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Redis connection failed: {str(e)}'
            }


class MT5HealthCheck:
    """MT5 connector health check."""
    
    def __init__(self, mt5_connector):
        self.mt5_connector = mt5_connector
        self.logger = get_logger("health.mt5")
    
    async def check(self) -> Dict[str, Any]:
        """Check MT5 connector status."""
        try:
            if not self.mt5_connector:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': 'MT5 connector not initialized'
                }
            
            status = self.mt5_connector.get_status()
            
            if status.get('is_connected'):
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'MT5 connector connected',
                    'details': status
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'MT5 connector disconnected',
                    'details': status
                }
                
        except Exception as e:
            self.logger.error(f"MT5 health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'MT5 connector check failed: {str(e)}'
            }


class WebSocketHealthCheck:
    """WebSocket server health check."""
    
    def __init__(self, websocket_server):
        self.websocket_server = websocket_server
        self.logger = get_logger("health.websocket")
    
    async def check(self) -> Dict[str, Any]:
        """Check WebSocket server status."""
        try:
            if not self.websocket_server:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': 'WebSocket server not initialized'
                }
            
            status = self.websocket_server.get_status()
            
            if status.get('is_running'):
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'WebSocket server running',
                    'details': status
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'WebSocket server stopped',
                    'details': status
                }
                
        except Exception as e:
            self.logger.error(f"WebSocket health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'WebSocket server check failed: {str(e)}'
            }


class TelegramHealthCheck:
    """Telegram bot health check."""
    
    def __init__(self, telegram_service):
        self.telegram_service = telegram_service
        self.logger = get_logger("health.telegram")
    
    async def check(self) -> Dict[str, Any]:
        """Check Telegram bot status."""
        try:
            if not self.telegram_service:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': 'Telegram service not initialized'
                }
            
            status = self.telegram_service.get_status()
            
            if status.get('is_running'):
                return {
                    'status': HealthStatus.HEALTHY.value,
                    'message': 'Telegram bot running',
                    'details': status
                }
            else:
                return {
                    'status': HealthStatus.UNHEALTHY.value,
                    'message': 'Telegram bot stopped',
                    'details': status
                }
                
        except Exception as e:
            self.logger.error(f"Telegram health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'Telegram bot check failed: {str(e)}'
            }


class SystemHealthCheck:
    """System resource health check."""
    
    def __init__(self):
        self.logger = get_logger("health.system")
    
    async def check(self) -> Dict[str, Any]:
        """Check system resources."""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 90:
                status = HealthStatus.DEGRADED
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory.percent > 90:
                status = HealthStatus.DEGRADED
                issues.append(f"High memory usage: {memory.percent}%")
            
            if disk.percent > 90:
                status = HealthStatus.DEGRADED
                issues.append(f"High disk usage: {disk.percent}%")
            
            message = "System resources OK"
            if issues:
                message = "; ".join(issues)
            
            return {
                'status': status.value,
                'message': message,
                'details': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent,
                    'memory_available': f"{memory.available / (1024**3):.1f}GB",
                    'disk_free': f"{disk.free / (1024**3):.1f}GB"
                }
            }
            
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'message': f'System check failed: {str(e)}'
            }


# Global health checker
health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    return health_checker


def setup_health_checks(mt5_connector=None, websocket_server=None, telegram_service=None):
    """Set up default health checks."""
    # Add built-in checks
    health_checker.add_check(HealthCheck(
        name="database",
        check_func=DatabaseHealthCheck().check,
        timeout=5.0,
        critical=True,
        description="Database connectivity"
    ))
    
    health_checker.add_check(HealthCheck(
        name="redis",
        check_func=RedisHealthCheck().check,
        timeout=5.0,
        critical=True,
        description="Redis connectivity"
    ))
    
    if mt5_connector:
        health_checker.add_check(HealthCheck(
            name="mt5",
            check_func=MT5HealthCheck(mt5_connector).check,
            timeout=10.0,
            critical=True,
            description="MT5 connector"
        ))
    
    if websocket_server:
        health_checker.add_check(HealthCheck(
            name="websocket",
            check_func=WebSocketHealthCheck(websocket_server).check,
            timeout=5.0,
            critical=True,
            description="WebSocket server"
        ))
    
    if telegram_service:
        health_checker.add_check(HealthCheck(
            name="telegram",
            check_func=TelegramHealthCheck(telegram_service).check,
            timeout=10.0,
            critical=False,
            description="Telegram bot"
        ))
    
    health_checker.add_check(HealthCheck(
        name="system",
        check_func=SystemHealthCheck().check,
        timeout=5.0,
        critical=False,
        description="System resources"
    ))