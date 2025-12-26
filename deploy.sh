#!/bin/bash

# Copyright (c) 2024 Simon Callaghan. All rights reserved.

# ============================================================================
# GOLD TRADER - ONE-COMMAND DEPLOYMENT SCRIPT
# ============================================================================
# This script deploys the entire Gold Trader trading platform with one command.
# Usage: bash deploy.sh
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    GOLD TRADER DEPLOYMENT SCRIPT                      ║"
echo "║                   One-Command Trading Platform                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  Note: Running without root privileges. Docker commands may require sudo.${NC}"
    SUDO="sudo"
else
    SUDO=""
fi

# Generate secure secret key
generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32
}

# ============================================================================
# STEP 1: Setup Directories
# ============================================================================
echo ""
echo -e "${BLUE}📁 Step 1: Creating directory structure...${NC}"

mkdir -p logs data monitoring/grafana/provisioning/dashboards monitoring/grafana/provisioning/datasources logging nginx/ssl

echo -e "${GREEN}✅ Directories created${NC}"

# ============================================================================
# STEP 2: Generate SSL Certificates
# ============================================================================
echo ""
echo -e "${BLUE}🔒 Step 2: Generating SSL certificates...${NC}"

if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    openssl req -x509 -newkey rsa:4096 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -days 365 \
        -nodes \
        -subj "/C=US/ST=State/L=City/O=GoldTrader/CN=localhost" \
        2>/dev/null || {
        # Fallback for systems without openssl
        python3 << PYEOF
import ssl
import os
from datetime import datetime, timedelta

# Generate self-signed certificate
key = ssl.RSA.generate(4096)
cert = ssl.X509()
cert.get_subject().CN = "localhost"
cert.get_issuer().CN = "localhost"
cert.not_before = datetime.utcnow()
cert.not_after = datetime.utcnow() + timedelta(days=365)
cert.sign(key, 'sha256')

with open("nginx/ssl/cert.pem", "wb") as f:
    f.write(ssl.DER_to_PEM(cert))
with open("nginx/ssl/key.pem", "wb") as f:
    f.write(ssl.DER_to_PEM(key))
print("Certificate generated")
PYEOF
    }
    echo -e "${GREEN}✅ SSL certificates generated${NC}"
else
    echo -e "${YELLOW}⚠️  SSL certificates already exist, skipping${NC}"
fi

# ============================================================================
# STEP 3: Create Environment File
# ============================================================================
echo ""
echo -e "${BLUE}⚙️  Step 3: Creating environment configuration...${NC}"

SECRET_KEY=$(generate_secret)

cat > .env << EOF
# Gold Trader Environment Configuration
# Generated automatically by deploy.sh

# Application Settings
APP_NAME=XAUUSD Gold Trading System
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server Settings
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Security - Auto-generated secure key
SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_ENABLED=true

# API Settings
API_PREFIX=/api/v1
CORS_ORIGINS=*
RATE_LIMIT_PER_MINUTE=100

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=
JSON_LOGS=false
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# WebSocket Settings
WS_PORT=8001
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS=100

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gold_trader
DB_USER=postgres
DB_PASSWORD=postgres
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_SSL_MODE=prefer

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Monitoring Settings
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Trading Configuration
DEFAULT_SYMBOL=XAUUSD
DEFAULT_TIMEFRAME=M15
MAX_POSITION_SIZE=0.1
RISK_PER_TRADE=2.0
MAX_CONCURRENT_TRADES=2
MIN_RISK_REWARD=2.0

# SMC Parameters
FVG_MIN_SIZE_PIPS=5
OB_LOOKBACK_CANDLES=20
OB_MIN_QUALITY=70
CONFLUENCE_THRESHOLD=80
LIQUIDITY_SWEEP_THRESHOLD=3

# Telegram Configuration (optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_NOTIFY_SIGNALS=true
TELEGRAM_NOTIFY_TRADES=true
TELEGRAM_NOTIFY_DAILY_REPORT=true

# MT5 Configuration (Windows connector)
MT5_PATH=
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=

# Session Configuration
ASIAN_START=00:00
ASIAN_END=08:00
ASIAN_RISK_MULTIPLIER=0.5
LONDON_START=08:00
LONDON_END=13:00
LONDON_RISK_MULTIPLIER=1.0
NY_START=13:00
NY_END=17:00
NY_RISK_MULTIPLIER=1.5
EOF

echo -e "${GREEN}✅ Environment file created${NC}"

# ============================================================================
# STEP 4: Create Monitoring Configuration Files
# ============================================================================
echo ""
echo -e "${BLUE}📊 Step 4: Creating monitoring configuration...${NC}"

cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'trading_app'
    static_configs:
      - targets: ['trading_app:8000']
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
EOF

cat > monitoring/grafana/provisioning/datasources/datasources.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
EOF

cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Gold Trader Dashboards'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: true
EOF

cat > logging/logstash.conf << 'EOF'
input {
  beats {
    port => 5044
  }
}

