# ENIGMA Frontend Migration Plan

**Date**: 2026-08-07  
**Based on**: `frontend-inventory.md`  
**Target Architecture**: Control Plane over Cognitive Core  
**Reference**: `frontend-contracts.md`

---

## Current State

### Existing Frontend Model
- **Architecture**: Linear Product Journey
- **Navigation**: Phase-based (Research → Decisions → Strategy → Execution → Analytics → Learning)
- **User Flow**: Goal Selection → Product Creation → Linear Phases
- **Pages**: 15 pages (2 auth + 13 app)
- **Components**: 3 reusable components
- **JavaScript Modules**: 12 ES modules
- **Design**: Modern dark theme with glass morphism, Arabic RTL

### Current Strengths
- Solid API layer with authentication
- Clean ES module architecture
- No intelligence leakage (proper Control Plane)
- Good developer tools (dashboard, live console)
- Reusable UI components
- Modern design system

### Current Weaknesses
- Linear product journey doesn't match workspace architecture
- Phase-based navigation conflicts with workspace model
- Hardcoded goals limit flexibility
- Manual user type selection
- Mixed concerns (product management + engine monitoring)

---

## Target State

### New Architecture
```
USER
 ↓
ENIGMA PROFILE
 ↓
WORKSPACES
 ├── FREELANCING
 └── BRAND & MARKETING
```

### New Navigation Model
- **Workspace-based**: Users activate and switch between workspaces
- **Profile-centric**: User identity and capabilities drive experience
- **Contract-driven**: All UI backed by API contracts
- **Control Plane**: Frontend displays, backend computes

### New Page Structure
```
Auth Pages (KEEP)
├── login.html
└── register.html

Profile Pages (NEW)
├── profile.html (ENIGMA PROFILE)
└── profile-edit.html

Workspace Landing (NEW)
└── workspaces.html (Workspace selector)

Freelancing Workspace (REFACTOR from existing)
├── freelancing-home.html
├── platforms.html
├── capabilities.html
├── jobs.html
├── applications.html
└── active-work.html

Brand & Marketing Workspace (NEW)
├── brand-home.html
├── brand-identity.html
├── content.html
└── campaigns.html

Developer Tools (KEEP - Separated)
├── dashboard.html
└── live-console.html
```

---

## KEEP

### Components to Keep Without Changes

#### API Layer
- **File**: `js/api.js`
- **Reason**: Solid HTTP client with auth, error handling, loading states
- **Changes**: Update endpoint URLs to match new API contracts
- **Mapping**: 
  - `/auth/me` → `GET /api/user/profile`
  - `/auth/login` → `POST /api/user/login` (if different)
  - `/auth/register` → `POST /api/user/register` (if different)

#### Authentication
- **File**: `js/auth.js`
- **Reason**: Working token-based auth, session management
- **Changes**: Update API endpoints to USER Contract
- **Mapping**: Use USER Contract endpoints

#### Router
- **File**: `js/router.js`
- **Reason**: Good ES module loading architecture
- **Changes**: Update route list for new page structure
- **Mapping**: Add new workspace routes

#### Dashboard
- **File**: `js/dashboard.js` + `pages/dashboard.html`
- **Reason**: Valuable developer tool for engine monitoring
- **Changes**: None (keep as developer tool)
- **Mapping**: Keep separate from main user Control Plane

#### Live Console
- **File**: `js/live-console.js` + `pages/live-console.html`
- **Reason**: Critical for worker observability
- **Changes**: None (WebSocket endpoint stays same)
- **Mapping**: Keep separate from main user Control Plane

#### UI Components
- **Files**: All CSS classes, `components/sidebar.html`, `components/mobile-header.html`
- **Reason**: Architecture-agnostic, reusable design system
- **Changes**: Update sidebar navigation for workspace model
- **Mapping**: Keep design system, update navigation structure

#### Design System
- **Files**: `css/style.css`, Tailwind config in `index.html`
- **Reason**: Modern, cohesive design
- **Changes**: None
- **Mapping**: Keep entire design system

---

## REFACTOR

### Components Requiring Structural Changes

#### Sidebar
- **File**: `components/sidebar.html`
- **Current**: Phase-based navigation (Research, Decisions, Strategy, Execution, Analytics, Learning)
- **Target**: Workspace-based navigation (Freelancing, Brand & Marketing)
- **Changes**:
  - Remove phase-based links
  - Add workspace selector
  - Add profile link
  - Keep developer tools (Dashboard, Live Console) in separate section
