# Setup Guide

Complete step-by-step guide to set up the XAUUSD Gold Trading System from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MT5 Account Setup](#mt5-account-setup)
3. [Telegram Bot Creation](#telegram-bot-creation)
4. [VPS Server Setup](#vps-server-setup)
5. [Windows MT5 Connector Setup](#windows-mt5-connector-setup)
6. [Linux Analysis Server Setup](#linux-analysis-server-setup)
7. [Database Configuration](#database-configuration)
8. [Initial Testing](#initial-testing)
9. [Going Live](#going-live)

---

## Prerequisites

### Required Accounts
- [ ] MetaTrader 5 broker account (demo or live)
- [ ] Telegram account
- [ ] VPS server (Ubuntu 20.04+ or Debian 11+)
- [ ] Domain name (optional, for SSL)

### Required Software
- [ ] Windows 10/11 (for MT5 connector)
- [ ] MetaTrader 5 terminal
- [ ] Python 3.11 or higher
- [ ] Git
- [ ] SSH client (PuTTY for Windows, built-in for Linux/Mac)

### Required Knowledge
- Basic command line usage
- Basic understanding of trading concepts
- Familiarity with configuration files

---

## MT5 Account Setup

### Step 1: Choose a Broker

Select a broker that supports:
- ✅ MetaTrader 5 platform
- ✅ XAUUSD (Gold) trading
- ✅ API access for automated trading
- ✅ Good execution speed and low spreads

**Recommended Brokers** (for demo/testing):
- IC Markets
- Pepperstone
- FP Markets
- Admiral Markets

### Step 2: Create MT5 Account

1. **Visit broker's website**
   - Navigate to account registration
   - Choose "MetaTrader 5" account type

2. **Select account type**
   - **Demo Account** (recommended for initial testing)
     - No real money risk
     - Full platform features
     - Unlimited practice time
   
   - **Live Account** (after successful testing)
     - Real money trading
     - Requires identity verification
     - Minimum deposit varies by broker

3. **Account Configuration**
   ```
   Account Type: Standard or Raw Spread
   Leverage: 1:100 or 1:500 (for gold trading)
   Base Currency: USD
   Initial Balance: $10,000 (demo) or your deposit (live)
   ```

4. **Save Account Credentials**
   ```
   Login: 12345678
   Password: YourSecurePassword123!
   Server: BrokerName-Demo or BrokerName-Live
   ```

### Step 3: Install MetaTrader 5

1. **Download MT5**
   - Visit your broker's website
   - Download MT5 for Windows
   - Or download from [MetaQuotes](https://www.metatrader5.com/en/download)

2. **Install MT5**
   ```
   Run the installer: mt5setup.exe
   Follow installation wizard
   Default location: C:\Program Files\MetaTrader 5
   ```

3. **Login to MT5**
   - Open MT5 terminal
   - File → Login to Trade Account
   - Enter your credentials
   - Select server from dropdown
   - Click "Login"

4. **Verify XAUUSD Symbol**
   - View → Market Watch (Ctrl+M)
   - Right-click → Symbols
   - Search for "XAUUSD" or "GOLD"
   - Enable the symbol
   - Verify you see live prices

### Step 4: Enable Algo Trading

1. **Configure MT5 for API Access**
   ```
   Tools → Options → Expert Advisors
   ✅ Allow automated trading
   ✅ Allow DLL imports
   ✅ Allow WebRequest for listed URL
   ```

2. **Add Allowed URLs** (if needed)
   ```
   https://your-vps-server.com
   wss://your-vps-server.com
   ```

3. **Test Connection**
   - Open a chart (XAUUSD, any timeframe)
   - Verify real-time price updates
   - Check connection status (bottom right corner)

---

## Telegram Bot Creation

### Step 1: Create Bot with BotFather

1. **Open Telegram**
   - Search for `@BotFather`
   - Start conversation

2. **Create New Bot**
   ```
   Send: /newbot
   
   BotFather: Alright, a new bot. How are we going to call it?
   You: XAUUSD Gold Trading Signals
   
   BotFather: Good. Now let's choose a username for your bot.
   You: xauusd_gold_trader_bot
   
   BotFather: Done! Congratulations on your new bot.
   ```

3. **Save Bot Token**
   ```
   Bot Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   ⚠️ **IMPORTANT**: Keep this token secret! Anyone with this token can control your bot.

4. **Configure Bot Settings**
   ```
   Send: /setdescription
   Select your bot
   Enter: Automated XAUUSD trading signals using Smart Money Concepts
   
   Send: /setabouttext
   Select your bot
   Enter: Professional gold trading signals with real-time updates
   
   Send: /setuserpic
   Select your bot
   Upload a logo/image for your bot
   ```

### Step 2: Create Telegram Channel

1. **Create Channel**
   - Open Telegram
   - Menu → New Channel
   - Channel Name: `XAUUSD Gold Signals`
   - Description: `Professional XAUUSD trading signals`
   - Type: Public or Private (your choice)

2. **Add Bot as Administrator**
   - Open your channel
   - Channel Info → Administrators
   - Add Administrator
   - Search for your bot username
   - Grant permissions:
     - ✅ Post messages
     - ✅ Edit messages
     - ✅ Delete messages

3. **Get Channel ID**

   **Method 1: Using Web Telegram**
   ```
   1. Open https://web.telegram.org
   2. Open your channel
   3. Look at URL: https://web.telegram.org/z/#-1001234567890
   4. Channel ID: -1001234567890
   ```

   **Method 2: Using Bot**
   ```python
   # Temporary script to get channel ID
   import asyncio
   from telegram import Bot
   
   async def get_channel_id():
       bot = Bot(token="YOUR_BOT_TOKEN")
       # Forward any message from your channel to the bot
       # Then run this to see updates
       updates = await bot.get_updates()
       for update in updates:
           print(update)
   
   asyncio.run(get_channel_id())
   ```

4. **Test Bot Posting**
   ```python
   # Test script
   import asyncio
   from telegram import Bot
   
   async def test_post():
       bot = Bot(token="YOUR_BOT_TOKEN")
       await bot.send_message(
           chat_id="-1001234567890",
           text="🔔 Test message from XAUUSD Trading Bot"
       )
   
   asyncio.run(test_post())
   ```

### Step 3: Configure Bot Commands (Optional)

```
Send to BotFather: /setcommands
Select your bot

Enter commands:
start - Start the bot
help - Show help message
status - Check system status
performance - View trading performance
settings - Configure notifications
```

---

## VPS Server Setup

### Step 1: Choose VPS Provider

**Recommended Providers**:
- **DigitalOcean** - $6-12/month, easy setup
- **Vultr** - $6-12/month, good performance
- **Linode** - $5-10/month, reliable
- **AWS Lightsail** - $5-10/month, scalable

**Minimum Specifications**:
```
CPU: 2 cores
RAM: 2 GB
Storage: 50 GB SSD
OS: Ubuntu 20.04 LTS or Ubuntu 22.04 LTS
Location: Choose closest to your broker's server
```

### Step 2: Create VPS Instance

**Example: DigitalOcean Droplet**

1. **Create Account**
   - Visit digitalocean.com
   - Sign up and verify email

2. **Create Droplet**
   ```
   Choose an image: Ubuntu 22.04 LTS
   Choose a plan: Basic - $12/month (2 GB RAM, 2 CPUs)
   Choose a datacenter: London (if broker in Europe)
   Authentication: SSH keys (recommended) or Password
   Hostname: xauusd-trading-server
   ```

3. **Note Server Details**
   ```
   IP Address: 123.45.67.89
   Username: root
   Password: (if using password auth)
   SSH Key: (if using key auth)
   ```

### Step 3: Initial Server Configuration

1. **Connect via SSH**
   ```bash
   # From Linux/Mac
   ssh root@123.45.67.89
   
   # From Windows (using PuTTY)
   # Enter IP: 123.45.67.89
   # Port: 22
   # Click Open
   ```

2. **Update System**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Create Non-Root User**
   ```bash
   # Create user
   adduser trader
   
   # Add to sudo group
   usermod -aG sudo trader
   
   # Switch to new user
   su - trader
   ```

4. **Configure Firewall**
   ```bash
   # Install UFW
   sudo apt install ufw -y
   
   # Allow SSH
   sudo ufw allow 22/tcp
   
   # Allow HTTP/HTTPS (for API)
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   
   # Allow WebSocket port
   sudo ufw allow 8765/tcp
   
   # Enable firewall
   sudo ufw enable
   
   # Check status
   sudo ufw status
   ```

5. **Set Timezone**
   ```bash
   # Set to UTC (recommended for trading)
   sudo timedatectl set-timezone UTC
   
   # Verify
   timedatectl
   ```

### Step 4: Install Required Software

1. **Install Python 3.11**
   ```bash
   # Add deadsnakes PPA
   sudo apt install software-properties-common -y
   sudo add-apt-repository ppa:deadsnakes/ppa -y
   sudo apt update
   
   # Install Python 3.11
   sudo apt install python3.11 python3.11-venv python3.11-dev -y
   
   # Install pip
   sudo apt install python3-pip -y
   
   # Verify installation
   python3.11 --version
   ```

2. **Install Docker**
   ```bash
   # Install dependencies
   sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
   
   # Add Docker GPG key
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   
   # Add Docker repository
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   
   # Install Docker
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io -y
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # Verify installation
   docker --version
   docker-compose --version
   ```

3. **Install Git**
   ```bash
   sudo apt install git -y
   git --version
   ```

4. **Install PostgreSQL Client**
   ```bash
   sudo apt install postgresql-client -y
   ```

5. **Install Nginx**
   ```bash
   sudo apt install nginx -y
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

---

## Windows MT5 Connector Setup

### Step 1: Install Python on Windows

1. **Download Python**
   - Visit python.org/downloads
   - Download Python 3.11 or higher
   - Run installer

2. **Installation Options**
   ```
   ✅ Add Python to PATH
   ✅ Install pip
   ✅ Install for all users
   Installation directory: C:\Python311
   ```

3. **Verify Installation**
   ```cmd
   python --version
   pip --version
   ```

### Step 2: Clone Repository

```cmd
# Open Command Prompt
cd C:\
git clone <repository-url> gold-trading-system
cd gold-trading-system\mt5-connector
```

### Step 3: Create Virtual Environment

```cmd
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```cmd
# Install requirements
pip install -r requirements.txt

# Verify MetaTrader5 library
python -c "import MetaTrader5; print(MetaTrader5.__version__)"
```

### Step 5: Configure MT5 Connector

1. **Create Configuration File**
   ```cmd
   copy config\mt5_config.example.yaml config\mt5_config.yaml
   ```

2. **Edit Configuration**
   ```yaml
   # config/mt5_config.yaml
   mt5:
     login: 12345678
     password: "YourMT5Password"
     server: "BrokerName-Demo"
     timeout: 60000
     
   symbols:
     - XAUUSD
     
   websocket:
     host: "your-vps-ip"  # e.g., 123.45.67.89
     port: 8765
     ssl: true
     reconnect_delay: 5
     max_reconnect_attempts: 10
     
   logging:
     level: INFO
     file: logs/mt5_connector.log
   ```

### Step 6: Test MT5 Connection

```cmd
# Test script
python test_mt5_connection.py
```

Expected output:
```
✓ MT5 initialized successfully
✓ Connected to account: 12345678
✓ Server: BrokerName-Demo
✓ XAUUSD symbol found
✓ Current price: 2045.50 / 2045.70
```

### Step 7: Install as Windows Service

1. **Install NSSM (Non-Sucking Service Manager)**
   ```cmd
   # Download from nssm.cc
   # Extract to C:\nssm
   ```

2. **Create Service**
   ```cmd
   # Run as Administrator
   cd C:\nssm\win64
   
   nssm install MT5Connector "C:\gold-trading-system\mt5-connector\venv\Scripts\python.exe" "C:\gold-trading-system\mt5-connector\main.py"
   
   # Configure service
   nssm set MT5Connector AppDirectory "C:\gold-trading-system\mt5-connector"
   nssm set MT5Connector DisplayName "XAUUSD MT5 Connector"
   nssm set MT5Connector Description "MetaTrader 5 price feed connector for XAUUSD trading system"
   nssm set MT5Connector Start SERVICE_AUTO_START
   
   # Start service
   nssm start MT5Connector
   
   # Check status
   nssm status MT5Connector
   ```

---

## Linux Analysis Server Setup

### Step 1: Clone Repository

```bash
# SSH into VPS
ssh trader@123.45.67.89

# Clone repository
cd ~
git clone <repository-url> gold-trading-system
cd gold-trading-system
```

### Step 2: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit environment variables
nano .env
```

```bash
# .env file
# Database
DATABASE_URL=postgresql://trader:SecurePassword123@localhost:5432/xauusd_trading
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHANNEL_ID=-1001234567890

# WebSocket
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8765
WEBSOCKET_SSL_CERT=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
WEBSOCKET_SSL_KEY=/etc/letsencrypt/live/yourdomain.com/privkey.pem

# API
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=generate-a-secure-random-key-here

# Trading
RISK_PER_TRADE=1.0
MAX_CONCURRENT_TRADES=2
MIN_RISK_REWARD=2.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/xauusd-trading/app.log

# Redis
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production
```

### Step 3: Generate Secure Keys

```bash
# Generate API secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Save output to .env file
```

### Step 4: Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f analysis-server
```

---

## Database Configuration

### Step 1: Access PostgreSQL Container

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U trader -d xauusd_trading
```

### Step 2: Verify Database Schema

```sql
-- List tables
\dt

-- Check signals table
SELECT COUNT(*) FROM signals;

-- Check trades table
SELECT COUNT(*) FROM trades;

-- Exit
\q
```

### Step 3: Create Database Backup

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
docker-compose exec postgres pg_dump -U trader xauusd_trading > ~/backups/xauusd_trading_$(date +%Y%m%d).sql

# Verify backup
ls -lh ~/backups/
```

---

## Initial Testing

### Step 1: Test WebSocket Connection

```bash
# On VPS, check WebSocket server
docker-compose logs websocket-server

# Should see:
# WebSocket server started on 0.0.0.0:8765
# Waiting for connections...
```

### Step 2: Test MT5 to Server Connection

```cmd
# On Windows, check MT5 connector logs
type C:\gold-trading-system\mt5-connector\logs\mt5_connector.log

# Should see:
# Connected to WebSocket server
# Streaming XAUUSD prices...
```

### Step 3: Test Signal Generation

```bash
# Monitor analysis server logs
docker-compose logs -f analysis-server

# Should see:
# Market data received: XAUUSD
# Analyzing M15 timeframe...
# Analyzing H1 timeframe...
# Analyzing H4 timeframe...
```

### Step 4: Test Telegram Notifications

```bash
# Send test notification
docker-compose exec analysis-server python -c "
from src.notifications.telegram_notifier import TelegramNotifier
import asyncio

async def test():
    notifier = TelegramNotifier()
    await notifier.send_test_message()

asyncio.run(test())
"
```

Check your Telegram channel for test message.

---

## Going Live

### Step 1: Pre-Launch Checklist

- [ ] MT5 connector running and stable for 24+ hours
- [ ] WebSocket connection stable
- [ ] Database backups configured
- [ ] Telegram notifications working
- [ ] All tests passing
- [ ] Monitoring dashboards set up
- [ ] Alert system configured

### Step 2: Start with Demo Account

```
Week 1-2: Monitor system performance
- Track signal quality
- Verify risk management
- Check notification timing
- Monitor system stability

Week 3-4: Optimize parameters
- Adjust confidence thresholds
- Fine-tune stop loss/take profit
- Optimize position sizing
```

### Step 3: Transition to Live Account

1. **Update MT5 Credentials**
   ```yaml
   # config/mt5_config.yaml
   mt5:
     login: YOUR_LIVE_ACCOUNT
     password: "YourLivePassword"
     server: "BrokerName-Live"
   ```

2. **Reduce Initial Risk**
   ```bash
   # .env
   RISK_PER_TRADE=0.5  # Start with 0.5% instead of 1%
   MAX_CONCURRENT_TRADES=1  # Start with 1 trade at a time
   ```

3. **Monitor Closely**
   - Check every signal manually for first week
   - Verify execution prices
   - Monitor slippage
   - Track actual vs expected performance

### Step 4: Scale Up Gradually

```
Month 1: 0.5% risk per trade, 1 concurrent trade
Month 2: 0.75% risk per trade, 1 concurrent trade
Month 3: 1.0% risk per trade, 2 concurrent trades
Month 4+: Full parameters based on performance
```

---

## Troubleshooting Setup Issues

### MT5 Connection Issues

**Problem**: Cannot connect to MT5
```
Solution:
1. Verify MT5 is running
2. Check login credentials
3. Verify server name
4. Check firewall settings
5. Restart MT5 terminal
```

**Problem**: XAUUSD symbol not found
```
Solution:
1. Open Market Watch (Ctrl+M)
2. Right-click → Symbols
3. Search for "XAUUSD" or "GOLD"
4. Enable symbol
5. Restart connector
```

### WebSocket Connection Issues

**Problem**: Cannot connect to WebSocket server
```
Solution:
1. Check VPS firewall: sudo ufw status
2. Verify port 8765 is open
3. Check WebSocket server logs
4. Verify IP address in config
5. Test with: telnet your-vps-ip 8765
```

### Telegram Bot Issues

**Problem**: Bot not posting to channel
```
Solution:
1. Verify bot token is correct
2. Check bot is admin in channel
3. Verify channel ID (include minus sign)
4. Test with simple message
5. Check bot permissions
```

### Database Issues

**Problem**: Cannot connect to database
```
Solution:
1. Check PostgreSQL is running: docker-compose ps
2. Verify credentials in .env
3. Check database exists: docker-compose exec postgres psql -U trader -l
4. Review database logs: docker-compose logs postgres
```

---

## Next Steps

After successful setup:

1. **Read Configuration Guide**: [CONFIGURATION.md](CONFIGURATION.md)
2. **Review Trading Logic**: [SMART_MONEY_CONCEPTS.md](SMART_MONEY_CONCEPTS.md)
3. **Set Up Monitoring**: [MONITORING_LOGGING.md](MONITORING_LOGGING.md)
4. **Review Security**: [SECURITY.md](SECURITY.md)

---

## Support

If you encounter issues not covered in this guide:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review system logs
3. Check GitHub issues
4. Contact support

---

**Setup Guide Version**: 1.0  
**Last Updated**: 2024-01-05  
**Estimated Setup Time**: 2-4 hours