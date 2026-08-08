# Frontend Contract

The Frontend Contract defines every page, its inputs, outputs, user actions, API requirements, state, and navigation. This is a specification document, not implementation.

## Frontend Architecture

```
Frontend
  ↓
Workspaces
  ↓
Pages
  ↓
Components
  ↓
State Management
  ↓
API Layer
  ↓
Backend
```

## Global Frontend Requirements

### Shared Components

All workspaces share:

1. **Navigation**: Common navigation bar
2. **Header**: Common header with user info
3. **Footer**: Common footer
4. **Theme**: Global theme configuration
5. **State**: Global state management
6. **Notifications**: Global notification system
7. **Authentication**: Global authentication system

### State Management

Global state includes:

- **User State**: User authentication and profile
- **Workspace State**: Current workspace
- **Theme State**: Theme preferences
- **Notification State**: Notification queue
- **API State**: API loading states

### API Layer

API layer provides:

- **Request Interception**: Intercepts all API requests
- **Response Handling**: Handles API responses
- **Error Handling**: Handles API errors
- **Caching**: Caches API responses
- **Retry Logic**: Retries failed requests

## Freelancing Workspace Pages

### 1. Dashboard

#### Purpose

Overview of freelance activity and performance metrics.

#### Inputs

- **Authentication**: User authentication token
- **Time Range**: Selected time range (7d, 30d, 90d, all)
- **Marketplace Filter**: Selected marketplace filter

#### Outputs

- **Job Discovery Metrics**: Jobs discovered, filtered, rejected
- **Readiness Coverage**: Percentage of jobs Enigma is ready for
- **Proposal Success Rate**: Proposals submitted vs accepted
- **Revenue Summary**: Total revenue, average per job
- **Active Jobs**: List of active jobs with status
- **Performance Trends**: Charts showing trends over time

#### User Actions

- **View Job Discovery Results**: Navigate to job discovery
- **Check Readiness Status**: View detailed readiness
- **Review Proposal Performance**: View proposal analytics
- **Track Revenue**: View revenue breakdown
- **Filter by Marketplace**: Change marketplace filter
- **Change Time Range**: Change time range filter

#### API Requirements

- `GET /api/freelance/dashboard` - Get dashboard data
- `GET /api/freelance/jobs/discovered` - Get discovered jobs
- `GET /api/freelance/readiness/summary` - Get readiness summary
- `GET /api/freelance/proposals/summary` - Get proposal summary
- `GET /api/freelance/revenue/summary` - Get revenue summary

#### State

- `selectedMarketplace`: Current marketplace filter
- `selectedTimeRange`: Current time range
- `dashboardData`: Dashboard metrics
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Job Discovery
- Proposals
- Execution
- Analytics

### 2. Job Discovery

#### Purpose

Browse and filter discovered freelance opportunities.

#### Inputs

- **Marketplace Selection**: Selected marketplace(s)
- **Keyword Filters**: Keyword search terms
- **Budget Range**: Min and max budget
- **Skill Filters**: Required skill filters
- **Category Filter**: Job category filter
- **Sort Order**: Sort by relevance, budget, deadline

#### Outputs

- **Filtered Job List**: List of jobs matching filters
- **Job Preview**: Quick preview of selected job
- **Classification Tags**: Profession and task tags
- **Readiness Indicators**: Visual readiness indicators
- **Job Count**: Total jobs matching filters

#### User Actions

- **Set Filters**: Apply filter criteria
- **Clear Filters**: Clear all filters
- **Sort Jobs**: Change sort order
- **View Job Details**: Open job details page
- **Check Readiness**: Quick readiness check
- **Request Proposal**: Request proposal draft

#### API Requirements

- `GET /api/freelance/jobs` - Get jobs with filters
- `GET /api/freelance/jobs/{id}` - Get job details
- `GET /api/freelance/jobs/{id}/classification` - Get classification
- `GET /api/freelance/jobs/{id}/readiness` - Get readiness score
- `POST /api/freelance/jobs/{id}/proposal-draft` - Request proposal draft

#### State

- `filters`: Applied filters
- `jobs`: Job list
- `selectedJob`: Currently selected job
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Dashboard
- Job Details
- Proposal Draft

### 3. Job Details

#### Purpose

View comprehensive job information and evaluation.

#### Inputs

- **Job ID**: Job identifier

#### Outputs

