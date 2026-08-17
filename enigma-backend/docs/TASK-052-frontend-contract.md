# TASK-052 Frontend Contract

## Overview

TASK-052 implements a safe submission boundary between APPROVED application packages and future external platform submission. No frontend changes are required in this task.

## API Contract

### Create Submission Intent

**Endpoint:** `POST /api/freelancing/application-packages/{application_id}/submission-intent`

**Authentication:** Required

**Request:**
- Path parameter: `application_id` (string) - The APPROVED application package ID

**Success Response (200):**
```json
{
  "submission_id": "intent_abc123...",
  "application_id": "pkg_dd5b438fd38f4708",
  "opportunity_id": "opp_123",
  "opportunity_title": "SEO Audit for E-commerce Site",
  "platform": "controlled_internal",
  "state": "PENDING_EXTERNAL_SUBMISSION",
  "submission_mode": "manual",
  "external_submission_attempted": false,
  "readiness_snapshot": {
    "readiness_score": 0.75,
    "readiness": "READY_TO_APPLY",
    "decision": "READY_TO_APPLY",
    "checked_at": "2026-08-17T00:00:00Z"
  },
  "created_at": "2026-08-17T00:00:00Z",
  "updated_at": "2026-08-17T00:00:00Z",
  "submission_boundary": "Intent recorded. No external platform action has been taken. APPROVED means human-approved for a future explicit submission step only."
}
```

**Error Responses:**
- `404`: Package not found or cross-user access
- `400`: Package not APPROVED, unknown platform, or stale readiness

### Get Submission Intent

**Endpoint:** `GET /api/freelancing/submission-intents/{submission_id}`

**Authentication:** Required

**Success Response (200):** Same as create response

**Error Responses:**
- `404`: Intent not found or cross-user access

### List Submission Intents

**Endpoint:** `GET /api/freelancing/submission-intents`

**Authentication:** Required

**Query Parameters:**
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Success Response (200):**
```json
{
  "intents": [...],
  "count": 5,
  "limit": 20,
  "offset": 0
}
```

### Cancel Submission Intent

**Endpoint:** `POST /api/freelancing/submission-intents/{submission_id}/cancel`

**Authentication:** Required

**Request Body (optional):**
```json
{
  "note": "User cancelled submission"
}
```

**Success Response (200):**
```json
{
  "submission_id": "intent_abc123...",
  "state": "CANCELLED",
  "cancelled_at": "2026-08-17T00:00:00Z",
  "cancellation_note": "User cancelled submission",
  "external_submission_attempted": false,
  ...
}
```

**Error Responses:**
- `404`: Intent not found or cross-user access
- `400`: Intent not in PENDING_EXTERNAL_SUBMISSION state

## UI State Mapping

### Approved Package
- **Display:** "Prepare for submission"
- **Action:** Call create submission intent endpoint
- **User Message:** "This application is approved and ready for submission. Create a submission intent to proceed."

### Pending Intent
- **Display:** "Awaiting explicit submit action"
- **Action:** Show cancel button
- **User Message:** "Submission intent recorded. No external action has been taken. You can cancel this intent or proceed to submit (future feature)."

### Cancelled Intent
- **Display:** "Cancelled"
- **Action:** Allow creating new intent if eligibility still passes
- **User Message:** "Submission cancelled. You can create a new submission intent if the application remains eligible."

## Important Notes

1. **No External Submission:** TASK-052 does NOT submit to external platforms. The `submission_boundary` field in all responses explicitly states this.

2. **No Submit Button:** Do not add a "Submit to Upwork" or similar button in TASK-052. Only "Prepare for submission" / "Cancel" actions.

3. **State Machine:** Only two states are relevant in TASK-052:
   - `PENDING_EXTERNAL_SUBMISSION` - Intent recorded, awaiting action
   - `CANCELLED` - Intent cancelled

4. **Future External Execution:** A future task will add the actual external submission step. The current intent serves as a safety boundary and audit trail.

5. **Ownership Isolation:** All endpoints are scoped to the authenticated user. Cross-user access returns 404 (non-disclosure).

## Frontend Implementation (Future)

When implementing the UI in a future task:

1. Add "Prepare for submission" button on APPROVED application packages
2. Show submission intent status in application detail view
3. Add cancel button for PENDING intents
4. Display the `submission_boundary` message prominently
5. Do not add external submission buttons until a future task implements that feature
