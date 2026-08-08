# Production Deployment Guide

This guide covers deploying Enigma to a production environment.

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis server
- Upwork API credentials (client_id, client_secret)
- NVIDIA NIM API key
- Domain name with SSL certificate

## Environment Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure production values:

```bash
cp .env.example .env
```

Required production variables:

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:password@host:port/database
NVIDIA_API_KEY=nvapi-...
SECRET_KEY=<strong-random-secret>
UPWORK_CLIENT_ID=<upwork-client-id>
UPWORK_CLIENT_SECRET=<upwork-client-secret>
UPWORK_REDIRECT_URI=https://your-domain.com/callback
CORS_ORIGINS=https://your-frontend-domain.com
```

### 2. Database Setup

Create PostgreSQL database:

```sql
CREATE DATABASE enigma_production;
```

Run migrations:

```bash
python -m alembic upgrade head
```

### 3. Redis Setup

Install and configure Redis:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Deployment Options

### Option 1: Docker (Recommended)

Build and run with Docker Compose:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Option 2: Systemd Service

Create systemd service file:

```ini
[Unit]
Description=Enigma Backend API
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=enigma
WorkingDirectory=/opt/enigma/enigma-backend
Environment="PATH=/opt/enigma/.venv/bin"
ExecStart=/opt/enigma/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable enigma
sudo systemctl start enigma
```

### Option 3: Cloud Platform

Deploy to your preferred cloud platform (AWS, GCP, Azure, Render, Railway, etc.) following their specific deployment guides.

## SSL/HTTPS Configuration

Use a reverse proxy (nginx) with Let's Encrypt:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Checks

Verify deployment:

```bash
curl https://your-domain.com/health
curl https://your-domain.com/health/detailed
curl https://your-domain.com/api/execution/health
```

## Monitoring

- Check logs: `journalctl -u enigma -f`
- Monitor database connections
- Monitor Redis memory usage
- Track Upwork API rate limits

## Backup Strategy

### Database Backups

Daily automated backups:

```bash
pg_dump enigma_production > backup_$(date +%Y%m%d).sql
```

### Configuration Backups

Backup `.env` file securely.

## Rollback Procedure

If deployment fails:

1. Stop the service: `sudo systemctl stop enigma`
2. Restore database from backup
3. Revert to previous code version
4. Restart service: `sudo systemctl start enigma`

## Security Checklist

- [ ] DEBUG=false in production
- [ ] Strong SECRET_KEY configured
- [ ] Database credentials not in code
- [ ] Upwork credentials not in code
- [ ] SSL/HTTPS enabled
- [ ] CORS configured correctly
- [ ] Firewall rules configured
- [ ] Regular security updates applied
