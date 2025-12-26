"""
Test suite for XAUUSD Gold Trading System.

Provides comprehensive testing for all components including:
- Unit tests
- Integration tests
- API tests
- Performance tests
"""

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

import os
import sys
import asyncio
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///./test.db",
    "redis_url": "redis://localhost:6379/1",
    "test_data_dir": Path(__file__).parent / "data",
    "log_level": "DEBUG",
}

# Ensure test data directory exists
TEST_CONFIG["test_data_dir"].mkdir(exist_ok=True)
