# Workspaces

Workspaces are the primary user interfaces for interacting with Enigma. Each workspace serves a specific business purpose while sharing common infrastructure.

## Workspace Architecture

```
Frontend
  ↓
Workspaces
  ↓
Business Modules
  ↓
Shared Intelligence
  ↓
Cognitive Core
```

## Initial Workspaces

### 1. Freelancing Workspace

#### Purpose

The Freelancing workspace is the primary interface for discovering, evaluating, and executing freelance work across marketplaces.

#### Pages

##### Dashboard

**Purpose**: Overview of freelance activity and performance

**Inputs**:
- User authentication
- Selected marketplace filters
- Time range selection

**Outputs**:
- Job discovery metrics
- Readiness coverage
- Proposal success rate
- Revenue summary
- Active jobs list

**User Actions**:
- View job discovery results
- Check readiness status
- Review proposal performance
- Track revenue

**API Requirements**:
- GET /api/freelance/dashboard
- GET /api/freelance/jobs/discovered
- GET /api/freelance/readiness/summary

**State**:
- Selected marketplace
- Time range filter
- Sort order

**Navigation**:
- Job Discovery
- Proposals
- Execution
- Analytics

##### Job Discovery

**Purpose**: Browse and filter discovered freelance opportunities

**Inputs**:
- Marketplace selection
- Keyword filters
- Budget range
- Skill filters

**Outputs**:
- Filtered job list
- Job details
- Classification results
- Readiness scores

**User Actions**:
- Filter jobs by criteria
- View job details
- Check readiness
- Request proposal draft

**API Requirements**:
- GET /api/freelance/jobs
- GET /api/freelance/jobs/{id}
- GET /api/freelance/jobs/{id}/classification
- GET /api/freelance/jobs/{id}/readiness

**State**:
- Filter parameters
- Selected job
- View mode (list/detail)

**Navigation**:
- Dashboard
- Job Details
- Proposal Draft

##### Job Details

**Purpose**: View comprehensive job information and evaluation

**Inputs**:
- Job ID

**Outputs**:
- Full job description
- Classification details
- Capability requirements
- Readiness assessment
- Missing knowledge/skills
- Recommendation

**User Actions**:
- View job requirements
- Check capability gaps
- View learning requirements
- Generate proposal draft

**API Requirements**:
- GET /api/freelance/jobs/{id}
- GET /api/freelance/jobs/{id}/evaluation
- GET /api/freelance/jobs/{id}/learning-requirements

**State**:
- Selected job
- Evaluation results

**Navigation**:
- Job Discovery
- Proposal Draft
- Learning

##### Proposal Draft

**Purpose**: Review and edit AI-generated proposal drafts

**Inputs**:
- Job ID
- Draft preferences

**Outputs**:
- Generated proposal draft
- Governed knowledge references
- Timeline estimate
- Questions for client

**User Actions**:
- Review proposal
- Edit proposal
- Add custom elements
- Submit to marketplace
- Save as draft

**API Requirements**:
- GET /api/freelance/jobs/{id}/proposal-draft
- POST /api/freelance/jobs/{id}/proposal-draft
- PUT /api/freelance/jobs/{id}/proposal-draft
- POST /api/freelance/jobs/{id}/submit

**State**:
- Job ID
- Draft content
- Edit mode

**Navigation**:
- Job Details
- Dashboard

##### Execution

**Purpose**: Monitor and manage active freelance work

**Inputs**:
- Filter by status
- Time range

**Outputs**:
- Active jobs list
- Progress tracking
- Deliverables status
- Evidence capture

**User Actions**:
- View job progress
- Monitor deliverables
- Review evidence
- Handle issues

**API Requirements**:
- GET /api/freelance/execution/active
- GET /api/freelance/execution/{id}
- GET /api/freelance/execution/{id}/evidence

**State**:
- Filter parameters
- Selected job

**Navigation**:
- Dashboard
- Job Details

##### Analytics

**Purpose**: View freelance performance analytics

**Inputs**:
- Time range
- Metric selection

