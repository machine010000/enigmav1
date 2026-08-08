# ENIGMA Frontend Contracts

## Overview

The ENIGMA frontend is a **Control Plane** over the cognitive core. It does not decide how Enigma thinks - it accepts user intent, displays brain state, and presents results.

## Architecture

```
USER
 ↓
ENIGMA PROFILE
 ↓
WORKSPACES
 ├── Freelancing
 └── Brand & Marketing
```

## Contract Definitions

### 1. USER Contract

**Purpose**: User identity, authentication, and profile management

**Fields**:
- `user_id`: str - Unique identifier
- `username`: str - Display name
- `email`: str - Contact email
- `created_at`: datetime - Account creation
- `last_active`: datetime - Last activity
- `subscription_tier`: str - Free/Pro/Enterprise
- `preferences`: Dict - User settings
- `linked_platforms`: List[str] - Connected freelancing platforms

**Backend Mapping**:
- Maps to `app.models.user.User`
- Authentication via FastAPI security
- Session management via execution layer

---

### 2. ENIGMA PROFILE Contract

**Purpose**: The user's professional identity within Enigma - capabilities, evidence, and readiness

**Fields**:
- `profile_id`: str - Unique profile identifier
- `user_id`: str - Owner
- `display_name`: str - Professional name
- `tagline`: str - Professional summary
- `capabilities`: List[CapabilityProfile] - Offered capabilities
- `evidence_vault`: EvidenceVault - Collected evidence
- `readiness_score`: float - Overall readiness (0.0-1.0)
- `active_workspaces`: List[str] - Enabled workspaces
- `knowledge_domains`: List[str] - Areas of expertise
- `profession_focus`: str - Primary profession

**CapabilityProfile**:
- `capability_id`: str
- `name`: str
- `maturity_level`: int - 1-5
- `knowledge_coverage`: float - 0.0-1.0
- `evidence_count`: int
- `execution_success_rate`: float
- `last_used`: datetime

**EvidenceVault**:
- `portfolio_items`: List[PortfolioItem]
- `certifications`: List[Certification]
- `testimonials`: List[Testimonial]
- `work_history`: List[WorkEntry]
- `skills_assessment`: Dict

**Backend Mapping**:
- `capabilities` → `app.profession.capability.Capability`
- `evidence_vault` → `app.knowledge.evidence.Evidence`
- `readiness_score` → Computed from `app.profession.readiness.ReadinessAssessment`
- `profession_focus` → `app.profession.Profession`

---

### 3. FREELANCING Workspace Contract

**Purpose**: Manage freelancing platforms, job discovery, applications, and execution

**Sub-Contracts**:

#### 3.1 Platforms
- `platform_id`: str
- `platform_name`: str - Upwork, Freelancer, Fiverr, Khamsat
- `connection_status`: str - connected/disconnected/pending
- `api_credentials_encrypted`: str
- `credits_balance`: int - Connects/bids available
- `success_rate`: float - Historical success on platform
- `knowledge_pack_id`: str - Platform-specific knowledge

#### 3.2 Capabilities Selection
- `selected_capabilities`: List[str] - IDs of selected capabilities
- `platform_recommendations`: Dict[platform, List[capability]]
- `market_demand`: Dict[capability, demand_score]

#### 3.3 Job Discovery
- `job_id`: str
- `platform`: str
- `title`: str
- `description`: str
- `budget_min`: float
- `budget_max`: float
- `client_rating`: float
- `posted_date`: datetime
- `match_score`: float - Enigma's match assessment
- `knowledge_match`: float
- `execution_match`: float
- `risk_level`: str - low/medium/high
- `required_capabilities`: List[str]
- `deliverables`: List[str]

#### 3.4 Readiness Assessment
- `capability_id`: str
- `knowledge_readiness`: float - 0.0-1.0
- `execution_readiness`: float - 0.0-1.0
- `platform_readiness`: float - 0.0-1.0
- `proposal_readiness`: float - 0.0-1.0
- `missing_knowledge`: List[str]
- `risks`: List[str]
- `status`: str - ready/research_required/not_ready

