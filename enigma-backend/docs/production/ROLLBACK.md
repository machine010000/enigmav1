# Rollback Procedure

This document covers rollback procedures for Enigma production deployment.

## Rollback Triggers

Rollback should be considered if:
- Critical errors in production
- Security vulnerability discovered
- Data corruption detected
- Performance degradation
- Upwork integration broken
- Authentication failure
- Database issues

## Pre-Rollback Checklist

- [ ] Identify the issue
- [ ] Determine rollback scope
- [ ] Notify stakeholders
- [ ] Prepare rollback plan
- [ ] Verify backup availability
- [ ] Estimate rollback time

## Rollback Procedures

### Code Rollback

#### Option 1: Git Rollback

```bash
# Identify the commit to rollback to
git log --oneline

# Rollback to previous commit
git checkout <previous-commit-hash>

# Redeploy
# (Use your deployment method)
```

#### Option 2: Docker Rollback

```bash
# Stop current containers
docker-compose -f docker-compose.prod.yml down

# Pull previous image
docker pull your-registry/enigma:previous-tag

# Start with previous image
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 3: Systemd Service Rollback

```bash
# Stop service
sudo systemctl stop enigma

# Revert code
cd /opt/enigma
git checkout <previous-commit-hash>

# Restart service
sudo systemctl start enigma
```

### Database Rollback

#### Option 1: Restore from Backup

```bash
# Stop application
sudo systemctl stop enigma

# Drop current database
psql -U postgres -c "DROP DATABASE enigma_production;"

# Restore from backup
psql -U postgres -c "CREATE DATABASE enigma_production;"
psql -U postgres enigma_production < backup_YYYYMMDD.sql

# Start application
sudo systemctl start enigma
```

#### Option 2: Migration Rollback

```bash
# Rollback to previous migration
python -m alembic downgrade -1

# Or rollback to specific version
python -m alembic downgrade <revision>
```

### Configuration Rollback

```bash
# Restore previous .env file
cp .env.backup .env

# Restart service
sudo systemctl restart enigma
```

## Rollback Verification

After rollback, verify:

- [ ] Health endpoint returns 200
- [ ] Authentication works
- [ ] Database accessible
- [ ] No critical errors in logs
- [ ] Upwork integration works (if applicable)
- [ ] Performance acceptable

## Rollback Time Estimates

| Component | Time Estimate |
|-----------|--------------|
| Code rollback | 5-10 minutes |
| Database restore | 10-30 minutes |
| Configuration rollback | 2-5 minutes |
| Full rollback | 15-45 minutes |

## Rollback Communication

### Internal Team

- Notify development team
- Notify operations team
- Notify management
- Document rollback reason

### External Stakeholders

- Notify users if service interruption
- Post status update
- Provide estimated recovery time

## Rollback Documentation

After rollback, document:

1. Rollback reason
2. Time taken
3. Issues encountered
4. Root cause analysis
5. Preventive measures

## Rollback Testing

Test rollback procedures regularly:

- Monthly rollback drills
- Test with staging environment
- Verify backup restoration
- Update procedures based on lessons learned

## Emergency Rollback

For critical issues, use emergency rollback:

1. Stop service immediately
2. Restore from most recent backup
3. Restart service
4. Verify functionality
5. Document incident

## Rollback Decision Tree

```
Issue Detected
    ↓
Is it critical?
    ↓ Yes → Emergency Rollback
    ↓ No
Can it be fixed in place?
    ↓ Yes → Fix in place
    ↓ No
Is rollback faster than fix?
    ↓ Yes → Rollback
    ↓ No → Fix in place
```

## Rollback Success Criteria

Rollback is successful when:
- Service is operational
- No data loss
- No new errors
- Performance acceptable
- Authentication works
- Database accessible

## Post-Rollback Actions

1. Monitor system closely
2. Check logs for errors
3. Verify all functionality
4. Communicate status
5. Schedule fix for the issue
6. Update rollback procedures
