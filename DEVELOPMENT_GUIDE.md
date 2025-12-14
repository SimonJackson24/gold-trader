# Development Guide

Comprehensive guide for developers contributing to the XAUUSD Gold Trading System.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Git Workflow](#git-workflow)
5. [Code Review Process](#code-review-process)
6. [Testing Guidelines](#testing-guidelines)
7. [Documentation Standards](#documentation-standards)
8. [Contribution Guidelines](#contribution-guidelines)

---

## Development Environment Setup

### Prerequisites

```bash
# Python 3.11+
python --version

# Poetry for dependency management
curl -sSL https://install.python-poetry.org | python3 -

# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### Local Setup

```bash
# Clone repository
git clone https://github.com/your-org/xauusd-trading-system.git
cd xauusd-trading-system

# Install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start local services
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start development server
python -m src.main
```

### IDE Configuration

#### VSCode Settings

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "editor.rulers": [100],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true
  }
}
```

#### PyCharm Settings

- Enable Black formatter
- Set line length to 100
- Enable type checking
- Configure pytest as test runner

---

## Project Structure

```
xauusd-trading-system/
├── src/
│   ├── analysis/           # Market analysis modules
│   │   ├── smc/           # Smart Money Concepts
│   │   ├── indicators/    # Technical indicators
│   │   └── patterns/      # Chart patterns
│   ├── trading/           # Trading logic
│   │   ├── signal_generator.py
│   │   ├── trade_manager.py
│   │   └── risk_manager.py
│   ├── connectors/        # External connections
│   │   ├── mt5_bridge.py
│   │   └── telegram_bot.py
│   ├── database/          # Database models & queries
│   │   ├── models.py
│   │   └── repositories.py
│   ├── api/               # REST API
│   │   ├── routes/
│   │   └── schemas.py
│   ├── monitoring/        # Observability
│   │   ├── metrics.py
│   │   └── logging.py
│   └── utils/             # Utilities
│       ├── config.py
│       └── helpers.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── config/                # Configuration files
├── migrations/            # Database migrations
├── docker/                # Docker files
├── pyproject.toml         # Poetry dependencies
├── pytest.ini             # Pytest configuration
└── README.md
```

### Module Organization

```python
# Each module should have clear responsibilities

# analysis/smc/fair_value_gap.py
"""Fair Value Gap detection and analysis"""

class FairValueGapDetector:
    """Detects FVGs in price data"""
    pass

# analysis/smc/order_block.py
"""Order Block identification"""

class OrderBlockDetector:
    """Identifies order blocks"""
    pass
```

---

## Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these additions:

```python
# Line length: 100 characters
# Use Black formatter
# Use type hints
# Use docstrings

from typing import Optional, List, Dict
from datetime import datetime

class SignalGenerator:
    """
    Generates trading signals based on Smart Money Concepts.
    
    This class analyzes market structure, identifies high-probability
    setups, and generates actionable trading signals.
    
    Attributes:
        confluence_threshold: Minimum confluence score (0-100)
        min_risk_reward: Minimum risk:reward ratio
    """
    
    def __init__(
        self,
        confluence_threshold: float = 80.0,
        min_risk_reward: float = 2.0
    ) -> None:
        """
        Initialize signal generator.
        
        Args:
            confluence_threshold: Minimum confluence score required
            min_risk_reward: Minimum R:R ratio for valid signals
        """
        self.confluence_threshold = confluence_threshold
        self.min_risk_reward = min_risk_reward
    
    def generate_signal(
        self,
        analysis: Dict[str, any]
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal from analysis.
        
        Args:
            analysis: Market analysis data containing SMC indicators
        
        Returns:
            TradingSignal if valid setup found, None otherwise
        
        Raises:
            ValueError: If analysis data is invalid
        """
        if not self._validate_analysis(analysis):
            raise ValueError("Invalid analysis data")
        
        confluence = self._calculate_confluence(analysis)
        
        if confluence >= self.confluence_threshold:
            return self._create_signal(analysis, confluence)
        
        return None
```

### Naming Conventions

```python
# Classes: PascalCase
class TradeManager:
    pass

# Functions/Methods: snake_case
def calculate_position_size():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_CONCURRENT_TRADES = 3
DEFAULT_RISK_PERCENT = 1.0

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Variables: snake_case
signal_confidence = 0.85
entry_price = 2045.50
```

### Type Hints

```python
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime
from decimal import Decimal

# Always use type hints
def calculate_stop_loss(
    entry_price: Decimal,
    atr: Decimal,
    multiplier: float = 1.5
) -> Decimal:
    """Calculate stop loss based on ATR"""
    return entry_price - (atr * Decimal(str(multiplier)))

# Use Optional for nullable values
def find_signal(signal_id: str) -> Optional[TradingSignal]:
    """Find signal by ID"""
    pass

# Use Union for multiple types
def process_price(price: Union[float, Decimal]) -> Decimal:
    """Process price value"""
    if isinstance(price, float):
        return Decimal(str(price))
    return price
```

### Docstrings

```python
def analyze_market_structure(
    candles: List[Candle],
    timeframe: str
) -> MarketStructure:
    """
    Analyze market structure from candle data.
    
    Identifies swing highs/lows, trend direction, and structure breaks
    using Smart Money Concepts methodology.
    
    Args:
        candles: List of OHLC candles, minimum 200 required
        timeframe: Timeframe string (e.g., 'H1', 'M15')
    
    Returns:
        MarketStructure object containing:
            - trend: Current trend direction ('bullish', 'bearish', 'ranging')
            - swing_highs: List of swing high points
            - swing_lows: List of swing low points
            - last_break: Most recent structure break
    
    Raises:
        ValueError: If insufficient candles provided
        
    Example:
        >>> candles = fetch_candles('XAUUSD', 'H1', 200)
        >>> structure = analyze_market_structure(candles, 'H1')
        >>> print(structure.trend)
        'bullish'
    """
    if len(candles) < 200:
        raise ValueError("Minimum 200 candles required")
    
    # Implementation
    pass
```

### Error Handling

```python
# Use specific exceptions
class InsufficientDataError(Exception):
    """Raised when insufficient data for analysis"""
    pass

class InvalidSignalError(Exception):
    """Raised when signal validation fails"""
    pass

# Handle errors appropriately
def generate_signal(data: Dict) -> TradingSignal:
    """Generate trading signal"""
    try:
        # Validate data
        if not data.get('candles'):
            raise InsufficientDataError("No candle data provided")
        
        # Process
        signal = process_data(data)
        
        # Validate signal
        if not validate_signal(signal):
            raise InvalidSignalError("Signal failed validation")
        
        return signal
        
    except InsufficientDataError as e:
        logger.error("insufficient_data", error=str(e))
        raise
    except Exception as e:
        logger.error("signal_generation_failed", error=str(e))
        raise
```

### Logging

```python
import structlog

logger = structlog.get_logger()

# Use structured logging
logger.info("signal_generated",
    signal_id="XAU_001",
    instrument="XAUUSD",
    direction="BUY",
    confidence=0.85
)

# Include context
logger.error("database_error",
    operation="insert_signal",
    table="signals",
    error=str(e)
)

# Use appropriate levels
logger.debug("processing_candle", index=i)  # Verbose
logger.info("trade_opened", trade_id=123)   # Important events
logger.warning("high_volatility", atr=18.5) # Warnings
logger.error("connection_failed", host=host) # Errors
logger.critical("system_shutdown", reason=reason) # Critical
```

---

## Git Workflow

### Branch Strategy

```
main (production)
  ↓
develop (integration)
  ↓
feature/add-liquidity-sweep
feature/improve-fvg-detection
bugfix/fix-stop-loss-calculation
hotfix/critical-mt5-connection
```

### Branch Naming

```bash
# Features
feature/add-correlation-analysis
feature/implement-ml-enhancement

# Bug fixes
bugfix/fix-signal-validation
bugfix/correct-position-sizing

# Hotfixes
hotfix/critical-database-connection
hotfix/urgent-telegram-notification

# Improvements
improve/optimize-smc-calculation
improve/enhance-error-handling
```

### Commit Messages

```bash
# Format: <type>(<scope>): <subject>

# Types: feat, fix, docs, style, refactor, test, chore

# Good examples
git commit -m "feat(smc): add liquidity sweep detection"
git commit -m "fix(trading): correct stop loss calculation"
git commit -m "docs(api): update endpoint documentation"
git commit -m "refactor(analysis): optimize FVG detection"
git commit -m "test(signal): add confluence calculation tests"

# With body
git commit -m "feat(smc): implement order block detection

- Add order block identification algorithm
- Include volume and wick analysis
- Add tests for various market conditions
- Update documentation

Closes #123"
```

### Pull Request Process

```bash
# 1. Create feature branch
git checkout -b feature/add-liquidity-sweep

# 2. Make changes and commit
git add .
git commit -m "feat(smc): add liquidity sweep detection"

# 3. Push to remote
git push origin feature/add-liquidity-sweep

# 4. Create pull request on GitHub
# - Fill in PR template
# - Link related issues
# - Request reviewers

# 5. Address review comments
git add .
git commit -m "refactor: address review comments"
git push origin feature/add-liquidity-sweep

# 6. Merge after approval
# - Squash and merge for clean history
# - Delete branch after merge
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Related Issues
Closes #123
```

---

## Code Review Process

### Review Checklist

**Functionality**
- [ ] Code accomplishes intended purpose
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No obvious bugs

**Code Quality**
- [ ] Follows coding standards
- [ ] Clear and readable
- [ ] No code duplication
- [ ] Appropriate abstractions

**Testing**
- [ ] Adequate test coverage
- [ ] Tests are meaningful
- [ ] Tests pass

**Documentation**
- [ ] Code is well-commented
- [ ] Docstrings present
- [ ] README updated if needed

**Performance**
- [ ] No obvious performance issues
- [ ] Efficient algorithms used
- [ ] Database queries optimized

**Security**
- [ ] No security vulnerabilities
- [ ] Sensitive data protected
- [ ] Input validation present

### Review Comments

```python
# Good review comments

# Suggestion
# Consider using a dictionary for faster lookups:
# signal_map = {s.signal_id: s for s in signals}

# Question
# Why is the threshold set to 0.85? Should this be configurable?

# Issue
# This will fail if candles list is empty. Add validation:
# if not candles:
#     raise ValueError("Empty candles list")

# Praise
# Nice use of type hints and clear variable names!
```

---

## Testing Guidelines

### Test Structure

```python
# tests/unit/test_signal_generator.py
import pytest
from src.trading.signal_generator import SignalGenerator

class TestSignalGenerator:
    """Test suite for SignalGenerator"""
    
    @pytest.fixture
    def generator(self):
        """Create signal generator instance"""
        return SignalGenerator(
            confluence_threshold=80.0,
            min_risk_reward=2.0
        )
    
    def test_generate_signal_with_valid_setup(self, generator):
        """Test signal generation with valid setup"""
        # Arrange
        analysis = {
            'fvg': {'present': True, 'score': 30},
            'order_block': {'present': True, 'score': 25},
            'liquidity_sweep': {'present': True, 'score': 25}
        }
        
        # Act
        signal = generator.generate_signal(analysis)
        
        # Assert
        assert signal is not None
        assert signal.confidence >= 0.80
        assert signal.direction in ['BUY', 'SELL']
    
    def test_generate_signal_with_low_confluence(self, generator):
        """Test signal generation with low confluence"""
        # Arrange
        analysis = {
            'fvg': {'present': True, 'score': 20},
            'order_block': {'present': False, 'score': 0}
        }
        
        # Act
        signal = generator.generate_signal(analysis)
        
        # Assert
        assert signal is None
```

### Test Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Minimum coverage: 80%
# Critical modules: 90%+
```

---

## Documentation Standards

### Code Documentation

```python
# Module docstring
"""
Signal generation module.

This module contains the core logic for generating trading signals
based on Smart Money Concepts analysis.
"""

# Class docstring
class SignalGenerator:
    """
    Generates trading signals from market analysis.
    
    Attributes:
        confluence_threshold: Minimum confluence score
        min_risk_reward: Minimum R:R ratio
    """

# Method docstring
def calculate_confluence(self, analysis: Dict) -> float:
    """
    Calculate confluence score from analysis.
    
    Args:
        analysis: Dictionary containing SMC indicators
    
    Returns:
        Confluence score between 0 and 100
    """
```

### README Updates

```markdown
# Update README when:
- Adding new features
- Changing setup process
- Modifying configuration
- Adding dependencies
```

---

## Contribution Guidelines

### Getting Started

1. Fork the repository
2. Clone your fork
3. Create feature branch
4. Make changes
5. Write tests
6. Update documentation
7. Submit pull request

### Code of Conduct

- Be respectful and professional
- Provide constructive feedback
- Help others learn and grow
- Follow project guidelines

### Communication

- Use GitHub issues for bugs/features
- Use pull requests for code changes
- Use discussions for questions
- Tag maintainers when needed

---

## Best Practices

### 1. Keep Functions Small

```python
# Good: Single responsibility
def calculate_stop_loss(entry: Decimal, atr: Decimal) -> Decimal:
    """Calculate stop loss"""
    return entry - (atr * Decimal('1.5'))

# Bad: Multiple responsibilities
def process_signal(data):
    # Validates, calculates, saves, notifies...
    pass
```

### 2. Use Meaningful Names

```python
# Good
def calculate_position_size(account_balance, risk_percent):
    pass

# Bad
def calc_ps(ab, rp):
    pass
```

### 3. Avoid Magic Numbers

```python
# Good
CONFLUENCE_THRESHOLD = 80.0
MIN_RISK_REWARD = 2.0

if confluence >= CONFLUENCE_THRESHOLD:
    pass

# Bad
if confluence >= 80.0:
    pass
```

### 4. Handle Errors Gracefully

```python
# Good
try:
    signal = generate_signal(data)
except InsufficientDataError:
    logger.warning("insufficient_data")
    return None

# Bad
signal = generate_signal(data)  # May crash
```

### 5. Write Self-Documenting Code

```python
# Good
is_valid_setup = (
    has_fair_value_gap and
    has_order_block and
    confluence_score >= threshold
)

# Bad
x = a and b and c >= d
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05