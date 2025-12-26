"""
Metrics collection and monitoring for XAUUSD Gold Trading System.

Provides application metrics, performance monitoring,
and health checks.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import time
import asyncio
import psutil
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading

from ..logging_config import get_logger, metrics


@dataclass
class MetricValue:
    """Metric value with timestamp."""

    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)


class Counter:
    """Counter metric implementation."""

    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, int] = defaultdict(int)
        self.logger = get_logger(f"metrics.counter.{name}")

    def inc(self, value: int = 1, **labels):
        """Increment counter."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        self._values[label_tuple] += value

        metrics.log_counter(self.name, value, labels)
        self.logger.debug(f"Counter {self.name} incremented by {value}")

    def get(self, **labels) -> int:
        """Get counter value."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        return self._values[label_tuple]

    def reset(self, **labels):
        """Reset counter."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        self._values[label_tuple] = 0

    def values(self) -> Dict[str, int]:
        """Get all counter values."""
        result = {}
        for label_tuple, value in self._values.items():
            label_str = ",".join(str(l) for l in label_tuple if l)
            key = f"{self.name}{{{label_str}}}" if label_str else self.name
            result[key] = value
        return result


class Gauge:
    """Gauge metric implementation."""

    def __init__(self, name: str, description: str = "", labels: List[str] = None):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[tuple, float] = {}
        self.logger = get_logger(f"metrics.gauge.{name}")

    def set(self, value: float, **labels):
        """Set gauge value."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        self._values[label_tuple] = value

        metrics.log_gauge(self.name, value, labels)
        self.logger.debug(f"Gauge {self.name} set to {value}")

    def get(self, **labels) -> Optional[float]:
        """Get gauge value."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        return self._values.get(label_tuple)

    def inc(self, value: float = 1, **labels):
        """Increment gauge value."""
        current = self.get(**labels) or 0
        self.set(current + value, **labels)

    def dec(self, value: float = 1, **labels):
        """Decrement gauge value."""
        current = self.get(**labels) or 0
        self.set(current - value, **labels)

    def values(self) -> Dict[str, float]:
        """Get all gauge values."""
        result = {}
        for label_tuple, value in self._values.items():
            label_str = ",".join(str(l) for l in label_tuple if l)
            key = f"{self.name}{{{label_str}}}" if label_str else self.name
            result[key] = value
        return result


class Histogram:
    """Histogram metric implementation."""

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: List[float] = None,
        labels: List[str] = None,
    ):
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ]
        self._values: Dict[tuple, List[float]] = defaultdict(list)
        self.logger = get_logger(f"metrics.histogram.{name}")

    def observe(self, value: float, **labels):
        """Observe value."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        self._values[label_tuple].append(value)

        # Keep only last 1000 observations per label combination
        if len(self._values[label_tuple]) > 1000:
            self._values[label_tuple] = self._values[label_tuple][-1000:]

        metrics.log_histogram(self.name, value, labels)
        self.logger.debug(f"Histogram {self.name} observed {value}")

    def get_buckets(self, **labels) -> Dict[str, int]:
        """Get bucket counts."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        values = self._values.get(label_tuple, [])

        bucket_counts = {}
        for bucket in self.buckets:
            count = sum(1 for v in values if v <= bucket)
            bucket_counts[f"le_{bucket}"] = count

        bucket_counts["le_inf"] = len(values)
        return bucket_counts

    def get_summary(self, **labels) -> Dict[str, float]:
        """Get summary statistics."""
        label_tuple = tuple(labels.get(name, "") for name in self.label_names)
        values = self._values.get(label_tuple, [])

        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(sorted_values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": sum(sorted_values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p90": sorted_values[int(count * 0.9)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)],
        }


