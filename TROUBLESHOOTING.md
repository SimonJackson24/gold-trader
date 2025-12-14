# Troubleshooting Guide

Common issues and solutions for the XAUUSD Gold Trading System.

## Table of Contents

1. [System Won't Start](#system-wont-start)
2. [MT5 Connection Issues](#mt5-connection-issues)
3. [Database Problems](#database-problems)
4. [Telegram Bot Issues](#telegram-bot-issues)
5. [WebSocket Connection Problems](#websocket-connection-problems)
6. [Trading Signal Issues](#trading-signal-issues)
7. [Performance Problems](#performance-problems)
8. [Docker Issues](#docker-issues)
9. [API Errors](#api-errors)
10. [Logging and Debugging](#logging-and-debugging)

---

## System Won't Start

### Problem: Docker containers won't start

**Symptoms:**
```bash
docker-compose up -d
# Containers exit immediately
```

**Solutions:**

1. **Check Docker logs:**
```bash
docker-compose logs
docker-compose logs analysis-server
```

2. **Check disk space:**
```bash
df -h
# If disk is full, clean up
docker system prune -a
```

3. **Check memory:**
```bash
free -h
# If low memory, increase swap or upgrade server
```

4. **Verify environment variables:**
```bash
# Check .env file exists and is valid
cat .env | grep -v '^#' | grep -v '^$'
```

5. **Rebuild containers:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problem: Services crash on startup

**Check logs for specific errors:**
```bash
# Analysis server logs
docker-compose logs -f analysis-server

# Common errors and fixes:
# - "ModuleNotFoundError": pip install -r requirements.txt
# - "Connection refused": Check database/redis is running
# - "Permission denied": Check file permissions
```

---

## MT5 Connection Issues

### Problem: Cannot connect to MT5

**Symptoms:**
- "MT5 initialization failed"
- "Invalid account credentials"
- "Connection timeout"

**Solutions:**

1. **Verify MT5 is running:**
```cmd
# On Windows, check Task Manager
# MT5 terminal should be running
```

2. **Check credentials:**
```yaml
# config/mt5_config.yaml
mt5:
  login: 12345678  # Correct account number?
  password: "..."  # Correct password?
  server: "BrokerName-Demo"  # Correct server name?
```

3. **Test MT5 connection:**
```python
import MetaTrader5 as mt5

if not mt5.initialize():
    print("MT5 initialization failed")
    print(mt5.last_error())
else:
    print("MT5 initialized successfully")
    print(f"Version: {mt5.version()}")
    mt5.shutdown()
```

4. **Check firewall:**
```cmd
# Windows Firewall might be blocking MT5
# Add exception for MT5 terminal
```

5. **Verify symbol availability:**
```python
import MetaTrader5 as mt5

mt5.initialize()
symbol_info = mt5.symbol_info("XAUUSD")
if symbol_info is None:
    print("XAUUSD not found")
    # Enable symbol in Market Watch
else:
    print(f"XAUUSD available: {symbol_info}")
```

### Problem: MT5 connector keeps disconnecting

**Solutions:**

1. **Check network stability:**
```bash
# Ping broker server
ping broker-server.com

# Check for packet loss
```

2. **Increase timeout:**
```yaml
# config/mt5_config.yaml
mt5:
  timeout: 120000  # Increase from 60000
```

3. **Implement reconnection logic:**
```python
class MT5Connector:
    def connect_with_retry(self, max_retries=5):
        for attempt in range(max_retries):
            if mt5.initialize():
                return True
            time.sleep(2 ** attempt)  # Exponential backoff
        return False
```

---

## Database Problems

### Problem: Cannot connect to database

**Symptoms:**
- "Connection refused"
- "Authentication failed"
- "Database does not exist"

**Solutions:**

1. **Check PostgreSQL is running:**
```bash
docker-compose ps postgres
# Should show "Up"

# If not running:
docker-compose up -d postgres
```

2. **Verify credentials:**
```bash
# Test connection
docker-compose exec postgres psql -U trader -d xauusd_trading

# If fails, check .env file
grep DATABASE .env
```

3. **Check database exists:**
```bash
docker-compose exec postgres psql -U trader -l
# Should list xauusd_trading database
```

4. **Reset database:**
```bash
# Backup first!
docker-compose exec postgres pg_dump -U trader xauusd_trading > backup.sql

# Drop and recreate
docker-compose exec postgres psql -U trader -c "DROP DATABASE xauusd_trading;"
docker-compose exec postgres psql -U trader -c "CREATE DATABASE xauusd_trading;"

# Run migrations
docker-compose exec analysis-server alembic upgrade head
```

### Problem: Database queries are slow

**Solutions:**

1. **Check indexes:**
```sql
-- List indexes
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public';

-- Create missing indexes
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
```

2. **Analyze query performance:**
```sql
EXPLAIN ANALYZE 
SELECT * FROM signals WHERE instrument = 'XAUUSD';
```

3. **Vacuum database:**
```bash
docker-compose exec postgres psql -U trader -d xauusd_trading -c "VACUUM ANALYZE;"
```

4. **Check connections:**
```sql
SELECT count(*) FROM pg_stat_activity;
-- If too many, increase pool size or close idle connections
```

---

## Telegram Bot Issues

### Problem: Bot not sending messages

**Symptoms:**
- No messages in Telegram channel
- "Unauthorized" error
- "Chat not found" error

**Solutions:**

1. **Verify bot token:**
```bash
# Test bot token
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe

# Should return bot information
```

2. **Check channel ID:**
```python
# Get channel ID
import asyncio
from telegram import Bot

async def get_updates():
    bot = Bot(token="YOUR_BOT_TOKEN")
    updates = await bot.get_updates()
    for update in updates:
        print(update)

asyncio.run(get_updates())
```

3. **Verify bot is admin:**
```
# In Telegram:
# 1. Go to channel
# 2. Channel Info → Administrators
# 3. Ensure bot is listed with "Post messages" permission
```

4. **Test message sending:**
```python
import asyncio
from telegram import Bot

async def test_send():
    bot = Bot(token="YOUR_BOT_TOKEN")
    await bot.send_message(
        chat_id="YOUR_CHANNEL_ID",
        text="Test message"
    )

asyncio.run(test_send())
```

### Problem: Messages not formatting correctly

**Solutions:**

1. **Check parse mode:**
```python
# Use Markdown or HTML
await bot.send_message(
    chat_id=channel_id,
    text="**Bold** _italic_",
    parse_mode="Markdown"
)
```

2. **Escape special characters:**
```python
def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)
```

---

## WebSocket Connection Problems

### Problem: WebSocket won't connect

**Symptoms:**
- "Connection refused"
- "SSL handshake failed"
- "Connection timeout"

**Solutions:**

1. **Check WebSocket server:**
```bash
# Check if server is listening
netstat -tulpn | grep 8765

# Test connection
wscat -c ws://localhost:8765
```

2. **Verify SSL certificates:**
```bash
# Check certificate validity
openssl x509 -in cert.pem -noout -dates

# Test SSL connection
openssl s_client -connect localhost:8765
```

3. **Check firewall:**
```bash
# Ensure port 8765 is open
sudo ufw status
sudo ufw allow 8765/tcp
```

4. **Test with simple client:**
```python
import asyncio
import websockets

async def test_connection():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        await websocket.send("ping")
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_connection())
```

---

## Trading Signal Issues

### Problem: No signals being generated

**Symptoms:**
- System running but no signals
- Telegram channel empty
- Database has no new signals

**Solutions:**

1. **Check market data:**
```bash
# Verify price data is being received
docker-compose logs -f analysis-server | grep "price_tick"
```

2. **Lower confluence threshold:**
```yaml
# config/smc_parameters.yaml
signals:
  min_confluence_score: 70  # Lower from 80
```

3. **Check timeframe data:**
```python
# Verify candles are being created
from src.core.market_data_processor import MarketDataProcessor

processor = MarketDataProcessor()
print(f"M15 candles: {len(processor.m15_window.data)}")
print(f"H1 candles: {len(processor.h1_window.data)}")
print(f"H4 candles: {len(processor.h4_window.data)}")
```

4. **Enable debug logging:**
```bash
# .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart analysis-server
```

### Problem: Too many false signals

**Solutions:**

1. **Increase confluence threshold:**
```yaml
signals:
  min_confluence_score: 85  # Increase from 80
```

2. **Adjust SMC parameters:**
```yaml
fvg:
  min_size_pips: 7  # Increase from 5
  strength_threshold: 0.8  # Increase from 0.7

order_blocks:
  quality_threshold: 80  # Increase from 70
```

3. **Add filters:**
```python
# Filter by session
if signal.session not in ['LONDON', 'NY_OVERLAP']:
    return None  # Skip Asian session

# Filter by volatility
if current_atr > high_volatility_threshold:
    return None  # Skip high volatility
```

---

## Performance Problems

### Problem: System is slow

**Solutions:**

1. **Check resource usage:**
```bash
# CPU and memory
docker stats

# Disk I/O
iostat -x 1

# If high, optimize or upgrade server
```

2. **Optimize database queries:**
```sql
-- Add indexes
CREATE INDEX idx_trades_entry_time ON trades(entry_time DESC);

-- Analyze slow queries
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

3. **Increase resources:**
```yaml
# docker-compose.yml
services:
  analysis-server:
    deploy:
      resources:
        limits:
          cpus: '4'  # Increase from 2
          memory: 4G  # Increase from 2G
```

4. **Enable caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_swing_points(candle_hash):
    # Expensive calculation
    pass
```

### Problem: High memory usage

**Solutions:**

1. **Check for memory leaks:**
```python
import tracemalloc

tracemalloc.start()
# Run code
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

2. **Limit data retention:**
```python
# Keep only recent data
class RollingWindow:
    def __init__(self, size=200):  # Reduce from 500
        self.data = deque(maxlen=size)
```

3. **Clear old data:**
```sql
-- Delete old price history
DELETE FROM price_history 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

---

## Docker Issues

### Problem: Container keeps restarting

**Check restart reason:**
```bash
docker inspect <container_id> | grep -A 10 State
```

**Common causes:**

1. **Application crash:**
```bash
# Check logs
docker-compose logs --tail=100 analysis-server
```

2. **Health check failing:**
```yaml
# Adjust health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 60s  # Increase from 30s
  timeout: 10s
  retries: 5  # Increase from 3
```

3. **Resource limits:**
```yaml
# Increase limits
deploy:
  resources:
    limits:
      memory: 4G  # Increase
```

### Problem: Cannot remove containers

**Solutions:**
```bash
# Force remove
docker-compose down -v --remove-orphans

# If still stuck
docker rm -f $(docker ps -aq)

# Clean everything
docker system prune -a --volumes
```

---

## API Errors

### Problem: 401 Unauthorized

**Solutions:**

1. **Check authentication:**
```bash
# Verify token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/signals
```

2. **Generate new token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### Problem: 500 Internal Server Error

**Solutions:**

1. **Check server logs:**
```bash
docker-compose logs -f analysis-server
```

2. **Enable debug mode:**
```bash
# .env
DEBUG=true
```

3. **Check database connection:**
```python
# Test database
from src.database import engine
engine.connect()
```

---

## Logging and Debugging

### Enable Debug Logging

```bash
# .env
LOG_LEVEL=DEBUG

# Restart
docker-compose restart
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f analysis-server

# Last 100 lines
docker-compose logs --tail=100 analysis-server

# Follow with grep
docker-compose logs -f | grep ERROR
```

### Debug Python Code

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb
import ipdb; ipdb.set_trace()

# Remote debugging
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
analyze_market_data()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Review system logs
3. Search GitHub issues
4. Check documentation

### When Reporting Issues

Include:
- System information (OS, Docker version)
- Error messages (full stack trace)
- Steps to reproduce
- Configuration (sanitized)
- Logs (relevant sections)

### Support Channels

- GitHub Issues: [repository-url]/issues
- Email: support@example.com
- Discord: [invite-link]

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05