- **Full Job Description**: Complete job details
- **Classification Details**: Profession, task, requirements
- **Capability Requirements**: Required skills, knowledge, capabilities
- **Readiness Assessment**: Readiness score and breakdown
- **Missing Knowledge**: Missing knowledge areas
- **Missing Skills**: Missing skills
- **Missing Capabilities**: Missing capabilities
- **Recommendation**: Apply/learn/reject recommendation
- **Reason**: Explanation for recommendation

#### User Actions

- **View Requirements**: View detailed requirements
- **Check Capability Gaps**: View missing capabilities
- **View Learning Requirements**: View learning needs
- **Generate Proposal Draft**: Generate proposal draft
- **Save Job**: Save job for later
- **Share Job**: Share job with team

#### API Requirements

- `GET /api/freelance/jobs/{id}` - Get job details
- `GET /api/freelance/jobs/{id}/classification` - Get classification
- `GET /api/freelance/jobs/{id}/evaluation` - Get evaluation
- `GET /api/freelance/jobs/{id}/readiness` - Get readiness
- `GET /api/freelance/jobs/{id}/learning-requirements` - Get learning needs
- `POST /api/freelance/jobs/{id}/proposal-draft` - Generate proposal draft
- `POST /api/freelance/jobs/{id}/save` - Save job
- `POST /api/freelance/jobs/{id}/share` - Share job

#### State

- `jobId`: Current job ID
- `jobData`: Job details
- `classification`: Classification data
- `evaluation`: Evaluation data
- `readiness`: Readiness data
- `learningRequirements`: Learning requirements
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Job Discovery
- Proposal Draft
- Learning

### 4. Proposal Draft

#### Purpose

Review and edit AI-generated proposal drafts.

#### Inputs

- **Job ID**: Job identifier
- **Draft Preferences**: Tone, length, emphasis preferences

#### Outputs

- **Generated Proposal Draft**: AI-generated proposal
- **Governed Knowledge References**: References to governed knowledge
- **Timeline Estimate**: Estimated timeline
- **Questions for Client**: Questions to ask client
- **Proposal Sections**: Introduction, approach, deliverables, timeline, pricing

#### User Actions

- **Review Proposal**: Read through proposal
- **Edit Proposal**: Edit proposal sections
- **Add Custom Elements**: Add custom content
- **Adjust Timeline**: Adjust timeline estimate
- **Modify Questions**: Add/remove questions
- **Preview Proposal**: Preview final proposal
- **Save as Draft**: Save for later
- **Submit to Marketplace**: Submit proposal
- **Discard**: Discard proposal

#### API Requirements

- `GET /api/freelance/jobs/{id}/proposal-draft` - Get proposal draft
- `POST /api/freelance/jobs/{id}/proposal-draft` - Generate new draft
- `PUT /api/freelance/jobs/{id}/proposal-draft` - Update draft
- `POST /api/freelance/jobs/{id}/submit` - Submit proposal
- `POST /api/freelance/jobs/{id}/save-draft` - Save draft
- `DELETE /api/freelance/jobs/{id}/draft` - Discard draft

#### State

- `jobId`: Current job ID
- `draftContent`: Proposal content
- `editMode`: Edit mode state
- `unsavedChanges`: Unsaved changes flag
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Job Details
- Dashboard

### 5. Execution

#### Purpose

Monitor and manage active freelance work.

#### Inputs

- **Status Filter**: Filter by job status
- **Time Range**: Time range filter

#### Outputs

- **Active Jobs List**: List of active jobs
- **Progress Tracking**: Progress for each job
- **Deliverables Status**: Status of deliverables
- **Evidence Capture**: Captured evidence
- **Issues Log**: Issues encountered

#### User Actions

- **View Job Progress**: View detailed progress
- **Monitor Deliverables**: Check deliverable status
- **Review Evidence**: Review captured evidence
- **Handle Issues**: Address issues
- **Update Status**: Update job status
- **Add Notes**: Add notes to job

#### API Requirements

- `GET /api/freelance/execution/active` - Get active jobs
- `GET /api/freelance/execution/{id}` - Get execution details
- `GET /api/freelance/execution/{id}/progress` - Get progress
- `GET /api/freelance/execution/{id}/deliverables` - Get deliverables
- `GET /api/freelance/execution/{id}/evidence` - Get evidence
- `GET /api/freelance/execution/{id}/issues` - Get issues
- `PUT /api/freelance/execution/{id}/status` - Update status
- `POST /api/freelance/execution/{id}/notes` - Add notes

#### State