class MetricsRegistry:
    """Central metrics registry."""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self.logger = get_logger("metrics.registry")

    def counter(
        self, name: str, description: str = "", labels: List[str] = None
    ) -> Counter:
        """Create or get counter."""
        if name not in self._metrics:
            self._metrics[name] = Counter(name, description, labels)
            self.logger.info(f"Created counter metric: {name}")
        return self._metrics[name]

    def gauge(
        self, name: str, description: str = "", labels: List[str] = None
    ) -> Gauge:
        """Create or get gauge."""
        if name not in self._metrics:
            self._metrics[name] = Gauge(name, description, labels)
            self.logger.info(f"Created gauge metric: {name}")
        return self._metrics[name]

    def histogram(
        self,
        name: str,
        description: str = "",
        buckets: List[float] = None,
        labels: List[str] = None,
    ) -> Histogram:
        """Create or get histogram."""
        if name not in self._metrics:
            self._metrics[name] = Histogram(name, description, buckets, labels)
            self.logger.info(f"Created histogram metric: {name}")
        return self._metrics[name]

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics values."""
        result = {}
        for name, metric in self._metrics.items():
            if hasattr(metric, "values"):
                result.update(metric.values())
        return result


class SystemMetrics:
    """System metrics collector."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.logger = get_logger("metrics.system")

        # System metrics
        self.cpu_usage = registry.gauge(
            "system_cpu_usage_percent", "CPU usage percentage"
        )
        self.memory_usage = registry.gauge(
            "system_memory_usage_percent", "Memory usage percentage"
        )
        self.disk_usage = registry.gauge(
            "system_disk_usage_percent", "Disk usage percentage"
        )
        self.network_bytes_sent = registry.counter(
            "system_network_bytes_sent_total", "Total bytes sent"
        )
        self.network_bytes_recv = registry.counter(
            "system_network_bytes_recv_total", "Total bytes received"
        )

        # Process metrics
        self.process_cpu = registry.gauge("process_cpu_percent", "Process CPU usage")
        self.process_memory = registry.gauge(
            "process_memory_bytes", "Process memory usage"
        )
        self.process_threads = registry.gauge(
            "process_threads_count", "Process thread count"
        )
        self.process_fds = registry.gauge(
            "process_fds_count", "Process file descriptor count"
        )

        self._running = False
        self._task = None

    async def start(self, interval: int = 30):
        """Start system metrics collection."""
        self._running = True
        self._task = asyncio.create_task(self._collect_loop(interval))
        self.logger.info("System metrics collection started")

    async def stop(self):
        """Stop system metrics collection."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("System metrics collection stopped")

    async def _collect_loop(self, interval: int):
        """Collect system metrics loop."""
        process = psutil.Process()

        while self._running:
            try:
                # System metrics
                self.cpu_usage.set(psutil.cpu_percent())

                memory = psutil.virtual_memory()
                self.memory_usage.set(memory.percent)

                disk = psutil.disk_usage("/")
                self.disk_usage.set(disk.percent)

                network = psutil.net_io_counters()
                self.network_bytes_sent.inc(network.bytes_sent)
                self.network_bytes_recv.inc(network.bytes_recv)

                # Process metrics
                self.process_cpu.set(process.cpu_percent())
                self.process_memory.set(process.memory_info().rss)
                self.process_threads.set(process.num_threads())

                try:
                    self.process_fds.set(process.num_fds())
                except (AttributeError, psutil.AccessDenied):
                    # num_fds not available on all platforms
                    pass

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(interval)


class ApplicationMetrics:
    """Application-specific metrics."""

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry
        self.logger = get_logger("metrics.application")

        # Trading metrics
        self.signals_generated = registry.counter(
            "trading_signals_generated_total",
            "Total signals generated",
            ["symbol", "type"],
        )
        self.trades_executed = registry.counter(
            "trading_trades_executed_total",
            "Total trades executed",
            ["symbol", "type", "status"],
        )
        self.trade_volume = registry.gauge(
            "trading_trade_volume", "Current trade volume", ["symbol"]
        )
        self.trade_profit_loss = registry.gauge(
            "trading_profit_loss", "Trade profit/loss", ["symbol"]
        )

        # Market data metrics
        self.market_data_updates = registry.counter(
            "market_data_updates_total", "Market data updates", ["symbol", "type"]
        )
        self.candle_processing_time = registry.histogram(
            "candle_processing_duration_seconds", "Candle processing time"
        )
        self.signal_generation_time = registry.histogram(
            "signal_generation_duration_seconds", "Signal generation time"
        )

        # API metrics
        self.api_requests = registry.counter(
            "api_requests_total", "API requests", ["method", "endpoint", "status"]
        )
        self.api_request_duration = registry.histogram(
            "api_request_duration_seconds", "API request duration"
        )

        # WebSocket metrics
        self.websocket_connections = registry.gauge(
            "websocket_connections_count", "WebSocket connections"
        )
        self.websocket_messages = registry.counter(
            "websocket_messages_total", "WebSocket messages", ["type"]
        )

        # Database metrics
        self.db_connections = registry.gauge(
            "database_connections_count", "Database connections"
        )
        self.db_query_duration = registry.histogram(
            "database_query_duration_seconds", "Database query duration"
        )

        # Error metrics
        self.errors_total = registry.counter(
            "errors_total", "Total errors", ["component", "type"]
        )
        self.exceptions_total = registry.counter(
            "exceptions_total", "Total exceptions", ["component", "type"]
        )

    def record_signal(self, symbol: str, signal_type: str):
        """Record signal generation."""
        self.signals_generated.inc(symbol=symbol, type=signal_type)

    def record_trade(
        self, symbol: str, trade_type: str, status: str, volume: float, pnl: float
    ):
        """Record trade execution."""
        self.trades_executed.inc(symbol=symbol, type=trade_type, status=status)
        self.trade_volume.set(volume, symbol=symbol)
        self.trade_profit_loss.set(pnl, symbol=symbol)

    def record_market_data(self, symbol: str, data_type: str):
        """Record market data update."""
        self.market_data_updates.inc(symbol=symbol, type=data_type)

    def record_api_request(
        self, method: str, endpoint: str, status: int, duration: float
    ):
        """Record API request."""
        self.api_requests.inc(method=method, endpoint=endpoint, status=str(status))
        self.api_request_duration.observe(duration)

    def record_websocket_connection(self, count: int):
        """Record WebSocket connection count."""
        self.websocket_connections.set(count)

    def record_websocket_message(self, message_type: str):
        """Record WebSocket message."""
        self.websocket_messages.inc(type=message_type)

    def record_error(self, component: str, error_type: str):
        """Record error."""
        self.errors_total.inc(component=component, type=error_type)

    def record_exception(self, component: str, exception_type: str):
        """Record exception."""
        self.exceptions_total.inc(component=component, type=exception_type)


# Global registry and metrics
registry = MetricsRegistry()
system_metrics = SystemMetrics(registry)
application_metrics = ApplicationMetrics(registry)


def get_registry() -> MetricsRegistry:
    """Get metrics registry."""
    return registry


def get_system_metrics() -> SystemMetrics:
    """Get system metrics collector."""
    return system_metrics


def get_application_metrics() -> ApplicationMetrics:
    """Get application metrics."""
    return application_metrics


# Performance monitoring decorator
def monitor_performance(metric_name: str = None):
    """Decorator to monitor function performance."""

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration in histogram
                histogram = registry.histogram(
                    f"{name}_duration_seconds", f"Duration of {name}"
                )
                histogram.observe(duration)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Record exception
                application_metrics.record_exception(func.__module__, type(e).__name__)

                # Record duration even for failed calls
                histogram = registry.histogram(
                    f"{name}_duration_seconds", f"Duration of {name}"
                )
                histogram.observe(duration)

                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            name = metric_name or f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record duration in histogram
                histogram = registry.histogram(
                    f"{name}_duration_seconds", f"Duration of {name}"
                )
                histogram.observe(duration)

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Record exception
                application_metrics.record_exception(func.__module__, type(e).__name__)

                # Record duration even for failed calls
                histogram = registry.histogram(
                    f"{name}_duration_seconds", f"Duration of {name}"
                )
                histogram.observe(duration)

                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