**Outputs**:
- Revenue charts
- Success rate trends
- Readiness coverage
- Capability growth
- Marketplace comparison

**User Actions**:
- View performance metrics
- Filter by time
- Compare marketplaces
- Export reports

**API Requirements**:
- GET /api/freelance/analytics/revenue
- GET /api/freelance/analytics/success-rate
- GET /api/freelance/analytics/readiness

**State**:
- Time range
- Selected metrics

**Navigation**:
- Dashboard

#### User Flow

1. **Discovery**: User browses discovered jobs on Dashboard → Job Discovery
2. **Evaluation**: User selects job → Job Details → evaluates readiness
3. **Learning**: If not ready → Learning requirements → Academy → Research
4. **Proposal**: If ready → Proposal Draft → edit → submit
5. **Execution**: If awarded → Execution → monitor progress
6. **Reflection**: After completion → evidence captured → knowledge updated

#### Required Backend APIs

- Job Discovery APIs
- Classification APIs
- Readiness APIs
- Proposal APIs
- Execution APIs
- Analytics APIs

#### Shared Intelligence

- **SEO**: For SEO-related jobs
- **Copywriting**: For content-related jobs
- **Marketing**: For marketing-related jobs
- **Analytics**: For performance tracking

### 2. Brand & Marketing Workspace

#### Purpose

The Brand & Marketing workspace manages Enigma's brand presence, content creation, and audience growth.

#### Pages

##### Brand Dashboard

**Purpose**: Overview of brand performance and content activity

**Inputs**:
- Time range selection
- Platform selection

**Outputs**:
- Audience metrics
- Content performance
- Brand health score
- Engagement trends
- Content calendar

**User Actions**:
- View brand metrics
- Monitor content performance
- Check audience growth
- Review content calendar

**API Requirements**:
- GET /api/brand/dashboard
- GET /api/brand/audience
- GET /api/brand/content/performance

**State**:
- Time range
- Platform filter

**Navigation**:
- Content Creation
- Social Media
- Analytics

##### Content Creation

**Purpose**: Create and manage marketing content

**Inputs**:
- Content type
- Topic
- Platform

**Outputs**:
- AI-generated content
- SEO suggestions
- Publishing schedule
- Performance predictions

**User Actions**:
- Generate content
- Edit content
- Schedule publication
- Publish immediately
- View analytics

**API Requirements**:
- POST /api/brand/content/generate
- PUT /api/brand/content/{id}
- POST /api/brand/content/{id}/publish
- GET /api/brand/content/schedule

**State**:
- Content type
- Selected content
- Edit mode

**Navigation**:
- Brand Dashboard
- Content Calendar

##### Social Media

**Purpose**: Manage social media presence and engagement

**Inputs**:
- Platform selection
- Content type

**Outputs**:
- Platform-specific metrics
- Audience insights
- Engagement data
- Posting schedule

**User Actions**:
- Schedule posts
- Monitor engagement
- Respond to comments
- Analyze performance

**API Requirements**:
- GET /api/brand/social/{platform}
- POST /api/brand/social/{platform}/post
- GET /api/brand/social/{platform}/analytics

**State**:
- Selected platform
- Time range

**Navigation**:
- Brand Dashboard
- Content Creation

##### Brand Assets

**Purpose**: Manage brand identity assets

**Inputs**:
- Asset type

**Outputs**:
- Logo variations
- Brand guidelines
- Color palette
- Typography
- Visual identity

**User Actions**:
- View brand assets
- Update guidelines
- Generate variations
- Download assets

**API Requirements**:
- GET /api/brand/assets
- PUT /api/brand/assets
- POST /api/brand/assets/generate

**State**:
- Asset type
- Edit mode

**Navigation**:
- Brand Dashboard

##### Brand Analytics

**Purpose**: Deep dive into brand performance analytics

**Inputs**:
- Time range
- Metric breakdown

**Outputs**:
- Audience growth charts
- Content performance
- Engagement analysis
- Conversion funnels
- ROI metrics

**User Actions**:
- View detailed analytics
- Compare time periods
- Export reports
- Set goals

