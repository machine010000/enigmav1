# Serverless/Vercel Limitations

## Critical Issues

### 1. Redis
- **Problem:** `redis://localhost:6379/0` invalid for serverless
- **Solution:** Use Redis Cloud or Upstash
- **Env:** `REDIS_URL=rediss://<user>:<pass>@<host>:<port>`

### 2. Background Processes
- **Problem:** Celery workers not supported (max 10-60s execution)
- **Solution:** Remove Celery or migrate to serverless queue

### 3. Filesystem
- **Problem:** No persistent filesystem
- **Solution:** Use S3/R2 for files, database for data

### 4. Database Pooling
- **Problem:** Connection pooling needs adjustment
- **Solution:** Use PgBouncer or Neon serverless driver

### 5. Execution Time
- **Problem:** 10s (free) or 60s (pro) limit
- **Solution:** Async job processing for long tasks

### 6. Cold Starts
- **Problem:** 1-3s latency on first request
- **Solution:** Keep-warm pings, optimize imports

## Upwork Integration

### Token Storage
- **Current:** In-memory (temporary)
- **Required:** Database storage with encryption

### Rate Limiting
- **Current:** In-memory (if any)
- **Required:** Distributed rate limiting (Redis)

## Required Actions Before Production

1. Configure production Redis (Redis Cloud/Upstash)
2. Remove or replace Celery
3. Implement database token storage
4. Add distributed rate limiting
5. Test with Vercel execution limits
6. Implement async job processing for LLM calls