#### 3.5 Application
- `application_id`: str
- `job_id`: str
- `proposal_content`: str
- `proposal_confidence`: float
- `submitted_at`: datetime
- `status`: str - draft/submitted/accepted/rejected
- `client_response`: Optional[str]

#### 3.6 Active Work
- `work_id`: str
- `job_id`: str
- `execution_session_id`: str
- `execution_plan`: List[ExecutionStep]
- `current_step`: int
- `progress`: float - 0.0-1.0
- `deliverables_completed`: List[str]
- `deliverables_pending`: List[str]
- `deadline`: datetime
- `status`: str - in_progress/delivered/paid/disputed

**Backend Mapping**:
- `Platforms` → `app.work_market.platform.Platform`
- `Job Discovery` → `app.intelligence.job_analyzer.JobAnalysis`
- `Readiness Assessment` → `app.profession.readiness.ReadinessAssessment`
- `Application` → `app.engagement.proposal.Proposal`
- `Active Work` → `app.execution.ExecutionSession`

---

### 4. BRAND & MARKETING Workspace Contract

**Purpose**: Manage Enigma's brand identity, content, and marketing channels

**Sub-Contracts**:

#### 4.1 Brand Identity
- `brand_id`: str
- `name`: str - "ENIGMA"
- `positioning`: str - Market positioning statement
- `value_proposition`: str
- `tone_of_voice`: str
- `visual_identity`: Dict - Colors, fonts, logo
- `brand_guidelines`: Dict

#### 4.2 Capabilities Display
- `capability_id`: str
- `display_name`: str
- `description`: str
- `case_study_count`: int
- `success_rate`: float
- `featured`: bool

#### 4.3 Brand Assets
- `asset_id`: str
- `asset_type`: str - website/linkedin/facebook/instagram/tiktok/youtube
- `url`: str
- `status`: str - active/inactive/setup_needed
- `metrics`: Dict - Followers, engagement, etc.
- `last_updated`: datetime

#### 4.4 Content Engine
- `content_id`: str
- `content_type`: str - case_study/knowledge/behind_scenes/result/offer
- `topic`: str
- `purpose`: str - educate/convert/engage
- `target_channel`: str
- `status`: str - draft/scheduled/published
- `evidence_sources`: List[str] - Linked evidence IDs
- `generated_content`: str
- `metrics`: Dict - Views, engagement, conversions

#### 4.5 Campaigns
- `campaign_id`: str
- `name`: str
- `objective`: str
- `channels`: List[str]
- `content_ids`: List[str]
- `start_date`: datetime
- `end_date`: datetime
- `budget`: float
- `status`: str - planned/active/completed
- `results`: Dict

**Backend Mapping**:
- `Brand Identity` → `app.knowledge.brand.BrandIdentity`
- `Capabilities Display` → `app.profession.capability.Capability`
- `Content Engine` → `app.intelligence.content.ContentGenerator`
- `Campaigns` → `app.intelligence.campaign.Campaign`

---

## Backend Integration Points

### Cognitive Core → Frontend

1. **Profession Layer**
   - `Capability` → Profile capabilities, workspace selection
   - `ReadinessAssessment` → Readiness scores, missing knowledge
   - `Profession` → Profession focus

2. **Knowledge Governance**
   - `Knowledge` → Knowledge coverage, platform knowledge packs
   - `Evidence` → Evidence vault, portfolio items
   - `QualityGate` → Readiness validation

3. **Execution Layer**
   - `ExecutionSession` → Active work tracking
   - `ExecutionRuntime` → Progress monitoring
   - `WorkerResult` → Deliverable completion

4. **Intelligence Layer**
   - `JobAnalyzer` → Job discovery, match scoring
   - `ProposalGenerator` → Proposal generation
   - `ContentGenerator` → Brand content creation

5. **Engagement Layer**
   - `Proposal` → Application tracking
   - `ClientInteraction` → Communication history

### Frontend → Cognitive Core

1. **User Intent**
   - Workspace selection → ReasoningSession context
   - Capability selection → Profession Layer activation
   - Job selection → Intelligence Layer analysis

2. **Evidence Input**
   - Profile updates → Knowledge Governance ingestion
   - Work history → Evidence vault population

3. **Execution Control**
   - Start/stop/pause → ExecutionRuntime control
   - Approval checkpoints → ExecutionCheckpoint approval

