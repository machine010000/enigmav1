# TASK-052 Future External Execution Boundary

## Current State (TASK-052)

TASK-052 implements the **intent recording boundary** only:
- APPROVED application → PENDING_EXTERNAL_SUBMISSION intent
- Intent is persisted with readiness snapshot
- No external platform contact occurs
- `external_submission_attempted` is always `False`

## Future External Execution Design (TASK-053+)

### Proposed Architecture

When implementing actual external submission in a future task, the architecture should be:

```
PENDING_EXTERNAL_SUBMISSION intent
  → explicit human-triggered external execution
  → adapter invocation (separate service)
  → platform response handling
  → SUBMITTED or FAILED state transition
```

### Recommended Components

#### 1. External Submission Service (New)
```python
class ExternalSubmissionService:
    """
    Separate service for actual external platform submission.
    
    MUST NOT be part of SubmissionIntentService to maintain hard separation.
    """
    
    async def execute_submission(
        self,
        submission_intent: ApplicationSubmissionIntent,
        db: AsyncSession,
    ) -> SubmissionResult:
        """
        Execute external submission using platform adapter.
        
        Steps:
        1. Load APPROVED application package
        2. Authenticate to platform (OAuth, API keys)
        3. Call MarketplaceAdapter.submit_application
        4. Handle platform response
        5. Update intent state to SUBMITTED or FAILED
        6. Record external_submission_id
        7. Set external_submission_attempted = True
        """
        pass
```

#### 2. State Machine Extension

Add new state to `IntentState` enum:
```python
class IntentState(str, Enum):
    PENDING_EXTERNAL_SUBMISSION = "PENDING_EXTERNAL_SUBMISSION"
    CANCELLED = "CANCELLED"
    SUBMITTED = "SUBMITTED"  # NEW in future task
    FAILED = "FAILED"  # NEW in future task
```

#### 3. New API Endpoint

```python
@router.post("/submission-intents/{submission_id}/execute")
async def execute_external_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """
    Execute external platform submission.
    
    TASK-053+: This endpoint triggers actual external submission.
    TASK-052: This endpoint does NOT exist.
    """
    pass
```

### Safety Requirements for Future Task

1. **Explicit Human Trigger**: External submission must require explicit user action (button click, API call). No automatic execution.

2. **Cost Confirmation**: Before submission, display platform costs (connects, bids) and require confirmation.

3. **Rate Limit Check**: Verify platform limits before submission (e.g., Upwork connects available).

4. **Authentication Validation**: Ensure platform credentials are valid and not expired.

5. **Idempotency**: Handle duplicate execution attempts gracefully (check if already submitted).

6. **Error Handling**: 
   - Network failures → retry with backoff
   - Platform errors → record failure reason, allow retry
   - Authentication errors → prompt re-authentication

7. **Audit Trail**: Record all external submission attempts with timestamps, platform responses, and any errors.

8. **Learning Isolation**: External submission success/failure should NOT automatically update learning profile. Learning updates should be explicit and separate.

### Platform-Specific Considerations

#### Upwork
- Requires OAuth 2.0 authentication
- Costs connects per application
- Has daily/monthly application limits
- Returns application ID after submission

#### Fiverr
- Requires API key authentication
- Costs bids per application
- Has different rate limits
- Returns application status

#### Controlled Internal (Testing)
- No actual external call
- Simulates submission for testing
- Useful for integration tests

### Migration Requirements

When implementing external submission:

1. **Add new migration** to extend state enum in database (if stored as ENUM) or add new state values.

2. **Update intent model** to add:
   - `submitted_at` timestamp
   - `platform_response` JSON field
   - `retry_count` integer

3. **Update service** to handle new state transitions.

### Testing Requirements

Future task should include tests for:

1. Successful external submission
2. Failed external submission (network error)
3. Failed external submission (platform error)
4. Authentication failure handling
5. Rate limit enforcement
6. Idempotency (duplicate execution)
7. Cost confirmation flow
8. Platform-specific adapter integration
9. Learning isolation (no automatic updates)

### Security Considerations

1. **Credential Storage**: Platform credentials should be stored securely (encrypted at rest, never logged).

2. **Token Refresh**: Implement OAuth token refresh before submission if needed.

3. **Scope Limitation**: Use minimum required OAuth scopes.

4. **Audit Logging**: Log all external submission attempts (without credentials).

5. **User Consent**: Require explicit user consent before each external submission.

### Rollback Plan

If external submission needs to be disabled:

1. Remove or disable the `/execute` endpoint
2. Keep intent creation/cancellation endpoints (TASK-052 functionality)
3. Existing SUBMITTED intents remain in database for audit
4. New intents can only reach PENDING_EXTERNAL_SUBMISSION state

## Summary

TASK-052 provides the foundation:
- Safe intent recording
- Eligibility validation
- Ownership isolation
- Fresh readiness checks
- No external contact

Future task (TASK-053+) will add:
- External execution service
- Platform adapter integration
- SUBMITTED/FAILED states
- Cost confirmation
- Error handling

The hard separation between intent recording (TASK-052) and external execution (future task) ensures safety and allows independent testing of each component.
