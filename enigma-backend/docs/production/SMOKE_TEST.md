# Production Smoke Test Checklist

This checklist verifies that the production deployment is functioning correctly.

## Pre-Deployment Checks

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] Redis server running
- [ ] SSL certificate valid
- [ ] Firewall rules configured
- [ ] Backup procedures tested
- [ ] Rollback procedure documented

## Infrastructure Checks

### Frontend
- [ ] Frontend reachable at domain
- [ ] HTTPS works correctly
- [ ] SSL certificate valid
- [ ] Static assets load correctly
- [ ] No console errors

### Backend
- [ ] Backend reachable at API domain
- [ ] Health endpoint returns 200
- [ ] Detailed health endpoint passes
- [ ] Execution health endpoint passes
- [ ] CORS configured correctly
- [ ] Rate limiting enabled

### Database
- [ ] Database reachable
- [ ] Connection pool working
- [ ] Migrations applied
- [ ] Backup recent
- [ ] Performance acceptable

### External Services
- [ ] NVIDIA API accessible
- [ ] Redis connection working
- [ ] Upwork API accessible

## Authentication & Security

- [ ] User authentication works
- [ ] JWT token generation works
- [ ] Token refresh works
- [ ] Session handling secure
- [ ] DEBUG=false in production
- [ ] Secrets not exposed in logs
- [ ] CORS origins restricted
- [ ] HTTPS enforced

## Upwork Integration

### OAuth Flow
- [ ] OAuth initiation works
- [ ] User can authorize
- [ ] Callback handles correctly
- [ ] Token exchange works
- [ ] Token refresh works
- [ ] State parameter validated

### Account Information
- [ ] Account status retrievable
- [ ] Connects available displayed
- [ ] Account limits displayed
- [ ] Authentication errors handled

### Job Discovery
- [ ] Real jobs discovered
- [ ] Jobs normalized correctly
- [ ] Platform-specific fields not leaked
- [ ] Job source preserved
- [ ] Duplicate jobs handled

## Revenue Pipeline

### Job Intake
- [ ] Jobs enter Work Market
- [ ] Classification works
- [ ] Capability extraction works
- [ ] WorkSpecification created
- [ ] Acceptance criteria generated
- [ ] Execution capability assessed
- [ ] Recommendation generated (APPLY/LEARN_FIRST/RESEARCH_FIRST/REJECT)

### Research & Readiness
- [ ] Knowledge gap detection works
- [ ] Evidence gap detection works
- [ ] Research plan generated
- [ ] Research execution works
- [ ] Knowledge governance enforced
- [ ] Evidence provenance tracked
- [ ] Readiness calculation correct
- [ ] READY/NOT_READY status accurate
- [ ] Supporting evidence displayed
- [ ] Knowledge usage tracked
- [ ] Confidence scores accurate
- [ ] Blockers identified

### Proposal Generation
- [ ] Proposal strategy generated
- [ ] Knowledge selection works
- [ ] Proposal generated
- [ ] No fabricated claims
- [ ] No unsupported claims
- [ ] Evidence provenance preserved
- [ ] Client questions generated
- [ ] Application package created

### Human Approval
- [ ] Approval gate enforced
- [ ] DRAFT → READY_FOR_REVIEW works
- [ ] READY_FOR_REVIEW → WAITING_FOR_APPROVAL works
- [ ] WAITING_FOR_APPROVAL → APPROVED works
- [ ] APPROVED → SUBMIT works
- [ ] REJECTED blocks submission
- [ ] REVISION_REQUESTED returns to revision
- [ ] Approval audit trail maintained

### Connects/Cost Protection
- [ ] Application cost calculated
- [ ] Cost displayed before approval
- [ ] Connects checked before submission
- [ ] Insufficient connects blocks submission
- [ ] Account restricted blocks submission
- [ ] Invalid auth blocks submission
- [ ] Missing information blocks submission

## First Real Application

- [ ] Job discovered successfully
- [ ] Job normalized correctly
- [ ] Intake completed
- [ ] Research completed
- [ ] Readiness achieved
- [ ] Proposal generated
- [ ] Evidence verified
- [ ] User approved
- [ ] Cost checked
- [ ] Application submitted
- [ ] Application ID stored
- [ ] Application status tracked
- [ ] Connects deducted
- [ ] No errors in submission

## Application Tracking

- [ ] Platform recorded
- [ ] Platform application ID stored
- [ ] Job ID stored
- [ ] Application status tracked
- [ ] Submission timestamp recorded
- [ ] Proposal version stored
- [ ] Evidence used recorded
- [ ] Knowledge used recorded
- [ ] Connects spent recorded
- [ ] Platform response recorded
- [ ] Errors/retries logged

## Observability

### Logging
- [ ] Request lifecycle logged
- [ ] Job ingestion logged
- [ ] Research lifecycle logged
- [ ] Readiness calculation logged
- [ ] Proposal generation logged
- [ ] Approval event logged
- [ ] Submission event logged
- [ ] Platform errors logged
- [ ] No secrets in logs
- [ ] Structured logging working

### Health Monitoring
- [ ] Health endpoint monitored
- [ ] Database health monitored
- [ ] Redis health monitored
- [ ] API health monitored
- [ ] Upwork health monitored
- [ ] Alerts configured

## Failure & Recovery

- [ ] Invalid OAuth token handled
- [ ] Expired token refreshed
- [ ] Upwork 401 handled
- [ ] Upwork 429 handled with backoff
- [ ] Upwork 500 handled with retry
- [ ] Network failure handled
- [ ] Insufficient Connects blocked
- [ ] Account restricted handled
- [ ] Duplicate submission prevented
- [ ] Errors normalized to PlatformError
- [ ] Application state not corrupted

## Performance

- [ ] API response time < 500ms
- [ ] Database query time < 100ms
- [ ] Redis response time < 10ms
- [ ] Upwork API response time < 2s
- [ ] No memory leaks
- [ ] No connection pool exhaustion

## Final Verification

- [ ] All smoke tests passed
- [ ] No critical errors
- [ ] No security issues
- [ ] No data loss
- [ ] Rollback procedure tested
- [ ] Documentation complete
- [ ] Team notified
- [ ] Monitoring enabled

## Test Execution Command

Run smoke tests:

```bash
# Health checks
curl https://your-domain.com/health
curl https://your-domain.com/health/detailed
curl https://your-domain.com/api/execution/health

# Authentication
curl -X POST https://your-domain.com/api/auth/login

# Upwork OAuth
curl https://your-domain.com/upwork/auth

# Job discovery
curl https://your-domain.com/api/marketplace/upwork/jobs?query=python
```

## Failure Criteria

Smoke test fails if:
- Any critical check fails
- Health endpoint returns error
- Authentication fails
- Upwork OAuth fails
- Job discovery fails
- Any security issue found
- Secrets exposed in logs
- Performance below thresholds