- **Mapping**: 
  ```
  Current: Home → Workspace → Brain → User Brain → Products → Research → Decisions → Strategy → Execution → Analytics → Learning → Dashboard → Live Console
  Target: Profile → Workspaces → [Active Workspace Content] → [Developer Tools Section]
  ```

#### Home Page
- **File**: `pages/home.html`
- **Current**: Goal selection (6 predefined goals)
- **Target**: Workspace landing page
- **Changes**:
  - Remove hardcoded goal cards
  - Add workspace cards (Freelancing, Brand & Marketing)
  - Add workspace activation buttons
  - Show current workspace status
- **Mapping**: Convert to workspace selector per WORKSPACE Contract

#### Workspace Page
- **File**: `pages/workspace.html`
- **Current**: Activity overview with products, brain activity, today's mission
- **Target**: Workspace-specific landing
- **Changes**:
  - Make workspace-aware (show active workspace)
  - Remove hardcoded product journey elements
  - Add workspace-specific metrics
  - Add workspace switcher
- **Mapping**: Convert to workspace dashboard per WORKSPACE Contract

#### Brain Chat
- **File**: `pages/brain.html` + `js/chat.js`
- **Current**: Master Brain chat interface
- **Target**: Profile-integrated brain communication
- **Changes**:
  - Move into ENIGMA PROFILE context
  - Use API contracts for brain communication
  - Add profile context to chat
- **Mapping**: Integrate with ENIGMA PROFILE Contract

#### User Brain
- **File**: `pages/user-brain.html` + `js/userbrain.js`
- **Current**: Manual user type selection with journey tracking
- **Target**: ENIGMA PROFILE with capability selection
- **Changes**:
  - Remove manual user type selection
  - Add capability selection interface
  - Add evidence vault display
  - Add readiness score visualization
  - Add profession focus selection
- **Mapping**: Convert to ENIGMA PROFILE Contract

#### Products Page
- **File**: `pages/products.html` + `js/products.js`
- **Current**: Product management with status tracking
- **Target**: Freelancing workspace product management
- **Changes**:
  - Add workspace context
  - Update API endpoints to FREELANCING Contract
  - Add platform-specific product attributes
- **Mapping**: Move to FREELANCING Workspace Contract

---

## MOVE

### Components Requiring Location Change

#### Research Phase
- **File**: `pages/research.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/research.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Job Discovery

#### Decisions Phase
- **File**: `pages/decisions.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/decisions.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Readiness Assessment

#### Strategy Phase
- **File**: `pages/strategy.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/strategy.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Application Strategy

#### Execution Phase
- **File**: `pages/execution.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/execution.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Active Work

#### Analytics Phase
- **File**: `pages/analytics.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/analytics.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Revenue/Events

#### Learning Phase
- **File**: `pages/learning.html`
- **Current**: Standalone phase page
- **Target**: Part of FREELANCING workspace
- **Changes**:
  - Move to `pages/freelancing/learning.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Reflection

#### Add Product Modal
- **File**: `components/add-product-modal.html`
- **Current**: Global component
- **Target**: FREELANCING workspace component
- **Changes**:
  - Move to `pages/freelancing/add-product-modal.html`
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace

#### Onboarding
- **File**: `js/onboarding.js`
- **Current**: Global onboarding flow
- **Target**: FREELANCING workspace onboarding
- **Changes**:
  - Add workspace context
  - Update to use FREELANCING Contract
- **Mapping**: FREELANCING Workspace → Platform Connection

---

## REPLACE

### Components Conflicting with Target Architecture

#### Goal Selection
- **File**: `pages/home.html` (goal cards section)
- **Current**: 6 hardcoded goals (first sale, increase sales, launch product, build brand, content creation, custom)
- **Target**: Workspace selection
- **Changes**:
  - Remove goal cards entirely
  - Replace with workspace cards (Freelancing, Brand & Marketing)
  - Add workspace activation interface
- **Mapping**: Replace with WORKSPACE Contract

#### Phase Navigation
- **File**: `components/sidebar.html` (phase links)
- **Current**: Research, Decisions, Strategy, Execution, Analytics, Learning
- **Target**: Workspace navigation
- **Changes**:
  - Remove all phase-based links
  - Replace with workspace links
  - Add workspace-specific sub-navigation
