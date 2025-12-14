# Configuration Guide

Complete guide to configuring the XAUUSD Gold Trading System.

## Configuration Files

The system uses multiple configuration files for different aspects:

1. **`.env`** - Environment variables (credentials, secrets)
2. **`config/instruments.yaml`** - Instrument-specific parameters
3. **`config/smc_parameters.yaml`** - SMC algorithm parameters
4. **`config/risk_management.yaml`** - Risk management rules
5. **`config/sessions.yaml`** - Trading session configuration
6. **`docker-compose.yml`** - Service configuration

---

## Environment Variables (.env)

See [`.env.example`](.env.example) for complete list. Key variables:

### Database Configuration
```bash
DATABASE_URL=postgresql://trader:password@localhost:5432/xauusd_trading
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Telegram Configuration
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=-1001234567890
```

### Trading Configuration
```bash
RISK_PER_TRADE=1.0
MAX_CONCURRENT_TRADES=2
MIN_RISK_REWARD=2.0
```

---

## Instrument Configuration

**File:** `config/instruments.yaml`

```yaml
instruments:
  XAUUSD:
    enabled: true
    
    # Timeframes to analyze
    timeframes:
      - M15
      - H1
      - H4
    
    # Risk management
    risk_per_trade: 1.0  # Percentage
    max_concurrent_trades: 2
    max_daily_loss: 5.0  # Percentage
    
    # Position sizing
    min_position_size: 0.01  # Lots
    max_position_size: 1.0   # Lots
    
    # Spread limits
    max_spread: 2.0  # Pips
    
    # Telegram
    telegram_channel_id: "-1001234567890"
    
    # SMC Parameters (instrument-specific)
    smc_parameters:
      fvg_min_size_pips: 5
      ob_lookback_candles: 20
      liquidity_sweep_threshold: 5
      confluence_threshold: 80
    
    # Session-specific settings
    sessions:
      asian:
        enabled: true
        risk_multiplier: 0.5
      london:
        enabled: true
        risk_multiplier: 1.0
      ny_overlap:
        enabled: true
        risk_multiplier: 1.5
```

---

## SMC Parameters Configuration

**File:** `config/smc_parameters.yaml`

```yaml
# Fair Value Gap (FVG) Detection
fvg:
  min_size_pips: 5
  max_age_candles: 50
  strength_threshold: 0.7
  volume_multiplier: 1.5

# Order Block Detection
order_blocks:
  lookback_candles: 20
  min_volume_multiplier: 2.0
  min_wick_ratio: 0.6
  round_number_threshold: 10
  quality_threshold: 70

# Liquidity Analysis
liquidity:
  sweep_threshold_pips: 5
  pool_min_size: 3
  reversal_confirmation_candles: 3

# Market Structure
structure:
  swing_lookback: 10
  min_move_pips: 20
  confirmation_candles: 2
  trend_strength_threshold: 0.7

# Signal Generation
signals:
  min_confluence_score: 80
  h4_weight: 0.4
  h1_weight: 0.35
  m15_weight: 0.25
  min_risk_reward: 2.0
```

---

## Risk Management Configuration

**File:** `config/risk_management.yaml`

```yaml
# Position Sizing
position_sizing:
  method: "fixed_percentage"  # fixed_percentage, kelly_criterion, optimal_f
  base_risk_percentage: 1.0
  max_risk_percentage: 2.0
  min_position_size: 0.01
  max_position_size: 1.0

# Risk Limits
risk_limits:
  max_concurrent_trades: 2
  max_daily_loss_percentage: 5.0
  max_weekly_loss_percentage: 10.0
  max_monthly_loss_percentage: 20.0
  max_drawdown_percentage: 15.0

# Trade Management
trade_management:
  partial_close_enabled: true
  tp1_percentage: 50  # Close 50% at TP1
  tp2_percentage: 50  # Close 50% at TP2
  breakeven_after_tp1: true
  trailing_stop_enabled: false

# Stop Loss Rules
stop_loss:
  method: "structure_based"  # structure_based, atr_based, fixed_pips
  atr_multiplier: 1.5
  min_stop_loss_pips: 10
  max_stop_loss_pips: 100
  buffer_pips: 5

# Take Profit Rules
take_profit:
  tp1_multiplier: 1.5  # 1.5x risk
  tp2_multiplier: 3.0  # 3x risk
  use_structure_targets: true
```

---

## Session Configuration

**File:** `config/sessions.yaml`

```yaml
sessions:
  asian:
    name: "Asian Session"
    start_time: "00:00"  # UTC
    end_time: "08:00"
    enabled: true
    risk_multiplier: 0.5
    max_trades: 1
    strategy: "range"
    
  london:
    name: "London Session"
    start_time: "08:00"
    end_time: "13:00"
    enabled: true
    risk_multiplier: 1.0
    max_trades: 2
    strategy: "trend"
    
  ny_overlap:
    name: "NY Overlap"
    start_time: "13:00"
    end_time: "17:00"
    enabled: true
    risk_multiplier: 1.5
    max_trades: 2
    strategy: "aggressive"
    
  ny_close:
    name: "NY Close"
    start_time: "17:00"
    end_time: "23:59"
    enabled: false
    risk_multiplier: 0.5
    max_trades: 1
    strategy: "conservative"
```

---

## Volatility Configuration

**File:** `config/volatility.yaml`