- `statusFilter`: Current status filter
- `timeRange`: Current time range
- `activeJobs`: Active jobs list
- `selectedJob`: Selected job
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Dashboard
- Job Details

### 6. Analytics

#### Purpose

View freelance performance analytics.

#### Inputs

- **Time Range**: Time range selection
- **Metric Selection**: Metrics to display
- **Breakdown**: Breakdown by category

#### Outputs

- **Revenue Charts**: Revenue over time
- **Success Rate Trends**: Proposal success rate trends
- **Readiness Coverage**: Readiness coverage over time
- **Capability Growth**: Capability growth charts
- **Marketplace Comparison**: Comparison across marketplaces
- **Performance Reports**: Detailed performance reports

#### User Actions

- **View Metrics**: View specific metrics
- **Filter by Time**: Change time range
- **Compare Marketplaces**: Compare marketplace performance
- **Export Reports**: Export analytics reports
- **Set Goals**: Set performance goals

#### API Requirements

- `GET /api/freelance/analytics/revenue` - Get revenue analytics
- `GET /api/freelance/analytics/success-rate` - Get success rate analytics
- `GET /api/freelance/analytics/readiness` - Get readiness analytics
- `GET /api/freelance/analytics/capabilities` - Get capability analytics
- `GET /api/freelance/analytics/marketplaces` - Get marketplace comparison
- `POST /api/freelance/analytics/export` - Export report
- `POST /api/freelance/analytics/goals` - Set goals

#### State

- `timeRange`: Current time range
- `selectedMetrics`: Selected metrics
- `breakdown`: Current breakdown
- `analyticsData`: Analytics data
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Dashboard

## Brand & Marketing Workspace Pages

### 1. Brand Dashboard

#### Purpose

Overview of brand performance and content activity.

#### Inputs

- **Time Range**: Time range selection
- **Platform Selection**: Platform filter

#### Outputs

- **Audience Metrics**: Followers, engagement, reach
- **Content Performance**: Content metrics
- **Brand Health Score**: Overall brand health
- **Engagement Trends**: Engagement trends
- **Content Calendar**: Upcoming content schedule

#### User Actions

- **View Brand Metrics**: View detailed metrics
- **Monitor Content Performance**: Track content
- **Check Audience Growth**: Monitor audience
- **Review Content Calendar**: View schedule

#### API Requirements

- `GET /api/brand/dashboard` - Get dashboard data
- `GET /api/brand/audience` - Get audience metrics
- `GET /api/brand/content/performance` - Get content performance
- `GET /api/brand/calendar` - Get content calendar

#### State

- `timeRange`: Current time range
- `platformFilter`: Platform filter
- `dashboardData`: Dashboard data
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Content Creation
- Social Media
- Analytics

### 2. Content Creation

#### Purpose

Create and manage marketing content.

#### Inputs

- **Content Type**: Type of content to create
- **Topic**: Content topic
- **Platform**: Target platform
- **Tone**: Content tone preference

#### Outputs

- **AI-Generated Content**: Generated content
- **SEO Suggestions**: SEO optimization suggestions
- **Publishing Schedule**: Scheduled publication
- **Performance Predictions**: Predicted performance

#### User Actions

- **Generate Content**: Generate new content
- **Edit Content**: Edit generated content
- **Schedule Publication**: Schedule for later
- **Publish Immediately**: Publish now
- **View Analytics**: View content analytics

#### API Requirements

- `POST /api/brand/content/generate` - Generate content
- `PUT /api/brand/content/{id}` - Update content
- `POST /api/brand/content/{id}/publish` - Publish content
- `POST /api/brand/content/{id}/schedule` - Schedule content
- `GET /api/brand/content/{id}/analytics` - Get content analytics

#### State

- `contentType`: Current content type
- `selectedContent`: Selected content
- `editMode`: Edit mode state
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Brand Dashboard
- Content Calendar

### 3. Social Media

#### Purpose

Manage social media presence and engagement.

#### Inputs

- **Platform Selection**: Selected platform
- **Content Type**: Content type filter
- **Time Range**: Time range filter

#### Outputs

- **Platform Metrics**: Platform-specific metrics
- **Audience Insights**: Audience data
- **Engagement Data**: Engagement metrics
- **Posting Schedule**: Scheduled posts
- **Performance Reports**: Performance reports

#### User Actions

- **Schedule Posts**: Schedule posts
- **Monitor Engagement**: Monitor engagement
- **Respond to Comments**: Respond to interactions
- **Analyze Performance**: Analyze performance

#### API Requirements

