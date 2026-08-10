# TASK-053 — Production Deployment Guide

**Date:** 2026-08-10
**Task:** Production Deployment & Smoke Verification

---

## Pre-Deployment Checklist

### 1. Environment Variables

Set the following environment variables on the production server:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/enigma_prod

# Security
SECRET_KEY=<generate-strong-random-key>
ENIGMA_ENCRYPTION_KEY=<generate-fernet-key>

# CORS
CORS_ORIGINS=https://your-frontend-domain.com

# Environment
ENVIRONMENT=production
DEBUG=false

# API
API_HOST=0.0.0.0
API_PORT=8000

# NVIDIA NIM (if using)
NVIDIA_API_KEY=<your-api-key>
AI_MODEL=meta/llama-3.3-70b-instruct
```

### 2. Generate Keys

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Generate ENIGMA_ENCRYPTION_KEY:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Frontend Configuration

Update `enigma-frontend/index.html`:

```html
<script>
    window.ENIGMA_ENV = 'production';
    window.ENIGMA_API_BASE = 'https://your-backend-domain.com';
    window.ENIGMA_USE_MOCK_DATA = false;
</script>
```

---

## Deployment Steps

### Step 1: Database Migrations

Run the migration script to create new tables:

```bash
cd enigma-backend
python -m alembic upgrade head
```

Or manually create tables if not using Alembic:

```bash
python -c "
from app.database import engine
from app.models import Base
from app.models.enigma_profile import *
from app.models.marketplace import *
from app.models.oauth import *
import asyncio

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
"
```

### Step 2: Deploy Backend

```bash
cd enigma-backend

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 3: Deploy Frontend

The frontend is static files. Deploy to your web server:

```bash
# Copy frontend files to web server
cp -r enigma-frontend/* /var/www/enigma/

# Or use your preferred deployment method
```

### Step 4: Verify Deployment

Run the smoke test script:

```bash
python test_production_smoke.py
```

---

## Smoke Tests

### 1. Health Endpoint Test

```bash
curl https://your-backend-domain.com/health
```

Expected: `{"status": "healthy"}`

### 2. Database Read/Write Test

Run the database test script:

```bash
python test_database_read_write.py
```

### 3. Enigma Profile Persistence Test

```bash
python test_enigma_profile_persistence.py
```

### 4. Marketplace Persistence Test

```bash
python test_marketplace_persistence.py
```

### 5. OAuth Encryption Test

```bash
python test_oauth_security.py
```

---

## Production Verification Checklist

After deployment, verify:

- [ ] Backend health endpoint returns healthy
- [ ] Frontend loads without configuration errors
- [ ] Frontend connects to production backend (not localhost)
- [ ] Database read/write operations work
- [ ] Enigma Profile data persists across restarts
- [ ] Marketplace data persists across restarts
- [ ] OAuth tokens are encrypted in database
- [ ] No localhost in production configuration
- [ ] No mock data in production
- [ ] No fake marketplace responses
- [ ] No exposed secrets in logs
- [ ] CORS configuration matches frontend origin

---

## Rollback Plan

If deployment fails:

1. Revert backend to previous version
2. Revert frontend to previous version
3. Restore database from backup (if schema changed)
4. Verify rollback with smoke tests

---

## Post-Deployment Documentation

Document the following in `PRODUCTION-STATUS.md`:

- Production backend URL
- Production frontend URL
- Database connection details (without passwords)
- Environment variables set
- Migration version
- Smoke test results
- Any issues encountered

---

## Security Notes

- Never commit `.env` files to version control
- Never log encryption keys or secrets
- Never expose database credentials
- Use HTTPS in production
- Keep encryption keys secure and backed up
- Rotate secrets regularly

---

## Troubleshooting

### Frontend Configuration Error

If frontend shows "Configuration Error":
- Check `window.ENIGMA_API_BASE` is set correctly
- Check `window.ENIGMA_ENV` is set to 'production'
- Check browser console for specific error

### Database Connection Error

If backend cannot connect to database:
- Verify `DATABASE_URL` is correct
- Check database server is accessible
- Check database credentials
- Check firewall rules

### Encryption Key Error

If OAuth encryption fails:
- Verify `ENIGMA_ENCRYPTION_KEY` is set
- Verify key is valid Fernet key
- Check environment variable is loaded correctly

### CORS Error

If frontend cannot connect to backend:
- Verify `CORS_ORIGINS` includes frontend domain
- Check backend is running with correct CORS settings
- Verify frontend is using HTTPS (if required)

---

## Contact

For deployment issues, contact:
- DevOps team
- Database administrator
- Security team
