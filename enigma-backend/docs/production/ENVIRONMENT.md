# Environment Configuration Guide

This document explains the environment variables required for Enigma production deployment.

## Environment Variables

### Core Settings

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment name (development/production/test) | Yes | development |
| `DEBUG` | Enable debug mode | Yes | false |
| `API_HOST` | API server host | No | 0.0.0.0 |
| `API_PORT` | API server port | No | 8000 |

### Database

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |

Format: `postgresql://user:password@host:port/database`

### NVIDIA NIM API

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NVIDIA_API_KEY` | NVIDIA API key | Yes | - |
| `AI_MODEL` | AI model to use | No | meta/llama-3.3-70b-instruct |
| `AI_PROVIDER` | AI provider | No | nvidia |

### JWT Authentication

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | JWT secret key | Yes | - |
| `ALGORITHM` | JWT algorithm | No | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | No | 60 |

### Redis

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `REDIS_URL` | Redis connection string | Yes | redis://localhost:6379/0 |

### Upwork Marketplace

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `UPWORK_CLIENT_ID` | Upwork OAuth client ID | Yes | - |
| `UPWORK_CLIENT_SECRET` | Upwork OAuth client secret | Yes | - |
| `UPWORK_REDIRECT_URI` | OAuth callback URL | Yes | http://localhost:8000/callback |

### CORS

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | http://localhost:3000 |

### Logging

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No | INFO |
| `LOG_FORMAT` | Log format (json/text) | No | json |

### Security

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ALLOW_REGISTRATION` | Allow new user registration | No | false |

## Security Notes

1. **Never commit `.env` file to Git**
2. **Use strong random values for SECRET_KEY**
3. **Keep Upwork credentials secure**
4. **Rotate secrets regularly**
5. **Use environment-specific values**

## Getting Upwork Credentials

1. Go to https://www.upwork.com/developer/keys/apply
2. Log in with your Upwork account
3. Select "OAuth 2.0" as key type
4. Fill in application details
5. Set redirect URI to your production callback URL
6. Copy client_id and client_secret

## Getting NVIDIA API Key

1. Go to https://build.nvidia.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Generate new API key
5. Copy the key (starts with `nvapi-`)

## Environment-Specific Configurations

### Development

```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://localhost:5432/enigma_dev
LOG_LEVEL=DEBUG
```

### Production

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-host:5432/enigma_prod
LOG_LEVEL=INFO
```

### Testing

```env
ENVIRONMENT=test
DEBUG=false
DATABASE_URL=postgresql://localhost:5432/enigma_test
LOG_LEVEL=WARNING
```