- **Mapping**: Replace with WORKSPACE Contract

#### User Type Selection
- **File**: `pages/user-brain.html` (user type buttons)
- **Current**: Manual selection (Seller, Service Provider, Content Creator, Investor)
- **Target**: ENIGMA PROFILE with automatic detection
- **Changes**:
  - Remove manual selection buttons
  - Replace with capability selection
  - Add evidence-based profile building
- **Mapping**: Replace with ENIGMA PROFILE Contract

---

## DELETE

### Components Identified for Deletion

**NONE**

No components were identified as truly obsolete, unused, or duplicated. All current pages serve a purpose in the existing product journey model. The migration strategy is to REFACTOR/MOVE/REPLACE rather than DELETE.

---

## New Components Required

### ENIGMA PROFILE Pages

#### Profile Main Page
- **File**: `pages/profile.html`
- **Purpose**: Display user's ENIGMA PROFILE
- **Features**:
  - Display name, tagline, profession focus
  - Capability list with maturity levels
  - Evidence vault summary
  - Readiness score visualization
  - Active workspaces
- **Contract**: ENIGMA PROFILE Contract

#### Profile Edit Page
- **File**: `pages/profile-edit.html`
- **Purpose**: Edit ENIGMA PROFILE
- **Features**:
  - Edit display name, tagline
  - Select profession focus
  - Add/remove capabilities
  - Upload evidence
- **Contract**: ENIGMA PROFILE Contract

### Workspace Pages

#### Workspace Landing
- **File**: `pages/workspaces.html`
- **Purpose**: Workspace selector and manager
- **Features**:
  - List available workspaces
  - Show workspace states (CREATED, ACTIVE, PAUSED)
  - Activate/deactivate workspaces
  - Show workspace summaries
- **Contract**: WORKSPACE Contract

### FREELANCING Workspace Pages

#### Freelancing Home
- **File**: `pages/freelancing/home.html`
- **Purpose**: Freelancing workspace dashboard
- **Features**:
  - Platform connection status
  - Active jobs summary
  - Applications summary
  - Active work summary
  - Revenue overview
- **Contract**: FREELANCING Contract

#### Platforms
- **File**: `pages/freelancing/platforms.html`
- **Purpose**: Platform management
- **Features**:
  - List platforms (Upwork, Freelancer, Fiverr, Khamsat)
  - Connection status
  - Connect/disconnect platforms
  - Show credits balance
  - Platform-specific knowledge pack status
- **Contract**: FREELANCING Contract → Platforms

#### Capabilities
- **File**: `pages/freelancing/capabilities.html`
- **Purpose**: Capability selection for freelancing
- **Features**:
  - Select capabilities to offer
  - Platform recommendations
  - Market demand display
  - Capability readiness scores
- **Contract**: FREELANCING Contract → Capabilities Selection

#### Jobs
- **File**: `pages/freelancing/jobs.html`
- **Purpose**: Job discovery and analysis
- **Features**:
  - Job listing with filters
  - Match scores
  - Knowledge/execution match
  - Risk levels
  - Job analysis interface
  - Readiness assessment display
- **Contract**: FREELANCING Contract → Job Discovery

#### Applications
- **File**: `pages/freelancing/applications.html`
- **Purpose**: Application management
- **Features**:
  - Application listing
  - Draft proposals
  - Submitted applications
  - Application status tracking
  - Proposal generation interface
- **Contract**: FREELANCING Contract → Applications

#### Active Work
- **File**: `pages/freelancing/active-work.html`
- **Purpose**: Active work tracking
- **Features**:
  - Active jobs list
  - Execution plan display
  - Progress tracking
  - Deliverables status
  - Deadline management
- **Contract**: FREELANCING Contract → Active Work

### BRAND & MARKETING Workspace Pages

#### Brand Home
- **File**: `pages/brand/home.html`
- **Purpose**: Brand workspace dashboard
- **Features**:
  - Brand identity summary
  - Content overview
  - Campaign status
  - Channel metrics
  - Lead summary
- **Contract**: BRAND & MARKETING Contract

#### Brand Identity
- **File**: `pages/brand/identity.html`
- **Purpose**: Brand identity management
- **Features**:
  - Edit positioning, value proposition
  - Tone of voice settings
  - Visual identity settings
  - Brand guidelines
- **Contract**: BRAND & MARKETING Contract → Brand Identity