---

## Data Flow Example: Freelancing Application

```
1. USER selects capabilities
   ↓
2. FRONTEND sends to Profession Layer
   ↓
3. COGNITIVE CORE assesses readiness
   ↓
4. FRONTEND displays readiness assessment
   ↓
5. USER browses recommended jobs
   ↓
6. FRONTEND requests job analysis
   ↓
7. INTELLIGENCE LAYER analyzes job
   ↓
8. FRONTEND displays job match + risks
   ↓
9. USER requests proposal
   ↓
10. INTELLIGENCE LAYER generates proposal
    ↓
11. FRONTEND displays proposal for review
    ↓
12. USER approves and submits
    ↓
13. ENGAGEMENT LAYER tracks application
    ↓
14. If accepted → EXECUTION LAYER begins work
```

---

## Implementation Priority

1. **Phase 1**: USER + ENIGMA PROFILE contracts
2. **Phase 2**: FREELANCING workspace (Platforms + Capabilities + Readiness)
3. **Phase 3**: FREELANCING workspace (Job Discovery + Applications)
4. **Phase 4**: FREELANCING workspace (Active Work + Execution)
5. **Phase 5**: BRAND & MARKETING workspace

---

## Brain Boundary

**FORBIDDEN: Frontend must NOT perform**:
- Reasoning
- Knowledge scoring
- Conflict resolution
- Profession reasoning
- Decision making
- Planning
- Quality gate validation
- Knowledge graph traversal
- Memory retrieval logic
- Governance enforcement

**ALLOWED: Frontend may only**:
- Display computed results from backend
- Accept user input and intent
- Show brain state as reported by backend
- Present options provided by backend
- Render UI based on backend state

---

## State Machines

### Workspace States

```
CREATED → ACTIVE → PAUSED → ACTIVE
ACTIVE → ARCHIVED
PAUSED → ARCHIVED
```

### Job Lifecycle States

```
DISCOVERED → ANALYZING → READY → APPLICATION_DRAFTED → APPLIED
APPLIED → WON → EXECUTING → COMPLETED → REFLECTION_PENDING
APPLIED → REJECTED
EXECUTING → DISPUTED → RESOLVED
REFLECTION_PENDING → COMPLETED
```

### Brand Campaign States

```
DRAFT → READY → RUNNING → PAUSED → RUNNING
RUNNING → COMPLETED
PAUSED → COMPLETED
READY → CANCELLED
```

### Application States

```
DRAFT → SUBMITTED → ACCEPTED → ACTIVE
SUBMITTED → REJECTED
ACTIVE → COMPLETED → PAID
ACTIVE → CANCELLED
```

### Active Work States

```
INITIATED → IN_PROGRESS → DELIVERED → PAID
IN_PROGRESS → ON_HOLD → IN_PROGRESS
DELIVERED → REVISION_REQUESTED → IN_PROGRESS
DELIVERED → DISPUTED → RESOLVED → PAID
```

---

## API Contracts

### USER Endpoints

#### GET /api/user/profile
**Request**: None (authenticated)
**Response**:
```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "created_at": "ISO8601",
  "last_active": "ISO8601",
  "subscription_tier": "free|pro|enterprise",
  "preferences": {},
  "linked_platforms": ["string"]
}
```
**Errors**: 401 (unauthorized), 404 (not found)

#### PUT /api/user/profile
**Request**:
```json
{
  "username": "string",
  "email": "string",
  "preferences": {}
}
```
**Response**: Same as GET
**Errors**: 400 (invalid input), 401 (unauthorized)

---

### ENIGMA PROFILE Endpoints

#### GET /api/profile
**Request**: None (authenticated)
**Response**:
```json
{
  "profile_id": "string",
  "user_id": "string",
  "display_name": "string",
  "tagline": "string",
  "capabilities": [
    {
      "capability_id": "string",
      "name": "string",
      "maturity_level": 1,
      "knowledge_coverage": 0.0,
      "evidence_count": 0,
      "execution_success_rate": 0.0,
      "last_used": "ISO8601"
    }
  ],
  "evidence_vault": {
    "portfolio_items": [],
    "certifications": [],
    "testimonials": [],
    "work_history": [],
    "skills_assessment": {}
  },
  "readiness_score": 0.0,
  "active_workspaces": ["string"],
  "knowledge_domains": ["string"],
  "profession_focus": "string"
}
```
**Errors**: 401 (unauthorized), 404 (not found)

