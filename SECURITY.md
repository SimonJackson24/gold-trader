# Security Guide

Security best practices and guidelines for the XAUUSD Gold Trading System.

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Credential Management](#credential-management)
4. [Network Security](#network-security)
5. [Data Protection](#data-protection)
6. [API Security](#api-security)
7. [Container Security](#container-security)
8. [Monitoring & Auditing](#monitoring--auditing)
9. [Incident Response](#incident-response)
10. [Security Checklist](#security-checklist)

---

## Security Overview

### Security Principles

1. **Defense in Depth**: Multiple layers of security
2. **Least Privilege**: Minimum necessary permissions
3. **Fail Secure**: System fails to secure state
4. **Separation of Duties**: No single point of failure
5. **Security by Design**: Built-in from the start

### Threat Model

**Assets to Protect:**
- Trading capital and account access
- API keys and credentials
- Trading algorithms and strategies
- Historical trade data
- System infrastructure

**Potential Threats:**
- Unauthorized access to trading account
- API key theft
- Man-in-the-middle attacks
- DDoS attacks
- Data breaches
- Insider threats

---

## Authentication & Authorization

### Multi-Factor Authentication

```python
# Implement 2FA for admin access
from pyotp import TOTP

class TwoFactorAuth:
    def generate_secret(self):
        return pyotp.random_base32()
    
    def verify_token(self, secret, token):
        totp = TOTP(secret)
        return totp.verify(token, valid_window=1)
```

### JWT Token Security

```python
# Secure JWT implementation
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 32+ character random string
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### API Key Management

```python
# Secure API key generation and storage
import secrets
import hashlib

def generate_api_key():
    """Generate cryptographically secure API key"""
    return secrets.token_urlsafe(32)

def hash_api_key(api_key: str):
    """Hash API key before storing"""
    return hashlib.sha256(api_key.encode()).hexdigest()

# Store only hashed version in database
# Never log or display full API keys
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(Enum):
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"

class Permission(Enum):
    READ_SIGNALS = "read:signals"
    WRITE_SIGNALS = "write:signals"
    READ_TRADES = "read:trades"
    CLOSE_TRADES = "close:trades"
    UPDATE_CONFIG = "update:config"
    VIEW_LOGS = "view:logs"

ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.TRADER: [
        Permission.READ_SIGNALS,
        Permission.READ_TRADES,
        Permission.CLOSE_TRADES
    ],
    Role.VIEWER: [
        Permission.READ_SIGNALS,
        Permission.READ_TRADES
    ]
}
```

---

## Credential Management

### Environment Variables

```bash
# Never commit these to git
# Use .env file (add to .gitignore)

# Generate secure passwords
openssl rand -base64 32

# Generate API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Secrets Management

**Option 1: HashiCorp Vault**
```bash
# Store secrets in Vault
vault kv put secret/xauusd-trading \
  database_password="..." \
  telegram_token="..." \
  api_secret_key="..."

# Retrieve in application
vault kv get -field=database_password secret/xauusd-trading
```

**Option 2: AWS Secrets Manager**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

**Option 3: Docker Secrets**
```yaml
# docker-compose.yml
services:
  analysis-server:
    secrets:
      - db_password
      - telegram_token

secrets:
  db_password:
    file: ./secrets/db_password.txt
  telegram_token:
    file: ./secrets/telegram_token.txt
```

### Password Policy

```python
import re

def validate_password(password: str) -> bool:
    """
    Password requirements:
    - Minimum 16 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 16:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True
```

### Credential Rotation

```bash
# Rotate credentials every 90 days
# Set up automated rotation

# Database password rotation
./scripts/rotate_db_password.sh

# API key rotation
./scripts/rotate_api_keys.sh

# SSL certificate renewal
certbot renew
```

---

## Network Security

### Firewall Configuration

```bash
# UFW (Uncomplicated Firewall)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8765/tcp  # WebSocket (with IP whitelist)

# Enable firewall
sudo ufw enable
```

### IP Whitelisting

```python
# Restrict API access to known IPs
ALLOWED_IPS = [
    "203.0.113.0/24",  # Office network
    "198.51.100.50",   # VPN server
]

def check_ip_whitelist(request_ip: str) -> bool:
    from ipaddress import ip_address, ip_network
    
    ip = ip_address(request_ip)
    return any(ip in ip_network(allowed) for allowed in ALLOWED_IPS)
```

### SSL/TLS Configuration

```nginx
# nginx.conf - Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### VPN Access

```bash
# Set up WireGuard VPN for secure access
sudo apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Configure VPN
sudo nano /etc/wireguard/wg0.conf
```

---

## Data Protection

### Encryption at Rest

```python
# Encrypt sensitive data before storing
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Encrypt before storing in database
encrypted_api_key = encryptor.encrypt(api_key)
```

### Encryption in Transit

```python
# Force HTTPS for all connections
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)

# WebSocket with SSL
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', 'key.pem')
```

### Database Security

```sql
-- Use SSL for database connections
ALTER SYSTEM SET ssl = on;

-- Encrypt sensitive columns
CREATE EXTENSION pgcrypto;

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    key_hash VARCHAR(64),  -- Store hash, not plaintext
    encrypted_key BYTEA,   -- Encrypted with pgcrypto
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Row-level security
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_trades ON trades
    FOR ALL
    TO trader_role
    USING (user_id = current_user_id());
```

### Backup Encryption

```bash
# Encrypt backups before storing
pg_dump xauusd_trading | \
  gpg --encrypt --recipient admin@example.com | \
  aws s3 cp - s3://backups/xauusd_$(date +%Y%m%d).sql.gpg
```

---

## API Security

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/signals")
@limiter.limit("100/minute")
async def get_signals():
    pass
```

### Input Validation

```python
from pydantic import BaseModel, validator

class SignalCreate(BaseModel):
    instrument: str
    direction: str
    entry_price: float
    
    @validator('direction')
    def validate_direction(cls, v):
        if v not in ['BUY', 'SELL']:
            raise ValueError('Direction must be BUY or SELL')
        return v
    
    @validator('entry_price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### SQL Injection Prevention

```python
# Always use parameterized queries
from sqlalchemy import text

# BAD - Vulnerable to SQL injection
query = f"SELECT * FROM signals WHERE instrument = '{instrument}'"

# GOOD - Parameterized query
query = text("SELECT * FROM signals WHERE instrument = :instrument")
result = db.execute(query, {"instrument": instrument})
```

---

## Container Security

### Docker Security

```dockerfile
# Use specific versions, not 'latest'
FROM python:3.11.7-slim

# Run as non-root user
RUN useradd -m -u 1000 trader
USER trader

# Read-only filesystem
docker run --read-only --tmpfs /tmp myimage

# Drop capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myimage

# Security scanning
docker scan myimage:latest
```

### Docker Compose Security

```yaml
services:
  analysis-server:
    # Security options
    security_opt:
      - no-new-privileges:true
    
    # Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Image Scanning

```bash
# Scan for vulnerabilities
trivy image analysis-server:latest

# Scan during build
docker build --security-opt seccomp=unconfined .
```

---

## Monitoring & Auditing

### Audit Logging

```python
import structlog

logger = structlog.get_logger()

def audit_log(event_type: str, user_id: str, details: dict):
    """Log security-relevant events"""
    logger.info(
        "security_audit",
        event_type=event_type,
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        ip_address=request.client.host,
        **details
    )

# Log important events
audit_log("login_success", user_id, {"method": "jwt"})
audit_log("config_change", user_id, {"field": "risk_per_trade", "old": 1.0, "new": 1.5})
audit_log("trade_closed", user_id, {"trade_id": 123, "profit_loss": 250.00})
```

### Security Monitoring

```python
# Monitor for suspicious activity
class SecurityMonitor:
    def check_failed_logins(self, user_id: str):
        """Lock account after 5 failed attempts"""
        failed_attempts = redis.get(f"failed_login:{user_id}")
        if failed_attempts and int(failed_attempts) >= 5:
            self.lock_account(user_id)
            self.send_alert(f"Account locked: {user_id}")
    
    def detect_unusual_activity(self, user_id: str):
        """Detect unusual trading patterns"""
        recent_trades = get_recent_trades(user_id, hours=1)
        if len(recent_trades) > 10:
            self.send_alert(f"Unusual activity: {user_id}")
```

### Intrusion Detection

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure for SSH
sudo nano /etc/fail2ban/jail.local

[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
```

---

## Incident Response

### Incident Response Plan

1. **Detection**: Identify security incident
2. **Containment**: Isolate affected systems
3. **Eradication**: Remove threat
4. **Recovery**: Restore normal operations
5. **Lessons Learned**: Document and improve

### Emergency Procedures

```bash
# Emergency shutdown
./scripts/emergency_shutdown.sh

# Revoke all API keys
./scripts/revoke_all_keys.sh

# Change all passwords
./scripts/rotate_all_credentials.sh

# Restore from backup
./scripts/restore_from_backup.sh
```

### Contact Information

```
Security Team: security@example.com
Emergency Phone: +1-XXX-XXX-XXXX
PGP Key: [fingerprint]
```

---

## Security Checklist

### Pre-Deployment

- [ ] All credentials rotated and secure
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Security scanning completed
- [ ] Backup system tested
- [ ] Monitoring configured
- [ ] Incident response plan documented

### Regular Maintenance

- [ ] Weekly: Review audit logs
- [ ] Monthly: Rotate API keys
- [ ] Quarterly: Security audit
- [ ] Quarterly: Penetration testing
- [ ] Annually: Full security review

### Compliance

- [ ] GDPR compliance (if applicable)
- [ ] PCI DSS compliance (if handling payments)
- [ ] SOC 2 compliance (if required)
- [ ] Regular compliance audits

---

## Security Resources

### Tools

- **Vulnerability Scanning**: Trivy, Clair
- **Secret Scanning**: GitGuardian, TruffleHog
- **SAST**: Bandit, SonarQube
- **DAST**: OWASP ZAP, Burp Suite
- **Dependency Checking**: Safety, Snyk

### References

- OWASP Top 10
- CIS Benchmarks
- NIST Cybersecurity Framework
- ISO 27001

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-05  
**Next Review**: 2024-04-05