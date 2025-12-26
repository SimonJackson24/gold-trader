"""
Logging configuration for XAUUSD Gold Trading System.

Provides structured logging with multiple handlers,
log levels, and formatting.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any

from .config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
            ]:
                log_entry[key] = value

        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format the message
        formatted = super().format(record)

        # Add color to level name
        formatted = formatted.replace(
            f"[{record.levelname}]", f"[{color}{record.levelname}{reset}]"
        )

        return formatted


def setup_logging():
    """Set up logging configuration."""
    settings = get_settings()

    # Create logs directory
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if settings.debug:
        console_formatter = ColoredFormatter(
            fmt="[{asctime}] [{levelname}] {name}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{",
        )
    else:
        console_formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname}] {name}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{",
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    if settings.json_logs:
        file_formatter = JSONFormatter()
    else:
        file_formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname}] {name} [{module}:{funcName}:{lineno}]: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{",
        )

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_file = log_dir / "error.log"
    error_handler = logging.handlers.RotatingFileHandler(
        filename=error_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)

    if settings.json_logs:
        error_formatter = JSONFormatter()
    else:
        error_formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname}] {name} [{module}:{funcName}:{lineno}]: {message}\n{exc_text}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{",
        )

    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)

    # Trading specific log handler
    trading_log = log_dir / "trading.log"
    trading_handler = logging.handlers.RotatingFileHandler(
        filename=trading_log,
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10,
        encoding="utf-8",
    )
    trading_handler.setLevel(logging.INFO)

    # Create trading logger filter
    class TradingFilter(logging.Filter):
        def filter(self, record):
            return any(
                keyword in record.name.lower()
                for keyword in ["trade", "signal", "mt5", "market"]
            )

    trading_handler.addFilter(TradingFilter())

    if settings.json_logs:
        trading_formatter = JSONFormatter()
    else:
        trading_formatter = logging.Formatter(
            fmt="[{asctime}] [{levelname}] {name}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{",
        )

    trading_handler.setFormatter(trading_formatter)
    root_logger.addHandler(trading_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured - Level: {settings.log_level}, JSON: {settings.json_logs}"
    )
    logger.info(f"Log file: {settings.log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get logger with specific name."""
    return logging.getLogger(name)


class TradingLogger:
    """Specialized logger for trading operations."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"trading.{name}")

    def log_signal(self, signal_data: Dict[str, Any]):
        """Log trading signal."""
        self.logger.info(f"Signal generated: {signal_data}")

    def log_trade(self, trade_data: Dict[str, Any]):
        """Log trade execution."""
        self.logger.info(f"Trade executed: {trade_data}")

    def log_market_data(self, symbol: str, data: Dict[str, Any]):
        """Log market data."""
        self.logger.debug(f"Market data [{symbol}]: {data}")

    def log_error(
        self, operation: str, error: Exception, context: Dict[str, Any] = None
    ):
        """Log trading error with context."""
        error_msg = f"Error in {operation}: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        self.logger.error(error_msg, exc_info=True)

    def log_performance(
        self, operation: str, duration: float, details: Dict[str, Any] = None
    ):
        """Log performance metrics."""
        perf_msg = f"Performance [{operation}]: {duration:.3f}s"
        if details:
            perf_msg += f" | Details: {details}"
        self.logger.info(perf_msg)


class MetricsLogger:
    """Logger for application metrics."""

    def __init__(self):
        self.logger = logging.getLogger("metrics")

    def log_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Log counter metric."""
        metric_data = {
            "type": "counter",
            "name": name,
            "value": value,
            "labels": labels or {},
        }
        self.logger.info(f"Metric: {metric_data}")

    def log_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Log gauge metric."""
        metric_data = {
            "type": "gauge",
            "name": name,
            "value": value,
            "labels": labels or {},
        }
        self.logger.info(f"Metric: {metric_data}")

    def log_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Log histogram metric."""
        metric_data = {
            "type": "histogram",
            "name": name,
            "value": value,
            "labels": labels or {},
        }
        self.logger.info(f"Metric: {metric_data}")


# Global metrics logger
metrics = MetricsLogger()