#### PUT /api/profile
**Request**:
```json
{
  "display_name": "string",
  "tagline": "string",
  "profession_focus": "string"
}
```
**Response**: Same as GET
**Errors**: 400 (invalid input), 401 (unauthorized)

---

### WORKSPACE Endpoints

#### GET /api/workspaces
**Request**: None (authenticated)
**Response**:
```json
{
  "workspaces": [
    {
      "workspace_id": "string",
      "name": "string",
      "type": "freelancing|brand_marketing",
      "state": "CREATED|ACTIVE|PAUSED|ARCHIVED",
      "created_at": "ISO8601",
      "last_active": "ISO8601"
    }
  ]
}
```
**Errors**: 401 (unauthorized)

#### POST /api/workspaces/{workspace_id}/activate
**Request**: None
**Response**:
```json
{
  "workspace_id": "string",
  "state": "ACTIVE",
  "activated_at": "ISO8601"
}
```
**Errors**: 401 (unauthorized), 404 (not found), 409 (invalid state transition)

---

### FREELANCING Endpoints

#### GET /api/freelancing/platforms
**Request**: None (authenticated)
**Response**:
```json
{
  "platforms": [
    {
      "platform_id": "string",
      "platform_name": "string",
      "connection_status": "connected|disconnected|pending",
      "credits_balance": 0,
      "success_rate": 0.0,
      "knowledge_pack_id": "string"
    }
  ]
}
```
**Errors**: 401 (unauthorized)

#### POST /api/freelancing/platforms/{platform_id}/connect
**Request**:
```json
{
  "api_credentials": "string"
}
```
**Response**:
```json
{
  "platform_id": "string",
  "connection_status": "connected",
  "connected_at": "ISO8601"
}
```
**Errors**: 400 (invalid credentials), 401 (unauthorized), 404 (not found)

#### GET /api/freelancing/jobs
**Request**:
```json
{
  "platform": "string",
  "capabilities": ["string"],
  "limit": 20
}
```
**Response**:
```json
{
  "jobs": [
    {
      "job_id": "string",
      "platform": "string",
      "title": "string",
      "description": "string",
      "budget_min": 0.0,
      "budget_max": 0.0,
      "client_rating": 0.0,
      "posted_date": "ISO8601",
      "match_score": 0.0,
      "knowledge_match": 0.0,
      "execution_match": 0.0,
      "risk_level": "low|medium|high",
      "required_capabilities": ["string"],
      "deliverables": ["string"],
      "state": "DISCOVERED|ANALYZING|READY"
    }
  ]
}
```
**Errors**: 400 (invalid filters), 401 (unauthorized)

#### POST /api/freelancing/jobs/{job_id}/analyze
**Request**: None
**Response**:
```json
{
  "job_id": "string",
  "analysis": {
    "capability_match": {},
    "knowledge_gaps": ["string"],
    "execution_risks": ["string"],
    "recommended_approach": "string",
    "confidence": 0.0
  },
  "readiness": {
    "knowledge_readiness": 0.0,
    "execution_readiness": 0.0,
    "platform_readiness": 0.0,
    "proposal_readiness": 0.0,
    "status": "ready|research_required|not_ready"
  }
}
```
**Errors**: 401 (unauthorized), 404 (not found)

#### POST /api/freelancing/applications
**Request**:
```json
{
  "job_id": "string",
  "proposal_content": "string"
}
```
**Response**:
```json
{
  "application_id": "string",
  "job_id": "string",
  "status": "DRAFT",
  "created_at": "ISO8601"
}
```
**Errors**: 400 (invalid input), 401 (unauthorized), 404 (job not found)

#### POST /api/freelancing/applications/{application_id}/submit
**Request**: None
**Response**:
```json
{
  "application_id": "string",
  "status": "SUBMITTED",
  "submitted_at": "ISO8601"
}
```
**Errors**: 401 (unauthorized), 404 (not found), 409 (invalid state)

