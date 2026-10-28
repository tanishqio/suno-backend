# Deployment Guide

## Quick Start (Development)

### Local Development

```bash
# 1. Clone/navigate to project directory
cd hearing-screening-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set audio CDN URL (update config.py)
# AUDIO_BASE_URL = "https://your-cdn.example.com/hearing-test/"

# 5. Run the server
python main.py

# Server is now running at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Test the API

```bash
# In another terminal
python example_client.py

# Or use curl
bash curl_examples.sh
```

---

## Production Deployment

### Option 1: Using Gunicorn + Nginx (Recommended)

#### 1. Install Gunicorn

```bash
pip install gunicorn
```

#### 2. Create systemd Service File

Create `/etc/systemd/system/hearing-api.service`:

```ini
[Unit]
Description=Hearing Screening Agent API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/hearing-screening-api
Environment="PATH=/opt/hearing-screening-api/venv/bin"
ExecStart=/opt/hearing-screening-api/venv/bin/gunicorn \
  -w 4 \
  -b 127.0.0.1:8000 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start hearing-api
sudo systemctl enable hearing-api
```

#### 4. Nginx Reverse Proxy

Create `/etc/nginx/sites-available/hearing-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

Enable and test:

```bash
sudo ln -s /etc/nginx/sites-available/hearing-api \
  /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Setup SSL (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  hearing-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AUDIO_BASE_URL=https://your-cdn.example.com/hearing-test/
      - LOG_LEVEL=INFO
      - TOTAL_STEPS=5
      - TEST_EXPIRY_MINUTES=10
    volumes:
      - ./hearing_tests.db:/app/hearing_tests.db
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - hearing-api
    restart: unless-stopped
```

#### 3. Build and Run

```bash
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f hearing-api
```

---

### Option 3: AWS EC2 Deployment

#### 1. Launch EC2 Instance

- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.micro (or larger)
- Security Group: Allow ports 80, 443, 22

#### 2. SSH and Setup

```bash
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx curl git

# Clone repository
cd /opt
sudo git clone https://github.com/yourrepo/hearing-screening-api.git
sudo chown -R ubuntu:ubuntu hearing-screening-api
cd hearing-screening-api

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy systemd service
sudo cp hearing-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start hearing-api
sudo systemctl enable hearing-api
```

#### 3. Setup SSL

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 4: Heroku Deployment

#### 1. Create Procfile

```
web: gunicorn -w 4 -b 0.0.0.0:$PORT main:app
```

#### 2. Create runtime.txt

```
python-3.11.7
```

#### 3. Deploy

```bash
heroku login
heroku create hearing-screening-api
git push heroku main
heroku config:set AUDIO_BASE_URL=https://your-cdn.example.com/hearing-test/
```

#### 4. View Logs

```bash
heroku logs --tail
heroku open
```

---

### Option 5: Google Cloud Run

#### 1. Create Dockerfile (as shown above)

#### 2. Build and Deploy

```bash
# Build
docker build -t gcr.io/your-project/hearing-api .

# Push to Container Registry
docker push gcr.io/your-project/hearing-api

# Deploy to Cloud Run
gcloud run deploy hearing-api \
  --image gcr.io/your-project/hearing-api \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --set-env-vars AUDIO_BASE_URL=https://your-cdn.example.com/hearing-test/
```

---

## Configuration for Production

### 1. Environment Variables

```bash
# Database (use managed database in production)
DATABASE_URL=postgresql://user:pass@db-host:5432/hearing_db

# Audio CDN
AUDIO_BASE_URL=https://your-cdn.example.com/hearing-test/

# Server
LOG_LEVEL=INFO
TOTAL_STEPS=5
TEST_EXPIRY_MINUTES=10

# Security
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
```

### 2. Use PostgreSQL Instead of SQLite

Edit `models.py`:

```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hearing_tests.db")

# For PostgreSQL:
# DATABASE_URL = "postgresql://user:password@localhost/hearing_db"
```

Install PostgreSQL driver:

```bash
pip install psycopg2-binary
```

### 3. Enable CORS for Bolna

In `main.py`, adjust CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bolna-api.example.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 4. Add Request Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Add file handler
file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(file_handler)
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check if service is running
curl -s http://localhost:8000/health | jq .

# Monitor with Prometheus
curl -s http://localhost:8000/metrics
```

### Database Maintenance

```bash
# Backup SQLite
cp hearing_tests.db hearing_tests.db.backup

# Or with PostgreSQL
pg_dump -U user hearing_db > backup.sql
```

### Log Rotation

```bash
# Using logrotate
cat > /etc/logrotate.d/hearing-api << EOF
/opt/hearing-screening-api/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
EOF
```

### Performance Tuning

```nginx
# nginx.conf
worker_processes auto;
worker_connections 1024;

# Gunicorn workers
gunicorn -w 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Troubleshooting

### Service won't start

```bash
sudo systemctl status hearing-api
sudo journalctl -u hearing-api -n 50
```

### 502 Bad Gateway

```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Check Nginx proxy
nginx -t
```

### Database errors

```bash
# Check permissions
ls -la hearing_tests.db

# Reset database
rm hearing_tests.db
python -c "from models import Base, engine; Base.metadata.create_all(bind=engine)"
```

### High CPU usage

```bash
# Increase Gunicorn workers
gunicorn -w 8 main:app

# Or use async workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

---

## Security Checklist

- [ ] Change default AUDIO_BASE_URL to your CDN
- [ ] Use HTTPS only (SSL certificate configured)
- [ ] Enable CORS only for Bolna domain
- [ ] Rotate database backups regularly
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets
- [ ] Keep dependencies updated
- [ ] Run security scanning
- [ ] Setup rate limiting (if needed)
- [ ] Enable access logging

---

## Scaling Considerations

### For High Volume

1. **Use PostgreSQL** instead of SQLite
2. **Add Redis** for caching/sessions
3. **Use multiple Gunicorn workers** (4-8 per CPU core)
4. **Deploy load balancer** (AWS ELB, Nginx)
5. **Use managed database** (AWS RDS, Google Cloud SQL)
6. **Enable auto-scaling** (AWS Auto Scaling, GCP Autoscaling)
7. **Add CDN** (CloudFront, Cloudflare) for audio files

### Database Schema Optimization

```sql
-- Add indexes for faster queries
CREATE INDEX idx_test_phone ON hearing_tests(phone);
CREATE INDEX idx_test_call_id ON hearing_tests(call_id);
CREATE INDEX idx_test_created_at ON hearing_tests(created_at);
```

---

## Support & Monitoring Tools

### Recommended Services

- **Monitoring**: Datadog, New Relic, Prometheus
- **Logging**: ELK Stack, Splunk, Google Cloud Logging
- **Error Tracking**: Sentry, Rollbar, Bugsnag
- **APM**: Datadog APM, New Relic APM
- **Uptime Monitoring**: Pingdom, StatusCake, Uptime Robot

### Example: Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/123456",
    integrations=[FastApiIntegration()]
)
```

---

## Rollback Procedure

```bash
# Keep previous version
cp -r hearing-screening-api hearing-screening-api.backup

# Deploy new version
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart hearing-api

# If issues, rollback
sudo systemctl stop hearing-api
rm -rf hearing-screening-api
mv hearing-screening-api.backup hearing-screening-api
sudo systemctl start hearing-api
```

---

## Next Steps

1. Configure audio CDN (AWS S3, Google Cloud Storage, etc.)
2. Upload audio files to CDN
3. Update `AUDIO_BASE_URL` in `config.py`
4. Test with `curl_examples.sh`
5. Monitor performance and logs
6. Setup automated backups
7. Configure monitoring/alerting
