# 🚀 Gold Trader - Quick Start Guide

## One-Command Deployment

### Step 1: Deploy the Trading Server (Linux/VPS)

```bash
# Clone the repository
git clone https://github.com/your-org/gold-trader.git
cd gold-trader

# Run the one-command deployment script
bash deploy.sh
```

That's it! The script will:
- ✅ Create all necessary directories
- ✅ Generate SSL certificates
- ✅ Create environment configuration
- ✅ Build and start all Docker containers
- ✅ Run database migrations
- ✅ Display all connection information

---

### Step 2: Deploy the MT5 Connector (Windows with MetaTrader 5)

On your Windows machine with MetaTrader 5 installed:

```powershell
# Download deploy-connector.ps1 to your Windows machine

# Run the one-command deployment
powershell -ExecutionPolicy Bypass -File deploy-connector.ps1
```

Optional parameters:
```powershell
powershell -ExecutionPolicy Bypass -File deploy-connector.ps1 `
    -ServerUrl "ws://your-server-ip:8001" `
    -MT5Path "C:\Program Files\MetaTrader 5\terminal64.exe" `
    -MT5Login "123456" `
    -MT5Password "yourpassword" `
    -MT5Server "YourBroker-Server"
```

---

## What Gets Deployed

### Trading Server (Linux)
| Service | Port | URL |
|---------|------|-----|
| REST API | 8000 | http://localhost:8000 |
| WebSocket | 8001 | ws://localhost:8001 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| PostgreSQL | 5434 | localhost:5434 |
| Redis | 6379 | localhost:6379 |

### Default Credentials
| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | admin123 |
| PostgreSQL | postgres | postgres |
| Redis | (none) | redis123 |

---

## After Deployment

### Check System Health
```bash
curl http://localhost:8000/health
```

### View Active Signals
```bash
curl -H "Authorization: Bearer YOUR_SECRET_KEY" \
     http://localhost:8000/api/v1/signals
```

### View Logs
```bash
docker-compose logs -f trading_app
```

### Stop the Platform
```bash
docker-compose down
```

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs trading_app
```

### Database connection failed
```bash
docker-compose exec trading_app python -c "from src.database.connection import init_database; import asyncio; asyncio.run(init_database())"
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR LINUX SERVER                         │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │PostgreSQL│  │  Redis   │  │TradingApp│  │  Nginx   │    │
│  │ :5432    │  │  :6379   │  │:8000/8001│  │:80/:443  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         │              │               │                    │
│         └──────────────┼───────────────┘                    │
│                        │                                    │
│              ┌─────────▼─────────┐                         │
│              │   Docker Network  │                         │
│              └───────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket (WSS)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  WINDOWS MACHINE                            │
│                                                             │
│  ┌──────────┐                                              │
│  │ MetaTrader│◄──── Real-time data                         │
│  │    5     │                                              │
│  └────┬─────┘                                              │
│       │                                                    │
│  ┌────▼─────┐                                              │
│  │Connector │◄──── One-command: deploy-connector.ps1      │
│  └──────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Support

- 📧 Email: support@goldtrader.example.com
- 📖 Docs: See ARCHITECTURE.md and API_SPECIFICATION.md
- 🐛 Issues: Report on GitHub

---

**⚠️ Risk Warning**: Forex trading involves substantial risk of loss. This system is for educational and demonstration purposes. Always test thoroughly before deploying with real funds.