filter {
  if [type] == "trading" {
    json {
      source => "message"
    }
    
    date {
      match => ["timestamp", "yyyy-MM-dd'T'HH:mm:ss.SSSZ"]
      target => "@timestamp"
    }
    
    mutate {
      remove_field => ["message", "host"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "trading-logs-%{+YYYY.MM.dd}"
  }
}
EOF

echo -e "${GREEN}✅ Monitoring configuration created${NC}"

# ============================================================================
# STEP 5: Check Docker
# ============================================================================
echo ""
echo -e "${BLUE}🐳 Step 5: Checking Docker installation...${NC}"

# Determine docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ Docker Compose is not installed.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo "Installation: curl -fsSL https://get.docker.com | bash"
    exit 1
fi

echo -e "${GREEN}✅ Docker is available${NC}"

# ============================================================================
# STEP 6: Stop Existing Containers
# ============================================================================
echo ""
echo -e "${BLUE}🛑 Step 6: Stopping existing containers...${NC}"

$DOCKER_COMPOSE_CMD down --remove-orphans 2>/dev/null || true
docker ps -a --filter "name=gold_trader*" -q | xargs -r docker rm -f 2>/dev/null || true

echo -e "${GREEN}✅ Cleaned up existing containers${NC}"

# ============================================================================
# STEP 7: Build and Start Containers
# ============================================================================
echo ""
echo -e "${BLUE}🚀 Step 7: Building and starting containers...${NC}"

$DOCKER_COMPOSE_CMD up -d --build

echo -e "${GREEN}✅ Containers started${NC}"

# ============================================================================
# STEP 8: Wait for Services
# ============================================================================
echo ""
echo -e "${BLUE}⏳ Step 8: Waiting for services to be ready...${NC}"

echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec gold_trader_db pg_isready -U postgres -q 2>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    fi
    sleep 1
done

echo "Waiting for Redis..."
for i in {1..30}; do
    if docker exec gold_trader_redis redis-cli ping 2>/dev/null | grep -q PONG; then
        echo -e "${GREEN}✅ Redis is ready${NC}"
        break
    fi
    sleep 1
done

# ============================================================================
# STEP 9: Run Database Migrations
# ============================================================================
echo ""
echo -e "${BLUE}🗄️  Step 9: Running database migrations...${NC}"

for i in {1..20}; do
    if docker exec gold_trader_app python -c "from src.database.connection import init_database; import asyncio; asyncio.run(init_database())" 2>/dev/null; then
        echo -e "${GREEN}✅ Database initialized${NC}"
        break
    fi
    echo "Waiting for database connection..."
    sleep 2
done

# ============================================================================
# STEP 10: Verify Health
# ============================================================================
echo ""
echo -e "${BLUE}✅ Step 10: Verifying deployment...${NC}"

sleep 5

# Get container IPs and ports
API_PORT=$(docker port trading_app 8000 2>/dev/null | cut -d: -f2 || echo "8000")
WS_PORT=$(docker port trading_app 8001 2>/dev/null | cut -d: -f2 || echo "8001")
PROMETHEUS_PORT=$(docker port gold_trader_prometheus 9090 2>/dev/null | cut -d: -f2 || echo "9090")
GRAFANA_PORT=$(docker port gold_trader_grafana 3000 2>/dev/null | cut -d: -f2 || echo "3000")

# Check health
HEALTH_STATUS=$(curl -s http://localhost:$API_PORT/health 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")

# ============================================================================
# FINAL OUTPUT
# ============================================================================
echo ""
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE! 🎉                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${GREEN}📍 SERVICE ENDPOINTS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  🌐  API Server:       ${CYAN}http://localhost:$API_PORT${NC}"
echo -e "  🔌  WebSocket:        ${CYAN}ws://localhost:$WS_PORT${NC}"
echo -e "  📊  Prometheus:       ${CYAN}http://localhost:$PROMETHEUS_PORT${NC}"
echo -e "  📈  Grafana:          ${CYAN}http://localhost:$GRAFANA_PORT${NC}"
echo -e "  🏥  Health Check:     ${CYAN}http://localhost:$API_PORT/health${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}🔐 SECURITY CREDENTIALS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  🔑 JWT Secret Key:    ${YELLOW}(see .env file - SECRET_KEY)${NC}"
echo -e "  🔐 API Secret:        ${YELLOW}(see .env file - SECRET_KEY)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}🗄️  DATABASE CONNECTION:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Host:     localhost"
echo -e "  Port:     5434 (mapped from 5432)"
echo -e "  Database: gold_trader"
echo -e "  User:     postgres"
echo -e "  Password: postgres"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}🔧 USEFUL COMMANDS:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  View logs:     ${CYAN}docker-compose logs -f trading_app${NC}"
echo -e "  Stop:          ${CYAN}docker-compose down${NC}"
echo -e "  Restart:       ${CYAN}docker-compose restart${NC}"
echo -e "  API Status:    ${CYAN}curl http://localhost:$API_PORT/status${NC}"
echo -e "  Signals:       ${CYAN}curl http://localhost:$API_PORT/api/v1/signals${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}📱 TELEGRAM BOT (if configured):${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Start bot and send /start command"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${YELLOW}⚠️  NEXT STEP - MT5 Connector (Windows):${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Copy deploy-connector.ps1 to your Windows machine with MT5"
echo -e "  Run: ${CYAN}powershell -ExecutionPolicy Bypass -File deploy-connector.ps1${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}✅ Platform is running and ready to use!${NC}"
echo ""
