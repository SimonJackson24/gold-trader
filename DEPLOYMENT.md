# Deployment Guide

Complete guide for deploying the XAUUSD Gold Trading System to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [VPS Server Setup](#vps-server-setup)
3. [Docker Deployment](#docker-deployment)
4. [SSL/TLS Configuration](#ssltls-configuration)
5. [Database Setup](#database-setup)
6. [Service Configuration](#service-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup Configuration](#backup-configuration)
9. [Production Verification](#production-verification)
10. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Required Information

- [ ] VPS IP address and SSH credentials
- [ ] Domain name (optional, for SSL)
- [ ] MT5 account credentials
- [ ] Telegram bot token and channel ID
- [ ] Database password (strong, 16+ characters)
- [ ] API secret keys (generated)
- [ ] Backup storage location

### Required Accounts

- [ ] VPS provider account (DigitalOcean, Vultr, etc.)
- [ ] MT5 broker account
- [ ] Telegram account with bot created
- [ ] Domain registrar (if using custom domain)
- [ ] Email for alerts

### Local Requirements

- [ ] Git installed
- [ ] SSH client
- [ ] Text editor
- [ ] This repository cloned

---

## VPS Server Setup

### Step 1: Create VPS Instance

**Recommended Specifications:**
```
Provider: DigitalOcean, Vultr, or Linode
OS: Ubuntu 22.04 LTS
CPU: 2 vCPUs
RAM: 4 GB
Storage: 80 GB SSD
Location: Closest to broker server
```

**Create Droplet/Instance:**
```bash
# Example: DigitalOcean CLI
doctl compute droplet create xauusd-trading \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region lon1 \
  --ssh-keys YOUR_SSH_KEY_ID
```

### Step 2: Initial Server Configuration

```bash
# Connect to server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Set timezone to UTC
timedatectl set-timezone UTC

# Create non-root user
adduser trader
usermod -aG sudo trader

# Configure SSH for new user
mkdir -p /home/trader/.ssh
cp ~/.ssh/authorized_keys /home/trader/.ssh/
chown -R trader:trader /home/trader/.ssh
chmod 700 /home/trader/.ssh
chmod 600 /home/trader/.ssh/authorized_keys

# Switch to new user
su - trader
```

### Step 3: Configure Firewall

```bash
# Install UFW
sudo apt install ufw -y

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow WebSocket
sudo ufw allow 8765/tcp

# Allow custom ports (if needed)
sudo ufw allow 8000/tcp  # API
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 3000/tcp  # Grafana

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Step 4: Install Required Software

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y

# Install other utilities
sudo apt install htop curl wget vim -y

# Logout and login again for docker group to take effect
exit
ssh trader@YOUR_SERVER_IP

# Verify installations
docker --version
docker-compose --version
git --version
```

---

## Docker Deployment

### Step 1: Clone Repository

```bash
# Clone repository
cd ~
git clone <repository-url> gold-trading-system
cd gold-trading-system

# Create necessary directories
mkdir -p logs backups data
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Critical Variables to Set:**
```bash
# Database
DATABASE_PASSWORD=YOUR_SECURE_PASSWORD_HERE

# Telegram
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHANNEL_ID=YOUR_CHANNEL_ID_HERE

# API
API_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# JWT
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Step 3: Build and Start Services

```bash
# Build images
docker-compose build

# Start services in detached mode
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Initialize Database

```bash
# Access PostgreSQL container
docker-compose exec postgres psql -U trader -d xauusd_trading

# Run initialization script
\i /docker-entrypoint-initdb.d/init.sql

# Verify tables
\dt

# Exit
\q
```

---

## SSL/TLS Configuration

### Option 1: Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Stop nginx temporarily
docker-compose stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Update docker-compose.yml to mount certificates
# Add to nginx service:
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro

# Restart nginx
docker-compose start nginx

# Set up auto-renewal
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet && docker-compose restart nginx
```

### Option 2: Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/selfsigned.key \
  -out nginx/ssl/selfsigned.crt

# Update .env
WEBSOCKET_SSL_CERT=./nginx/ssl/selfsigned.crt
WEBSOCKET_SSL_KEY=./nginx/ssl/selfsigned.key
```

---

## Database Setup

### Step 1: Secure PostgreSQL

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U trader -d xauusd_trading

# Change default password
ALTER USER trader WITH PASSWORD 'YOUR_NEW_SECURE_PASSWORD';

# Create read-only user for monitoring
CREATE USER monitoring WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE xauusd_trading TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;

# Exit
\q
```

### Step 2: Configure Backups

```bash
# Create backup script
cat > ~/backup-database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/trader/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="xauusd_trading_${DATE}.sql.gz"

# Create backup
docker-compose exec -T postgres pg_dump -U trader xauusd_trading | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep only last 30 days
find ${BACKUP_DIR} -name "xauusd_trading_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${FILENAME}"
EOF

chmod +x ~/backup-database.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/trader/backup-database.sh >> /home/trader/logs/backup.log 2>&1
```

### Step 3: Test Backup and Restore

```bash
# Test backup
./backup-database.sh

# Test restore
gunzip -c backups/xauusd_trading_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T postgres psql -U trader -d xauusd_trading
```

---

## Service Configuration

### Step 1: Configure Systemd Services

```bash
# Create systemd service for Docker Compose
sudo nano /etc/systemd/system/xauusd-trading.service
```

```ini
[Unit]
Description=XAUUSD Gold Trading System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/trader/gold-trading-system
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=trader
Group=trader

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable xauusd-trading
sudo systemctl start xauusd-trading

# Check status
sudo systemctl status xauusd-trading
```

### Step 2: Configure Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/xauusd-trading
```

```
/home/trader/gold-trading-system/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 trader trader
    sharedscripts
    postrotate
        docker-compose -f /home/trader/gold-trading-system/docker-compose.yml restart analysis-server
    endscript
}
```

---

## Monitoring Setup

### Step 1: Configure Prometheus

```bash
# Create Prometheus configuration
mkdir -p monitoring
nano monitoring/prometheus.yml
```

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'analysis-server'
    static_configs:
      - targets: ['analysis-server:8000']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
  
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Step 2: Configure Grafana

```bash
# Access Grafana
# URL: http://YOUR_SERVER_IP:3000
# Default: admin/admin

# Add Prometheus data source
# Configuration → Data Sources → Add Prometheus
# URL: http://prometheus:9090

# Import dashboards
# Dashboard ID: 1860 (Node Exporter)
# Dashboard ID: 9628 (PostgreSQL)
```

### Step 3: Configure Alerts

```bash
# Create alerting rules
nano monitoring/alert_rules.yml
```

```yaml
groups:
  - name: trading_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"
      
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        annotations:
          summary: "Memory usage above 90%"
```

---

## Backup Configuration

### Step 1: Configure Remote Backups

```bash
# Install rclone for cloud backups
curl https://rclone.org/install.sh | sudo bash

# Configure rclone (example: AWS S3)
rclone config

# Create backup script with cloud upload
cat > ~/backup-to-cloud.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/trader/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="xauusd_trading_${DATE}.sql.gz"

# Database backup
docker-compose exec -T postgres pg_dump -U trader xauusd_trading | gzip > "${BACKUP_DIR}/${FILENAME}"

# Upload to cloud
rclone copy "${BACKUP_DIR}/${FILENAME}" remote:xauusd-backups/

# Backup configuration files
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" .env docker-compose.yml

# Upload config backup
rclone copy "${BACKUP_DIR}/config_${DATE}.tar.gz" remote:xauusd-backups/config/

echo "Backup completed and uploaded: ${FILENAME}"
EOF

chmod +x ~/backup-to-cloud.sh

# Schedule cloud backups
crontab -e
# Add: 0 3 * * * /home/trader/backup-to-cloud.sh >> /home/trader/logs/cloud-backup.log 2>&1
```

---

## Production Verification

### Step 1: Health Checks

```bash
# Check all services are running
docker-compose ps

# Check API health
curl http://localhost:8000/api/v1/health

# Check WebSocket
wscat -c ws://localhost:8765

# Check database
docker-compose exec postgres psql -U trader -d xauusd_trading -c "SELECT 1;"

# Check Redis
docker-compose exec redis redis-cli ping
```

### Step 2: Functional Tests

```bash
# Test Telegram notification
docker-compose exec analysis-server python -c "
from src.notifications.telegram_notifier import TelegramNotifier
import asyncio

async def test():
    notifier = TelegramNotifier()
    await notifier.send_message('🚀 System deployed successfully!')

asyncio.run(test())
"

# Check logs for errors
docker-compose logs --tail=100 analysis-server | grep ERROR

# Monitor resource usage
docker stats
```

### Step 3: Performance Baseline

```bash
# Run performance test
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# Check database performance
docker-compose exec postgres psql -U trader -d xauusd_trading -c "
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Rollback Procedures

### Emergency Rollback

```bash
# Stop current deployment
docker-compose down

# Restore from backup
gunzip -c backups/xauusd_trading_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T postgres psql -U trader -d xauusd_trading

# Checkout previous version
git log --oneline
git checkout PREVIOUS_COMMIT_HASH

# Rebuild and restart
docker-compose build
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8000/api/v1/health
```

### Gradual Rollback

```bash
# Keep old version running
docker-compose -f docker-compose.old.yml up -d

# Start new version on different ports
# Edit docker-compose.yml to use ports 8001, 8766, etc.
docker-compose up -d

# Test new version
curl http://localhost:8001/api/v1/health

# If successful, switch traffic
# Update nginx configuration
# If failed, stop new version and keep old
```

---

## Post-Deployment

### Step 1: Monitoring Setup

```bash
# Set up monitoring alerts
# Configure email/SMS notifications
# Set up uptime monitoring (UptimeRobot, Pingdom)
```

### Step 2: Documentation

```bash
# Document deployment
# Server IP: YOUR_SERVER_IP
# Deployment date: $(date)
# Version: $(git rev-parse HEAD)
# Configuration: Production
```

### Step 3: Team Notification

```bash
# Notify team of successful deployment
# Share access credentials (securely)
# Schedule post-deployment review
```

---

## Maintenance Schedule

### Daily
- Check system health
- Review error logs
- Monitor resource usage

### Weekly
- Review performance metrics
- Check backup integrity
- Update dependencies (if needed)

### Monthly
- Security updates
- Performance optimization
- Capacity planning review

### Quarterly
- Full system audit
- Disaster recovery test
- Documentation update

---

## Troubleshooting Deployment Issues

### Services Won't Start

```bash
# Check Docker logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h

# Restart Docker
sudo systemctl restart docker
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify credentials
docker-compose exec postgres psql -U trader -d xauusd_trading

# Check network
docker network ls
docker network inspect xauusd-network
```

### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -noout -dates

# Renew certificate
sudo certbot renew

# Check nginx configuration
docker-compose exec nginx nginx -t
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-02-05