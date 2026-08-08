# Security Guide

This document covers security considerations for Enigma production deployment.

## Authentication & Authorization

### JWT Tokens

- Tokens are signed with `SECRET_KEY`
- Tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
- Never expose tokens in frontend code
- Use HTTPS for all token transmission

### Upwork OAuth

- OAuth 2.0 Authorization Code Grant
- State parameter prevents CSRF attacks
- Tokens stored securely (not in frontend)
- Refresh tokens used for long-term access
- Never log OAuth tokens

## Secrets Management

### Required Secrets

- `SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Database credentials
- `NVIDIA_API_KEY` - NVIDIA API access
- `UPWORK_CLIENT_ID` - Upwork OAuth client ID
- `UPWORK_CLIENT_SECRET` - Upwork OAuth client secret

### Best Practices

1. **Never commit secrets to Git**
2. **Use environment variables for all secrets**
3. **Rotate secrets regularly**
4. **Use different secrets per environment**
5. **Limit secret access to necessary personnel**

### Secret Storage Options

- Environment variables (recommended for simple deployments)
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Google Secret Manager

## Data Protection

### Sensitive Data

Never log:
- Passwords
- API keys
- OAuth tokens
- Personal user information
- Upwork account details

### Logging

- Use structured logging (JSON format)
- Filter sensitive data from logs
- Log access to sensitive operations
- Retain logs for security auditing

### Database Security

- Use strong database passwords
- Enable SSL for database connections
- Restrict database access by IP
- Regular database backups
- Encrypt backups at rest

## Network Security

### HTTPS

- Always use HTTPS in production
- Use strong TLS ciphers
- Enable HSTS headers
- Use valid SSL certificates

### CORS

- Configure CORS origins explicitly
- Only allow trusted domains
- Validate CORS preflight requests

### Firewall

- Restrict inbound ports
- Only expose necessary services
- Use security groups (cloud)
- Regular security updates

## Upwork Security

### OAuth Flow

1. User initiates OAuth
2. Redirect to Upwork authorization
3. User approves access
4. Callback with authorization code
5. Exchange code for access token
6. Store tokens securely

### Rate Limiting

- Respect Upwork API rate limits
- Implement exponential backoff
- Monitor rate limit status
- Handle 429 responses gracefully

### Connects Protection

- Check connects before submission
- Display cost to user before approval
- Block submission if insufficient connects
- Track connects spent

## Human Approval Gate

### Mandatory Approval

- Applications cannot be submitted without approval
- Approval state must be explicitly set
- Approval cannot be bypassed programmatically
- Audit trail for all approvals

### Approval Workflow

```
DRAFT → READY_FOR_REVIEW → WAITING_FOR_APPROVAL → APPROVED → SUBMIT
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets in environment variables
- [ ] DEBUG=false in production
- [ ] Strong SECRET_KEY configured
- [ ] HTTPS enabled
- [ ] CORS configured correctly
- [ ] Database SSL enabled
- [ ] Firewall rules configured
- [ ] Log filtering enabled

### Post-Deployment

- [ ] Verify HTTPS works
- [ ] Test authentication flow
- [ ] Verify Upwork OAuth works
- [ ] Check logs for sensitive data
- [ ] Test rate limiting
- [ ] Verify approval gate works
- [ ] Test connects protection
- [ ] Security audit of logs

## Incident Response

### Security Incident

1. Identify affected systems
2. Rotate compromised secrets
3. Review access logs
4. Notify stakeholders
5. Document incident
6. Implement preventive measures

### Data Breach

1. Identify exposed data
2. Notify affected users
3. Review security controls
4. Implement additional safeguards
5. Comply with regulations
6. Document lessons learned