**API Requirements**:
- GET /api/brand/analytics/audience
- GET /api/brand/analytics/content
- GET /api/brand/analytics/conversion

**State**:
- Time range
- Selected metrics

**Navigation**:
- Brand Dashboard

#### User Flow

1. **Planning**: User reviews brand strategy → sets content goals
2. **Creation**: User generates content → edits → schedules/publishes
3. **Distribution**: Content posted to platforms → monitored
4. **Engagement**: User monitors engagement → responds to interactions
5. **Analysis**: User reviews analytics → adjusts strategy

#### Required Backend APIs

- Content Generation APIs
- Social Media APIs
- Brand Asset APIs
- Analytics APIs

#### Shared Intelligence

- **Branding**: Brand strategy and identity
- **Copywriting**: Content creation
- **Social Media**: Platform-specific optimization
- **Analytics**: Performance tracking
- **SEO**: Content optimization

## Future Workspaces

### 3. Academy Workspace

#### Purpose

The Academy workspace provides structured learning experiences for Enigma to acquire new capabilities.

#### Pages

- Curriculum Overview
- Lessons
- Exercises
- Research Tasks
- Exams
- Certifications
- Progress Tracking

#### Shared Intelligence

- All intelligence domains (for learning)

### 4. Knowledge Workspace

#### Purpose

The Knowledge workspace provides visibility into Enigma's governed knowledge base.

#### Pages

- Knowledge Graph Visualization
- Concept Explorer
- Evidence View
- Maturity Tracking
- Conflict Resolution
- Knowledge Search

#### Shared Intelligence

- All intelligence domains (knowledge source)

### 5. Brain Explorer Workspace

#### Purpose

The Brain Explorer workspace provides visibility into Enigma's cognitive processes.

#### Pages

- Reasoning Session Viewer
- Decision History
- Capability Map
- Learning Progress
- Evidence Vault
- Performance Metrics

#### Shared Intelligence

- All intelligence domains (cognitive context)

### 6. Settings Workspace

#### Purpose

The Settings workspace allows configuration of Enigma's behavior and preferences.

#### Pages

- Marketplace Configuration
- Intelligence Domain Settings
- Academy Settings
- Knowledge Governance Settings
- Performance Settings
- Integration Settings

#### Shared Intelligence

- None (configuration only)

## Workspace Integration

### Shared Components

All workspaces share:

- **Navigation**: Common navigation structure
- **State Management**: Global state persistence
- **Authentication**: User authentication
- **Notifications**: System notifications
- **Theme**: Visual theme

### Cross-Workspace Workflows

1. **Freelancing → Academy**: Jobs requiring learning trigger Academy lessons
2. **Academy → Freelancing**: Learned skills improve readiness
3. **Brand → Freelancing**: Brand presence improves freelance proposals
4. **Freelancing → Brand**: Freelance experience informs content
5. **Knowledge → All**: Governed knowledge available to all workspaces

### Workspace State

Each workspace maintains:

- **Local State**: Workspace-specific state
- **Global State**: Shared across workspaces
- **Backend State**: Persisted in backend
- **User Preferences**: User-specific settings

## Workspace Security

### Access Control

- **Public Workspaces**: Dashboard, Knowledge, Brain Explorer
- **Authenticated Workspaces**: Freelancing, Brand & Marketing, Academy, Settings
- **Admin Workspaces**: Settings (full access)

### Data Isolation

- **Module Data**: Isolated by business module
- **User Data**: Isolated by user
- **Evidence**: Governed and isolated
- **Knowledge**: Shared but governed

## Workspace Performance

### Optimization Strategies

- **Lazy Loading**: Load content on demand
- **Caching**: Cache frequently accessed data
- **Pagination**: Paginate large lists
- **Debouncing**: Debounce user actions
- **Virtual Scrolling**: Virtual scroll long lists

### Monitoring

- **Page Load Time**: Track page load performance
- **API Response Time**: Track API performance
- **User Actions**: Track user interactions
- **Errors**: Track and report errors