- `GET /api/brand/social/{platform}` - Get platform data
- `POST /api/brand/social/{platform}/post` - Create post
- `GET /api/brand/social/{platform}/analytics` - Get analytics
- `POST /api/brand/social/{platform}/respond` - Respond to comments

#### State

- `selectedPlatform`: Current platform
- `timeRange`: Current time range
- `socialData`: Social media data
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Brand Dashboard
- Content Creation

### 4. Brand Assets

#### Purpose

Manage brand identity assets.

#### Inputs

- **Asset Type**: Type of asset to view/manage

#### Outputs

- **Logo Variations**: Logo files
- **Brand Guidelines**: Brand guidelines document
- **Color Palette**: Color palette
- **Typography**: Typography settings
- **Visual Identity**: Visual identity elements

#### User Actions

- **View Assets**: View brand assets
- **Update Guidelines**: Update brand guidelines
- **Generate Variations**: Generate asset variations
- **Download Assets**: Download assets

#### API Requirements

- `GET /api/brand/assets` - Get brand assets
- `PUT /api/brand/assets` - Update assets
- `POST /api/brand/assets/generate` - Generate variations
- `GET /api/brand/assets/download` - Download assets

#### State

- `assetType`: Current asset type
- `editMode`: Edit mode state
- `assetsData`: Assets data
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Brand Dashboard

### 5. Brand Analytics

#### Purpose

Deep dive into brand performance analytics.

#### Inputs

- **Time Range**: Time range selection
- **Metric Breakdown**: Metrics to analyze

#### Outputs

- **Audience Growth Charts**: Audience growth over time
- **Content Performance**: Content performance metrics
- **Engagement Analysis**: Engagement analysis
- **Conversion Funnels**: Conversion funnels
- **ROI Metrics**: Return on investment metrics

#### User Actions

- **View Detailed Analytics**: View detailed metrics
- **Compare Time Periods**: Compare periods
- **Export Reports**: Export reports
- **Set Goals**: Set brand goals

#### API Requirements

- `GET /api/brand/analytics/audience` - Get audience analytics
- `GET /api/brand/analytics/content` - Get content analytics
- `GET /api/brand/analytics/conversion` - Get conversion analytics
- `POST /api/brand/analytics/export` - Export report
- `POST /api/brand/analytics/goals` - Set goals

#### State

- `timeRange`: Current time range
- `selectedMetrics`: Selected metrics
- `analyticsData`: Analytics data
- `loading`: Loading state
- `error`: Error state

#### Navigation

- Brand Dashboard

## Future Workspace Pages

### Academy Workspace Pages

- Curriculum Overview
- Lessons
- Exercises
- Research Tasks
- Exams
- Certifications
- Progress Tracking

### Knowledge Workspace Pages

- Knowledge Graph Visualization
- Concept Explorer
- Evidence View
- Maturity Tracking
- Conflict Resolution
- Knowledge Search

### Brain Explorer Workspace Pages

- Reasoning Session Viewer
- Decision History
- Capability Map
- Learning Progress
- Evidence Vault
- Performance Metrics

### Settings Workspace Pages

- Marketplace Configuration
- Intelligence Domain Settings
- Academy Settings
- Knowledge Governance Settings
- Performance Settings
- Integration Settings

## Frontend Implementation Guidelines

### Component Guidelines

1. **Reusable Components**: Create reusable components for common UI patterns
2. **Consistent Styling**: Use consistent styling across workspaces
3. **Responsive Design**: Ensure responsive design for all screen sizes
4. **Accessibility**: Ensure accessibility compliance
5. **Performance**: Optimize for performance

### State Management Guidelines

1. **Global State**: Use global state for cross-workspace data
2. **Local State**: Use local state for workspace-specific data
3. **Persistence**: Persist critical state to backend
4. **Synchronization**: Synchronize state across tabs/windows
5. **Optimization**: Optimize state updates for performance

### API Integration Guidelines

1. **Error Handling**: Handle API errors gracefully
2. **Loading States**: Show loading states during API calls
3. **Caching**: Cache API responses appropriately
4. **Retry Logic**: Implement retry logic for failed requests
5. **Rate Limiting**: Respect API rate limits

### Navigation Guidelines

1. **Breadcrumb Navigation**: Show breadcrumb navigation
2. **Back Navigation**: Support back navigation
3. **Deep Linking**: Support deep linking to pages
4. **Navigation Guards**: Implement navigation guards
5. **Lazy Loading**: Lazy load pages for performance
