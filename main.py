"""
Main entry point for XAUUSD Gold Trading System.

Provides command-line interface for running the application
with various options and configurations.
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import asyncio
import argparse
import sys
from pathlib import Path
import signal
import logging

from src.config import get_settings
from src.logging_config import setup_logging, get_logger
from src.api.main import app
from src.monitoring.health import setup_health_checks
from src.monitoring.metrics import get_system_metrics
import uvicorn


logger = get_logger(__name__)


class TradingSystemApp:
    """Main application class."""

    def __init__(self):
        self.settings = get_settings()
        self.running = False

    async def start(self, host=None, port=None, reload=False):
        """Start the trading system."""
        logger.info("Starting XAUUSD Gold Trading System...")

        try:
            # Setup logging
            setup_logging()

            # Setup health checks
            await self._setup_health_checks()

            # Start system metrics collection
            system_metrics = get_system_metrics()
            await system_metrics.start()

            # Initialize database tables
            from src.database.connection import init_database

            await init_database()

            # Start FastAPI application
            config = uvicorn.Config(
                app=app,
                host=host or self.settings.host,
                port=port or self.settings.port,
                reload=reload,
                log_level="info",
            )

            server = uvicorn.Server(config)

            # Setup signal handlers
            def signal_handler(signum, frame):
                logger.info(f"Received signal {signum}, shutting down...")
                self.running = False
                server.should_exit = True

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            self.running = True
            logger.info(
                f"Server starting on {host or self.settings.host}:{port or self.settings.port}"
            )

            await server.serve()

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            sys.exit(1)
        finally:
            await self._cleanup()

    async def _setup_health_checks(self):
        """Setup health checks."""
        # Import here to avoid circular imports
        from src.connectors.mt5_connector import MT5Connector
        from src.connectors.websocket_server import WebSocketServer
        from src.notifications.telegram_service import TelegramService

        # Create service instances (mock for now)
        mt5_connector = None
        websocket_server = None
        telegram_service = None

        # Setup health checks
        setup_health_checks(
            mt5_connector=mt5_connector,
            websocket_server=websocket_server,
            telegram_service=telegram_service,
        )

        logger.info("Health checks configured")

    async def _cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up resources...")

        # Stop system metrics
        system_metrics = get_system_metrics()
        await system_metrics.stop()

        logger.info("Application shutdown complete")


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="XAUUSD Gold Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Start with default settings
  python main.py --host 0.0.0.0 --port 8080  # Custom host/port
  python main.py --reload                   # Enable auto-reload for development
  python main.py --config custom.env         # Use custom config file
        """,
    )

    parser.add_argument(
        "--host", default=None, help="Host to bind the server to (default: from config)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (default: from config)",
    )

    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    parser.add_argument(
        "--config", type=str, default=None, help="Path to configuration file"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Override log level",
    )

    parser.add_argument(
        "--version", action="version", version="XAUUSD Gold Trading System 1.0.0"
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Override config file if specified
    if args.config:
        import os

        os.environ["CONFIG_FILE"] = args.config

    # Override log level if specified
    if args.log_level:
        import os

        os.environ["LOG_LEVEL"] = args.log_level

    # Create and start application
    app = TradingSystemApp()

    try:
        asyncio.run(app.start(host=args.host, port=args.port, reload=args.reload))
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
