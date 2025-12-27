# CloudPanel Nginx Configuration for Gold Trader

## Option 1: Custom Vhost File

Create a custom vhost file for your site:

```bash
# Edit the vhost file for your domain
sudo nano /etc/nginx/sites-available/goldtrader.simoncallaghan.dev.vhost
```

Add this configuration (replacing the existing content):

```nginx
server {
    listen 80;
    listen [::]:80;
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    {{ssl_certificate}}
    {{ssl_certificate_key}}

    server_name goldtrader.simoncallaghan.dev;

    # Angular frontend static files
    root /var/www/goldtrader.simoncallaghan.dev/htdocs;
    index index.html;

    # API proxy to Docker app
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket proxy
    location /ws/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Frontend routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;
}
```

Then enable and test:

```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/goldtrader.simoncallaghan.dev.vhost /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Option 2: Quick Manual Proxy (edit existing vhost)

```bash
# Edit existing vhost
sudo nano /etc/nginx/sites-available/goldtrader.simoncallaghan.dev.vhost
```

Add these location blocks inside the server block:

```nginx
    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
```

## Option 3: Clone Frontend to CloudPanel

```bash
# In CloudPanel, create site and set document root
# Then clone frontend:
cd /var/www/goldtrader.simoncallaghan.dev/htdocs
git clone https://github.com/SimonJackson24/gold-trader.git .
cd gold-trader
cd gold-trader-ui && cp -r src/* .. && cd ..
```

Then just enable SSL in CloudPanel UI and the proxy config above.

## After Configuration

1. Enable SSL in CloudPanel (Free SSL with Let's Encrypt)
2. Test: curl -I https://goldtrader.simoncallaghan.dev/api/health
3. Check Docker logs: docker logs gold_trader_app
