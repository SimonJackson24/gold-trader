"""
Monitoring module for XAUUSD Gold Trading System.

Provides:
- Metrics collection and monitoring
- Health checks
- Performance monitoring
- System monitoring
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

from .metrics import (
    MetricsRegistry,
    Counter,
    Gauge,
    Histogram,
    SystemMetrics,
    ApplicationMetrics,
    get_registry,
    get_system_metrics,
    get_application_metrics,
    monitor_performance,
)

from .health import (
    HealthChecker,
    HealthCheck,
    HealthResult,
    HealthStatus,
    get_health_checker,
    setup_health_checks,
)

__all__ = [
    "MetricsRegistry",
    "Counter",
    "Gauge",
    "Histogram",
    "SystemMetrics",
    "ApplicationMetrics",
    "get_registry",
    "get_system_metrics",
    "get_application_metrics",
    "monitor_performance",
    "HealthChecker",
    "HealthCheck",
    "HealthResult",
    "HealthStatus",
    "get_health_checker",
    "setup_health_checks",
]