#### Content
- **File**: `pages/brand/content.html`
- **Purpose**: Content management
- **Features**:
  - Content listing
  - Content generation interface
  - Content scheduling
  - Content metrics
  - Evidence source linking
- **Contract**: BRAND & MARKETING Contract → Content Engine

#### Campaigns
- **File**: `pages/brand/campaigns.html`
- **Purpose**: Campaign management
- **Features**:
  - Campaign listing
  - Campaign creation
  - Campaign status tracking
  - Campaign results
  - Channel management
- **Contract**: BRAND & MARKETING Contract → Campaigns

### JavaScript Modules Required

#### Profile Module
- **File**: `js/profile.js`
- **Purpose**: ENIGMA PROFILE management
- **Functions**:
  - `loadProfile()` - Load user profile
  - `updateProfile()` - Update profile data
  - `selectCapabilities()` - Select capabilities
  - `uploadEvidence()` - Upload evidence
- **Contract**: ENIGMA PROFILE Contract

#### Workspace Module
- **File**: `js/workspaces.js`
- **Purpose**: Workspace management
- **Functions**:
  - `loadWorkspaces()` - Load available workspaces
  - `activateWorkspace()` - Activate a workspace
  - `deactivateWorkspace()` - Deactivate a workspace
  - `switchWorkspace()` - Switch active workspace
- **Contract**: WORKSPACE Contract

#### Freelancing Module
- **File**: `js/freelancing.js`
- **Purpose**: FREELANCING workspace logic
- **Functions**:
  - `loadPlatforms()` - Load platform data
  - `connectPlatform()` - Connect platform
  - `loadJobs()` - Load job listings
  - `analyzeJob()` - Request job analysis
  - `createApplication()` - Create application
  - `submitApplication()` - Submit application
  - `loadActiveWork()` - Load active work
- **Contract**: FREELANCING Contract

#### Brand Module
- **File**: `js/brand.js`
- **Purpose**: BRAND & MARKETING workspace logic
- **Functions**:
  - `loadBrandIdentity()` - Load brand data
  - `updateBrandIdentity()` - Update brand
  - `loadContent()` - Load content
  - `generateContent()` - Generate content
  - `loadCampaigns()` - Load campaigns
  - `createCampaign()` - Create campaign
- **Contract**: BRAND & MARKETING Contract

---

## Migration Order

### Phase 1: Foundation (No User Impact)
1. **Update API endpoints** in `js/api.js` to match new contracts
2. **Update authentication** in `js/auth.js` to use USER Contract
3. **Create new JavaScript modules**:
   - `js/profile.js`
   - `js/workspaces.js`
   - `js/freelancing.js`
   - `js/brand.js`
4. **Create new page templates**:
   - `pages/profile.html`
   - `pages/workspaces.html`
   - `pages/freelancing/*.html`
   - `pages/brand/*.html`

### Phase 2: Navigation Refactor (User Visible)
5. **Refactor sidebar** to workspace-based navigation
6. **Refactor home page** to workspace landing
7. **Update router** with new route structure
8. **Add workspace switching logic**

### Phase 3: Profile Implementation (User Visible)
9. **Implement ENIGMA PROFILE pages**
10. **Move user-brain functionality** to profile
11. **Add capability selection interface**
12. **Add evidence vault display**

### Phase 4: Freelancing Workspace (User Visible)
13. **Move existing phase pages** to freelancing directory
14. **Update freelancing pages** to use new contracts
15. **Add platform management interface**
16. **Add job discovery interface**
17. **Add application management interface**
18. **Add active work tracking**

### Phase 5: Brand Workspace (User Visible)
19. **Implement BRAND & MARKETING workspace pages**
20. **Add brand identity editor**
21. **Add content generation interface**
22. **Add campaign management interface**

### Phase 6: Cleanup (No User Impact)
23. **Remove old phase-based navigation**
24. **Remove hardcoded goal selection**
25. **Remove manual user type selection**
26. **Update documentation**
27. **Run architecture tests**

---

## Risk Mitigation

### Low Risk
- **API endpoint updates**: Backend contracts already defined
- **New module creation**: No impact on existing code
- **Design system changes**: None planned, keeping existing design

### Medium Risk
- **Navigation refactor**: Users accustomed to phase-based navigation
  - **Mitigation**: Keep old pages accessible during transition, add migration guide
- **Workspace model introduction**: New concept for users
  - **Mitigation**: Clear onboarding, workspace activation guidance