```yaml
volatility:
  # ATR Settings
  atr_period: 14
  atr_high_threshold: 15  # Pips
  atr_low_threshold: 5    # Pips
  
  # Volatility Regimes
  regimes:
    low:
      threshold: 0.7  # Relative to average
      strategy: "breakout"
      risk_multiplier: 1.2
      
    normal:
      threshold: 1.3
      strategy: "standard"
      risk_multiplier: 1.0
      
    high:
      threshold: 1.3
      strategy: "reversal"
      risk_multiplier: 0.7
  
  # Adjustments
  adjustments:
    stop_loss_multiplier: true
    position_size_adjustment: true
    confluence_threshold_increase: true
```

---

## News Filter Configuration

**File:** `config/news_filter.yaml`

```yaml
news_filter:
  enabled: true
  
  # High Impact Events
  high_impact_events:
    - "FOMC"
    - "NFP"
    - "CPI"
    - "GDP"
    - "Interest Rate Decision"
    - "Powell Speech"
    - "Yellen Speech"
  
  # Pause Trading Windows
  pause_before_minutes: 30
  pause_after_minutes: 30
  
  # Trade With News (experimental)
  trade_with_news: false
  news_direction_threshold: 0.8
  
  # API Configuration
  calendar_api:
    provider: "forexfactory"  # forexfactory, investing, fxstreet
    api_key: ""
    update_interval: 3600  # 1 hour
```

---

## Notification Configuration

**File:** `config/notifications.yaml`

```yaml
notifications:
  telegram:
    enabled: true
    
    # Message Types
    notify_on_signal: true
    notify_on_trade_open: true
    notify_on_trade_close: true
    notify_on_tp_hit: true
    notify_on_sl_hit: true
    notify_on_error: true
    notify_on_system_event: true
    
    # Reports
    daily_report:
      enabled: true
      time: "00:00"  # UTC
    
    weekly_report:
      enabled: true
      day: "sunday"
      time: "20:00"
    
    monthly_report:
      enabled: true
      day: 1
      time: "00:00"
    
    # Message Format
    include_chart: true
    include_analysis: true
    use_emojis: true
    parse_mode: "Markdown"
```

---

## Logging Configuration

**File:** `config/logging.yaml`

```yaml
logging:
  version: 1
  
  formatters:
    json:
      class: pythonjsonlogger.jsonlogger.JsonFormatter
      format: "%(asctime)s %(name)s %(levelname)s %(message)s"
    
    standard:
      format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: standard
      stream: ext://sys.stdout
    
    file:
      class: logging.handlers.RotatingFileHandler
      level: DEBUG
      formatter: json
      filename: /var/log/xauusd-trading/app.log
      maxBytes: 10485760  # 10MB
      backupCount: 10
    
    error_file:
      class: logging.handlers.RotatingFileHandler
      level: ERROR
      formatter: json
      filename: /var/log/xauusd-trading/error.log
      maxBytes: 10485760
      backupCount: 10
  
  loggers:
    root:
      level: INFO
      handlers: [console, file, error_file]
    
    src.analysis:
      level: DEBUG
      handlers: [file]
      propagate: false
    
    src.trading:
      level: DEBUG
      handlers: [file]
      propagate: false
```

---

## Configuration Best Practices

### 1. Environment-Specific Configurations

```bash
# Development
.env.development
config/development/

# Staging
.env.staging
config/staging/

# Production
.env.production
config/production/
```

### 2. Configuration Validation

```python
from pydantic import BaseSettings, validator

class TradingConfig(BaseSettings):
    risk_per_trade: float
    max_concurrent_trades: int
    
    @validator('risk_per_trade')
    def validate_risk(cls, v):
        if not 0.1 <= v <= 5.0:
            raise ValueError('Risk must be between 0.1% and 5%')
        return v
    
    class Config:
        env_file = '.env'
```

### 3. Hot Reload Configuration

```python
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            self.reload_config(event.src_path)
```

### 4. Configuration Hierarchy

```
1. Default values (in code)
2. Configuration files (YAML)
3. Environment variables (.env)
4. Command-line arguments
5. Runtime updates (via API)
```

### 5. Sensitive Data

```bash
# Never commit to git
.env
config/secrets.yaml

# Use environment variables for:
- API keys
- Passwords
- Tokens
- Private keys
```

---

## Configuration Examples

### Conservative Setup
```yaml
# For beginners or small accounts
risk_per_trade: 0.5
max_concurrent_trades: 1
min_risk_reward: 3.0
confluence_threshold: 85
```

### Aggressive Setup
```yaml
# For experienced traders with larger accounts
risk_per_trade: 2.0
max_concurrent_trades: 3
min_risk_reward: 2.0
confluence_threshold: 75
```

### Scalping Setup
```yaml
# For high-frequency trading
timeframes: [M1, M5, M15]
risk_per_trade: 0.5
max_concurrent_trades: 5
min_risk_reward: 1.5
```

---

## Dynamic Configuration Updates

### Via API
```bash
curl -X PUT http://localhost:8000/api/v1/config \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "risk_per_trade": 1.5,
    "max_concurrent_trades": 3
  }'
```

### Via Database
```sql
UPDATE system_config 
SET value = '1.5' 
WHERE key = 'risk_per_trade';
```

### Via File Watch
```python
# Automatically reload when config files change
observer = Observer()
observer.schedule(ConfigReloader(), path='./config', recursive=True)
observer.start()
```

---

## Configuration Backup

```bash
# Backup all configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  .env \
  config/ \
  docker-compose.yml

# Restore configuration
tar -xzf config_backup_20240105.tar.gz
```

---

## Troubleshooting Configuration

### Check Current Configuration
```bash
# View loaded configuration
docker-compose exec analysis-server python -c "
from src.core.config import settings
print(settings.dict())
"
```

### Validate Configuration
```bash
# Run validation script
python scripts/validate_config.py
```

### Reset to Defaults
```bash
# Copy default configuration
cp config/defaults/* config/
cp .env.example .env
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05