#### GET /api/freelancing/active-work
**Request**: None (authenticated)
**Response**:
```json
{
  "active_work": [
    {
      "work_id": "string",
      "job_id": "string",
      "execution_session_id": "string",
      "execution_plan": [],
      "current_step": 0,
      "progress": 0.0,
      "deliverables_completed": ["string"],
      "deliverables_pending": ["string"],
      "deadline": "ISO8601",
      "status": "INITIATED|IN_PROGRESS|DELIVERED|PAID|DISPUTED"
    }
  ]
}
```
**Errors**: 401 (unauthorized)

---

### BRAND & MARKETING Endpoints

#### GET /api/brand/identity
**Request**: None (authenticated)
**Response**:
```json
{
  "brand_id": "string",
  "name": "string",
  "positioning": "string",
  "value_proposition": "string",
  "tone_of_voice": "string",
  "visual_identity": {},
  "brand_guidelines": {}
}
```
**Errors**: 401 (unauthorized), 404 (not found)

#### PUT /api/brand/identity
**Request**:
```json
{
  "positioning": "string",
  "value_proposition": "string",
  "tone_of_voice": "string"
}
```
**Response**: Same as GET
**Errors**: 400 (invalid input), 401 (unauthorized)

#### GET /api/brand/content
**Request**:
```json
{
  "status": "draft|scheduled|published",
  "content_type": "string",
  "limit": 20
}
```
**Response**:
```json
{
  "content": [
    {
      "content_id": "string",
      "content_type": "string",
      "topic": "string",
      "purpose": "string",
      "target_channel": "string",
      "status": "draft|scheduled|published",
      "evidence_sources": ["string"],
      "generated_content": "string",
      "metrics": {},
      "created_at": "ISO8601"
    }
  ]
}
```
**Errors**: 400 (invalid filters), 401 (unauthorized)

#### POST /api/brand/content
**Request**:
```json
{
  "content_type": "string",
  "topic": "string",
  "purpose": "string",
  "target_channel": "string"
}
```
**Response**:
```json
{
  "content_id": "string",
  "status": "draft",
  "generated_content": "string",
  "created_at": "ISO8601"
}
```
**Errors**: 400 (invalid input), 401 (unauthorized)

#### GET /api/brand/campaigns
**Request**: None (authenticated)
**Response**:
```json
{
  "campaigns": [
    {
      "campaign_id": "string",
      "name": "string",
      "objective": "string",
      "channels": ["string"],
      "content_ids": ["string"],
      "start_date": "ISO8601",
      "end_date": "ISO8601",
      "budget": 0.0,
      "status": "DRAFT|READY|RUNNING|PAUSED|COMPLETED",
      "results": {}
    }
  ]
}
```
**Errors**: 401 (unauthorized)

---

## Error Contracts

All endpoints return standard error format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "timestamp": "ISO8601"
  }
}
```

**Common Error Codes**:
- `AUTH_REQUIRED` - 401
- `PERMISSION_DENIED` - 403
- `NOT_FOUND` - 404
- `INVALID_INPUT` - 400
- `INVALID_STATE` - 409
- `RATE_LIMITED` - 429
- `INTERNAL_ERROR` - 500

---

## Permission Boundaries

### User Permissions
- `profile:read` - Read own profile
- `profile:write` - Update own profile
- `workspace:read` - List workspaces
- `workspace:activate` - Activate workspace

### Freelancing Permissions
- `platform:read` - List platforms
- `platform:connect` - Connect platform
- `job:read` - Browse jobs
- `job:analyze` - Request job analysis
- `application:create` - Create application
- `application:submit` - Submit application
- `work:read` - View active work

### Brand Permissions
- `brand:read` - Read brand identity
- `brand:write` - Update brand identity
- `content:read` - List content
- `content:create` - Generate content
- `campaign:read` - List campaigns
- `campaign:create` - Create campaign

---

## Notes

- Frontend is stateless regarding intelligence - all state lives in cognitive core
- Frontend contracts are DTOs for API communication
- All readiness calculations happen backend
- Frontend only displays what the brain has computed
- Evidence flows from user → backend → frontend display
- State transitions are validated backend only
- Frontend must never bypass API contracts to access cognitive core directly