### High Risk
- **None identified**

---

## Testing Strategy

### Architecture Tests
- Run `test_frontend_architecture.py` after each phase
- Ensure no intelligence leakage
- Verify API contract compliance

### Integration Tests
- Test authentication flow with new endpoints
- Test workspace activation/deactivation
- Test profile CRUD operations
- Test freelancing workspace flows
- Test brand workspace flows

### Regression Tests
- Ensure existing dashboard still works
- Ensure live console still connects
- Ensure existing products still accessible
- Ensure no broken links

### User Acceptance Tests
- Test new navigation flow
- Test workspace switching
- Test profile editing
- Test freelancing workspace end-to-end
- Test brand workspace end-to-end

---

## Rollback Plan

### If Phase 1 Fails
- Revert API endpoint changes
- Revert authentication changes
- Delete new modules
- Continue with existing frontend

### If Phase 2 Fails
- Revert sidebar changes
- Revert home page changes
- Revert router changes
- Keep new modules for later use

### If Phase 3-5 Fail
- Keep existing pages as fallback
- Add "Old View" link in sidebar
- Gradual migration instead of big bang

---

## Success Criteria

### Technical
- [ ] All architecture tests pass
- [ ] No intelligence leakage
- [ ] All API contracts implemented
- [ ] No broken links
- [ ] Dashboard and live console still work

### Functional
- [ ] User can authenticate
- [ ] User can edit profile
- [ ] User can activate workspaces
- [ ] User can switch workspaces
- [ ] Freelancing workspace functional
- [ ] Brand workspace functional

### User Experience
- [ ] Navigation is intuitive
- [ ] Workspace model is clear
- [ ] Profile editing is easy
- [ ] No performance degradation

---

## Timeline Estimate

### Phase 1: Foundation
- **Effort**: 2-3 days
- **Risk**: Low
- **User Impact**: None

### Phase 2: Navigation Refactor
- **Effort**: 1-2 days
- **Risk**: Medium
- **User Impact**: High

### Phase 3: Profile Implementation
- **Effort**: 2-3 days
- **Risk**: Medium
- **User Impact**: High

### Phase 4: Freelancing Workspace
- **Effort**: 3-4 days
- **Risk**: Medium
- **User Impact**: High

### Phase 5: Brand Workspace
- **Effort**: 2-3 days
- **Risk**: Medium
- **User Impact**: High

### Phase 6: Cleanup
- **Effort**: 1 day
- **Risk**: Low
- **User Impact**: None

**Total Estimated Effort**: 11-16 days

---

## Dependencies

### Backend Dependencies
- USER Contract API endpoints must be implemented
- ENIGMA PROFILE Contract API endpoints must be implemented
- WORKSPACE Contract API endpoints must be implemented
- FREELANCING Contract API endpoints must be implemented
- BRAND & MARKETING Contract API endpoints must be implemented

### Frontend Dependencies
- Phase 1 must complete before Phase 2
- Phase 2 must complete before Phase 3
- Phase 3 must complete before Phase 4
- Phase 4 must complete before Phase 5

---

## Recommendation for TASK-037

### Next Step: Enigma Frontend Shell

**Recommendation**: Start with Phase 1 (Foundation) of this migration plan.

**Specific Actions for TASK-037**:
1. Update API endpoints in `js/api.js` to match USER Contract
2. Update authentication in `js/auth.js` to use USER Contract endpoints
3. Create `js/profile.js` module with ENIGMA PROFILE functions
4. Create `js/workspaces.js` module with WORKSPACE functions
5. Create basic page templates for profile and workspaces
6. Update router to include new routes
7. Test authentication flow with new endpoints

**Do NOT**:
- Modify existing page structure yet
- Change navigation yet
- Remove any existing functionality
- Implement workspace switching UI yet

**Focus**: Foundation only - prepare the infrastructure for the larger migration.

---

## Conclusion

The existing frontend is **already a proper Control Plane** with no intelligence leakage. The migration is primarily a **reorganization** from a linear product journey model to a workspace-based model, not an architectural fix.

The migration plan prioritizes:
1. **Safety**: No deletions, gradual rollout, rollback options
2. **Reuse**: Keep all solid existing components
3. **User Experience**: Clear workspace model, intuitive navigation
4. **Contract Compliance**: All UI backed by API contracts

The estimated effort is **11-16 days** with **low to medium risk** when executed in phases.
