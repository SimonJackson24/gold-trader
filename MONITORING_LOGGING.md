# Monitoring & Logging Guide

Comprehensive observability setup for the XAUUSD Gold Trading System.

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Logging Strategy](#logging-strategy)
3. [Metrics Collection](#metrics-collection)
4. [Alerting](#alerting)
5. [Dashboards](#dashboards)
6. [Log Analysis](#log-analysis)
7. [Performance Monitoring](#performance-monitoring)
8. [Troubleshooting with Logs](#troubleshooting-with-logs)

---

## Monitoring Overview

### Observability Pillars

1. **Logs**: What happened and when
2. **Metrics**: How the system is performing
3. **Traces**: How requests flow through the system

### Monitoring Stack

```
Application
    ↓
Prometheus (Metrics) + structlog (Logs) + Jaeger (Traces)
    ↓
Grafana (Visualization)
    ↓
Alertmanager (Alerts)
```

---

## Logging Strategy

### Log Levels

```python
import structlog

logger = structlog.get_logger()

# DEBUG: Detailed information for diagnosing problems
logger.debug("Analyzing candle", candle_index=i, timeframe="H1")

# INFO: General informational messages
logger.info("signal_generated", signal_id="XAU_001", confidence=0.85)

# WARNING: Warning messages for potentially harmful situations
logger.warning("high_volatility_detected", atr=18.5, threshold=15.0)

# ERROR: Error messages for serious problems
logger.error("database_connection_failed", error=str(e))

# CRITICAL: Critical messages for very serious problems
logger.critical("system_shutdown", reason="emergency_stop")
```

### Structured Logging

```python
# config/logging.yaml
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

### Log Format

```json
{
  "event": "signal_generated",
  "timestamp": "2024-01-05T14:30:00.123Z",
  "level": "info",
  "logger": "src.trading.signal_generator",
  "signal_id": "XAU_20240105_001",
  "instrument": "XAUUSD",
  "direction": "BUY",
  "confidence": 0.85,
  "confluence_score": 85,
  "request_id": "req_abc123",
  "user_id": "system"
}
```

### Contextual Logging

```python
# Add context to all logs in a request
from contextvars import ContextVar

request_id_var = ContextVar('request_id', default=None)

def log_with_context(**kwargs):
    """Add request context to logs"""
    context = {
        'request_id': request_id_var.get(),
        'timestamp': datetime.utcnow().isoformat()
    }
    context.update(kwargs)
    return context

# Usage
logger.info("processing_signal", **log_with_context(
    signal_id="XAU_001",
    action="validate"
))
```

### Log Rotation

```python
# config/logging.yaml
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/xauusd-trading/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
    formatter: json
```

---

## Metrics Collection

### Prometheus Setup

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary

# Counters
signals_generated = Counter(
    'signals_generated_total',
    'Total number of signals generated',
    ['instrument', 'direction']
)

trades_opened = Counter(
    'trades_opened_total',
    'Total number of trades opened',
    ['instrument', 'direction']
)

trades_closed = Counter(
    'trades_closed_total',
    'Total number of trades closed',
    ['instrument', 'outcome']  # win, loss, breakeven
)

# Gauges
active_trades = Gauge(
    'active_trades',
    'Number of currently active trades',
    ['instrument']
)

account_balance = Gauge(
    'account_balance_usd',
    'Current account balance in USD'
)

# Histograms
signal_confidence = Histogram(
    'signal_confidence_score',
    'Distribution of signal confidence scores',
    buckets=[0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
)

trade_duration = Histogram(
    'trade_duration_minutes',
    'Distribution of trade durations',
    buckets=[15, 30, 60, 120, 240, 480, 1440]
)

# Summary
profit_loss = Summary(
    'trade_profit_loss_usd',
    'Trade profit/loss in USD'
)
```

### Recording Metrics

```python
class SignalGenerator:
    def generate_signal(self, analysis):
        signal = self.evaluate_setup(analysis)
        
        if signal:
            # Record metric
            signals_generated.labels(
                instrument=signal.instrument,
                direction=signal.direction
            ).inc()
            
            signal_confidence.observe(signal.confidence_score)
            
            logger.info("signal_generated",
                signal_id=signal.signal_id,
                confidence=signal.confidence_score
            )
        
        return signal

class TradeManager:
    def close_trade(self, trade):
        # Record metrics
        outcome = 'win' if trade.profit_loss > 0 else 'loss'
        
        trades_closed.labels(
            instrument=trade.instrument,
            outcome=outcome
        ).inc()
        
        trade_duration.observe(trade.duration_minutes)
        profit_loss.observe(trade.profit_loss)
        
        # Update active trades gauge
        active_trades.labels(instrument=trade.instrument).dec()
```

### Custom Metrics

```python
# Business metrics
win_rate = Gauge(
    'trading_win_rate',
    'Current win rate percentage',
    ['instrument', 'timeframe']
)

average_rr = Gauge(
    'trading_average_risk_reward',
    'Average risk:reward ratio',
    ['instrument']
)

daily_pips = Counter(
    'trading_daily_pips_total',
    'Total pips gained/lost today',
    ['instrument']
)

# System metrics
websocket_connections = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections'
)

database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method', 'status']
)
```

---

## Alerting

### Alertmanager Configuration

```yaml
# monitoring/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'telegram'

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: 'YOUR_BOT_TOKEN'
        chat_id: YOUR_CHAT_ID
        parse_mode: 'HTML'
```

### Alert Rules

```yaml
# monitoring/alert_rules.yml
groups:
  - name: trading_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"
      
      # Database down
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "Database has been down for 1 minute"
      
      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
      
      # Low win rate
      - alert: LowWinRate
        expr: trading_win_rate < 0.40
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Win rate below 40%"
          description: "Current win rate: {{ $value }}%"
      
      # Large drawdown
      - alert: LargeDrawdown
        expr: trading_drawdown_percentage > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Drawdown exceeds 10%"
          description: "Current drawdown: {{ $value }}%"
      
      # MT5 disconnected
      - alert: MT5Disconnected
        expr: mt5_connection_status == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MT5 connection lost"
          description: "MT5 has been disconnected for 2 minutes"
```

### Telegram Alerts

```python
# src/monitoring/alerting.py
import asyncio
from telegram import Bot

class AlertManager:
    def __init__(self):
        self.bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        self.alert_channel = os.getenv("TELEGRAM_ALERT_CHANNEL")
    
    async def send_alert(self, severity, title, message):
        """Send alert to Telegram"""
        emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        alert_text = f"""
{emoji[severity]} **{severity.upper()} ALERT**

**{title}**

{message}

Time: {datetime.utcnow().isoformat()}
"""
        
        await self.bot.send_message(
            chat_id=self.alert_channel,
            text=alert_text,
            parse_mode='Markdown'
        )
    
    async def alert_high_drawdown(self, drawdown_pct):
        """Alert on high drawdown"""
        await self.send_alert(
            severity='critical',
            title='High Drawdown Detected',
            message=f'Current drawdown: {drawdown_pct:.2f}%\n'
                   f'Consider reducing position sizes or pausing trading.'
        )
    
    async def alert_system_error(self, error_type, error_message):
        """Alert on system errors"""
        await self.send_alert(
            severity='critical',
            title=f'System Error: {error_type}',
            message=f'Error: {error_message}\n'
                   f'Check logs for details.'
        )
```

---

## Dashboards

### Grafana Dashboard Setup

```json
{
  "dashboard": {
    "title": "XAUUSD Trading System",
    "panels": [
      {
        "title": "Active Trades",
        "targets": [
          {
            "expr": "active_trades{instrument='XAUUSD'}"
          }
        ]
      },
      {
        "title": "Win Rate",
        "targets": [
          {
            "expr": "trading_win_rate{instrument='XAUUSD'}"
          }
        ]
      },
      {
        "title": "Daily P/L",
        "targets": [
          {
            "expr": "sum(rate(trade_profit_loss_usd_sum[24h]))"
          }
        ]
      },
      {
        "title": "Signal Confidence Distribution",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, signal_confidence_score_bucket)"
          }
        ]
      }
    ]
  }
}
```

### Key Dashboards

1. **Trading Overview**
   - Active trades
   - Win rate
   - Daily P/L
   - Total pips

2. **System Health**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network traffic

3. **Performance Metrics**
   - API response times
   - Database query times
   - WebSocket latency
   - Error rates

4. **Business Metrics**
   - Signals generated
   - Trades opened/closed
   - Average R:R
   - Drawdown

---

## Log Analysis

### Log Aggregation

```bash
# Using Loki for log aggregation
docker run -d \
  --name=loki \
  -p 3100:3100 \
  grafana/loki:latest

# Configure Promtail to ship logs
docker run -d \
  --name=promtail \
  -v /var/log:/var/log \
  -v ./promtail-config.yml:/etc/promtail/config.yml \
  grafana/promtail:latest
```

### Log Queries

```
# Find all errors in last hour
{job="analysis-server"} |= "ERROR" | json

# Find slow database queries
{job="analysis-server"} | json | duration > 1s

# Find failed trades
{job="analysis-server"} | json | event="trade_closed" | outcome="loss"

# Find high confidence signals
{job="analysis-server"} | json | event="signal_generated" | confidence > 0.85
```

### Log Analysis Scripts

```python
# scripts/analyze_logs.py
import json
from collections import Counter

def analyze_error_patterns(log_file):
    """Analyze error patterns in logs"""
    errors = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if log.get('level') == 'error':
                    errors.append(log.get('event'))
            except json.JSONDecodeError:
                continue
    
    # Count error types
    error_counts = Counter(errors)
    
    print("Top 10 errors:")
    for error, count in error_counts.most_common(10):
        print(f"{error}: {count}")

def analyze_signal_performance(log_file):
    """Analyze signal generation performance"""
    signals = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if log.get('event') == 'signal_generated':
                    signals.append(log)
            except json.JSONDecodeError:
                continue
    
    # Calculate statistics
    confidences = [s['confidence'] for s in signals]
    avg_confidence = sum(confidences) / len(confidences)
    
    print(f"Total signals: {len(signals)}")
    print(f"Average confidence: {avg_confidence:.2f}")
```

---

## Performance Monitoring

### Application Performance Monitoring (APM)

```python
# src/monitoring/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

tracer = trace.get_tracer(__name__)

# Use in code
class SignalGenerator:
    def generate_signal(self, analysis):
        with tracer.start_as_current_span("generate_signal"):
            with tracer.start_as_current_span("calculate_confluence"):
                confluence = self.calculate_confluence(analysis)
            
            with tracer.start_as_current_span("validate_setup"):
                if self.validate_setup(confluence):
                    return self.create_signal(confluence)
```

### Database Query Monitoring

```python
# Monitor slow queries
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    if total > 1.0:  # Log slow queries (>1 second)
        logger.warning("slow_query",
            duration=total,
            query=statement[:100]
        )
    
    database_query_duration.labels(query_type="select").observe(total)
```

---

## Troubleshooting with Logs

### Common Log Patterns

```bash
# Find all errors
grep "ERROR" /var/log/xauusd-trading/app.log

# Find specific signal
grep "XAU_20240105_001" /var/log/xauusd-trading/app.log

# Find database errors
grep "database" /var/log/xauusd-trading/app.log | grep "ERROR"

# Find slow operations
jq 'select(.duration > 1)' /var/log/xauusd-trading/app.log

# Count errors by type
jq -r 'select(.level=="error") | .event' /var/log/xauusd-trading/app.log | sort | uniq -c
```

### Log Correlation

```python
# Correlate logs across services
def trace_request(request_id):
    """Trace a request across all services"""
    logs = []
    
    # Search all log files
    for log_file in ['/var/log/analysis-server.log', '/var/log/mt5-connector.log']:
        with open(log_file) as f:
            for line in f:
                log = json.loads(line)
                if log.get('request_id') == request_id:
                    logs.append(log)
    
    # Sort by timestamp
    logs.sort(key=lambda x: x['timestamp'])
    
    return logs
```

---

## Best Practices

### 1. Log What Matters

```python
# Good: Actionable information
logger.info("signal_generated",
    signal_id="XAU_001",
    confidence=0.85,
    entry_price=2045.50
)

# Bad: Too verbose
logger.debug("Processing candle 1 of 200...")
```

### 2. Use Structured Logging

```python
# Good: Structured
logger.info("trade_closed",
    trade_id=123,
    profit_loss=250.00,
    duration_minutes=105
)

# Bad: Unstructured
logger.info(f"Trade {trade_id} closed with P/L ${profit_loss}")
```

### 3. Include Context

```python
# Good: With context
logger.error("database_connection_failed",
    error=str(e),
    host=db_host,
    database=db_name,
    retry_attempt=attempt
)

# Bad: No context
logger.error("Database error")
```

### 4. Monitor Key Metrics

- Win rate
- Average R:R
- Drawdown
- System uptime
- Error rate
- Response times

### 5. Set Up Alerts

- Critical: System down, large drawdown
- Warning: High error rate, low win rate
- Info: Daily reports, system updates

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05