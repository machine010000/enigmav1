# ENIGMA Frontend Inventory

**Date**: 2026-08-07  
**Purpose**: Audit existing frontend before migration to new Control Plane architecture

---

## 1. Frontend Structure

### Directory Layout
```
enigma-frontend/
├── components/
│   ├── add-product-modal.html
│   ├── mobile-header.html
│   └── sidebar.html
├── css/
│   └── style.css
├── js/
│   ├── api.js
│   ├── auth.js
│   ├── chat.js
│   ├── config.js
│   ├── dashboard.js
│   ├── goals.js
│   ├── live-console.js
│   ├── main.js
│   ├── onboarding.js
│   ├── products.js
│   ├── router.js
│   └── userbrain.js
├── pages/
│   ├── analytics.html
│   ├── brain.html
│   ├── dashboard.html
│   ├── decisions.html
│   ├── execution.html
│   ├── home.html
│   ├── learning.html
│   ├── live-console.html
│   ├── login.html
│   ├── products.html
│   ├── register.html
│   ├── research.html
│   ├── strategy.html
│   ├── user-brain.html
│   └── workspace.html
└── index.html
```

---

## 2. Pages / Routes

### Auth Pages
| Route | File | Purpose | Status Mapping |
|-------|------|---------|----------------|
| `/login` | `pages/login.html` | User authentication | KEEP → USER Contract |
| `/register` | `pages/register.html` | User registration | KEEP → USER Contract |

### Main App Pages
| Route | File | Purpose | Current Model | Target Contract |
|-------|------|---------|---------------|-----------------|
| `/home` | `pages/home.html` | Goal selection landing | Product Journey | REFACTOR → Workspace Landing |
| `/workspace` | `pages/workspace.html` | Activity overview | Product Journey | REFACTOR → WORKSPACE Contract |
| `/brain` | `pages/brain.html` | Master Brain chat | Master Brain Chat | REFACTOR → ENIGMA PROFILE |
| `/user-brain` | `pages/user-brain.html` | User type detection | User Brain | MOVE → ENIGMA PROFILE |
| `/products` | `pages/products.html` | Product management | Product Journey | MOVE → FREELANCING Workspace |
| `/research` | `pages/research.html` | Research phase | Product Journey | MOVE → FREELANCING Workspace |
| `/decisions` | `pages/decisions.html` | Decisions phase | Product Journey | MOVE → FREELANCING Workspace |
| `/strategy` | `pages/strategy.html` | Strategy phase | Product Journey | MOVE → FREELANCING Workspace |
| `/execution` | `pages/execution.html` | Execution phase | Product Journey | MOVE → FREELANCING Workspace |
| `/analytics` | `pages/analytics.html` | Results analysis | Product Journey | MOVE → FREELANCING Workspace |
| `/learning` | `pages/learning.html` | Learning/reflection | Product Journey | MOVE → FREELANCING Workspace |
| `/dashboard` | `pages/dashboard.html` | Developer monitoring | Engine Monitoring | KEEP → Control Plane |
| `/live-console` | `pages/live-console.html` | Real-time events | Engine Monitoring | KEEP → Control Plane |

---

## 3. Components

### Layout Components
| Component | File | Purpose | Classification |
|-----------|------|---------|----------------|
| Sidebar | `components/sidebar.html` | Main navigation | REFACTOR → Workspace selector |
| Mobile Header | `components/mobile-header.html` | Mobile navigation | REFACTOR → Workspace selector |
| Add Product Modal | `components/add-product-modal.html` | Product creation | MOVE → FREELANCING Workspace |

### Reusable UI Elements (in CSS)
- `.glass-card` - Glass morphism card style
- `.btn-primary` / `.btn-secondary` - Button styles
- `.tag` - Status tags (green, purple, blue, yellow, red)
- `.input-field` - Form input style
- `.progress-bar` - Progress indicator
- `.metric-card` - Metric display card
- `.goal-card` - Goal selection card
- `.task-item` - Task list item
- `.chat-message` - Chat message bubble

**Classification**: KEEP - All reusable UI styles are architecture-agnostic

---

## 4. Data / API Layer

### API Client (`js/api.js`)
- **Function**: Centralized HTTP client with authentication
- **Features**:
  - Bearer token authentication
  - Automatic 401 handling (logout)
  - Loading states
  - Toast notifications
  - JSON request/response handling
- **Endpoints Used**:
  - `/auth/me` - Get current user
  - `/auth/login` - Login
  - `/auth/register` - Register
  - `/products` - Product CRUD
  - `/dashboard` - Engine monitoring data
  - WebSocket `/ws/events` - Live worker events

**Classification**: KEEP - Solid API layer, needs endpoint mapping to new contracts

### Authentication (`js/auth.js`)
- **Function**: User authentication and session management
- **Features**:
  - Token storage in localStorage
  - Login/register form handling
  - User profile loading
  - Logout functionality
  - Skip auth for development mode
- **State**: `currentUser` object

**Classification**: KEEP - Compatible with USER Contract, needs endpoint mapping

### Router (`js/router.js`)
- **Function**: Page routing and fragment loading
- **Features**:
  - ES module-based page loading
  - Sidebar navigation
  - Mobile header injection
  - Page visibility management
- **Routes**: 13 app pages + 2 auth pages

**Classification**: KEEP - Good architecture, needs route reorganization for workspaces

### Dashboard (`js/dashboard.js`)
- **Function**: Engine monitoring dashboard
- **Features**:
  - Worker execution tracking
  - Summary metrics (running, completed, failed, LLM calls, confidence)
  - Registered workers display
  - Recent executions with filtering
  - Event logs
  - Decision history
- **Data Displayed**: Worker status, execution time, confidence, memory usage, errors

**Classification**: KEEP - Developer tool, belongs in Control Plane

### Products (`js/products.js`)
- **Function**: Product management
- **Features**:
  - Product listing
  - Product creation
  - Product selection
  - Status tracking (onboarding, researching, strategizing, active)
  - Progress visualization
- **Endpoints**: `/products` (GET, POST)

**Classification**: MOVE - Belongs in FREELANCING Workspace

### Live Console (`js/live-console.js`)
- **Function**: Real-time worker event streaming
- **Features**:
  - WebSocket connection to `/ws/events`
  - Auto-reconnection
  - Event rendering with icons and colors
  - Message limiting (last 500)
  - Connection status display
- **Event Types**: started, finished, error, progress, worker_registered, execution_started, verification_started, research_started, audience_started, keyword_started

**Classification**: KEEP - Critical for observability, belongs in Control Plane

### User Brain (`js/userbrain.js`)
- **Function**: User type detection and journey tracking
- **Features**:
  - User type selection (seller, service provider, content creator, investor)
  - Journey visualization (user, product, production)
  - User type badge display

**Classification**: MOVE - Belongs in ENIGMA PROFILE

### Chat (`js/chat.js`)
- **Function**: Master Brain chat interface
- **Features**: Message sending/receiving

**Classification**: REFACTOR - Needs to use API contracts for brain communication

### Onboarding (`js/onboarding.js`)
- **Function**: Product onboarding flow
- **Features**: Onboarding question management

**Classification**: MOVE - Belongs in FREELANCING Workspace

---

## 5. Existing Business Features

### Product Journey Model (Current)
The current frontend follows a linear product journey:

```
Goal Selection → Product Creation → Research → Decisions → Strategy → Execution → Analytics → Learning
```

**Features per Phase**:
- **Goal Selection**: 6 predefined goals (first sale, increase sales, launch product, build brand, content creation, custom)
- **Product Creation**: Name, category, subcategory, market, description
- **Research**: Data collection from Google, Reddit, TikTok
- **Decisions**: Evidence-based decision tracking with confidence scores
- **Strategy**: Positioning, messaging, content strategy, growth strategy
- **Execution**: Daily task scheduling with time slots
- **Analytics**: Views, engagement, clicks, sales, revenue tracking
- **Learning**: What's working, what to improve, key insights

### Engine Monitoring Features
- Worker registration and listing
- Real-time execution tracking
- Event streaming
- Decision history
- Performance metrics (confidence, LLM calls, memory usage)

### User Management Features
- Authentication (login/register)
- User profile display
- User type classification
- Journey tracking

---

## 6. Technology Stack

### Frontend
- **Language**: Vanilla JavaScript (ES6 modules)
- **Styling**: Tailwind CSS (CDN)
- **Icons**: Font Awesome 6.4.0
- **Fonts**: Cairo (Google Fonts)
- **Architecture**: Single-page application with fragment loading

### Backend Integration
- **API**: RESTful endpoints
- **Authentication**: Bearer token (JWT)
- **Real-time**: WebSocket (`/ws/events`)
- **Base URL**: Configurable via `window.ENIGMA_API_BASE`

---

## 7. State Management

### Current State Storage
- **Authentication**: `localStorage.getItem('enigma_token')`
- **User**: `currentUser` variable in auth.js
- **Product**: `currentProduct` variable in products.js
- **Dashboard**: `currentDashboardTab` variable in dashboard.js

### State Flow
```
User Input → API Call → Backend Response → UI Update
```

**No complex state management library** - simple variable-based state

---

## 8. Design System

### Colors
- **Primary**: Brand purple (#8b5cf6), Brand blue (#3b82f6), Brand cyan (#06b6d4)
- **Dark Theme**: Dark 900 (#050507), Dark 800 (#0a0e1a), Dark 700 (#111827)
- **Status**: Green (#10b981), Yellow (#fbbf24), Red (#f87171)

### Typography
- **Font**: Cairo (Arabic-friendly)
- **Direction**: RTL (Arabic language)
- **Sizes**: Base text, headings up to 5xl

### Components
- Glass morphism effects
- Gradient backgrounds
- Rounded corners (10px-16px)
- Smooth transitions (0.3s)
- Responsive grid layouts

---

## 9. Intelligence Leakage Audit

### Checked For
- ❌ Reasoning logic in frontend
- ❌ Knowledge scoring in frontend
- ❌ Conflict resolution in frontend
- ❌ Decision making algorithms in frontend
- ❌ Direct database access
- ❌ Backend cognitive core imports

### Result
**NO INTELLIGENCE LEAKAGE DETECTED**

The frontend correctly:
- Displays data from backend APIs
- Renders backend-computed metrics
- Shows backend-generated decisions
- Streams backend events via WebSocket
- Does not implement any cognitive logic

**Conclusion**: Frontend is already a proper Control Plane from an intelligence perspective

---

## 10. Authentication Flow

### Current Implementation
1. User enters credentials on `/login`
2. Frontend calls `POST /auth/login`
3. Backend returns `access_token`
4. Frontend stores token in `localStorage`
5. Frontend calls `GET /auth/me` to load user profile
6. Frontend shows main app with user data

### Protected Routes
- All main app pages require authentication
- 401 responses trigger automatic logout
- Development mode allows "skip auth"

### User Identity
- Stored in `currentUser` variable
- Displayed in sidebar
- Used for API authentication

**Classification**: KEEP - Solid implementation, needs endpoint mapping to USER Contract

---

## 11. Current Dashboard Analysis

### Dashboard Purpose
**Developer-focused**: Engine monitoring and worker execution tracking

### Dashboard Features
- Summary metrics (running, completed, failed, total executions, LLM calls, avg confidence)
- Registered workers list with input/output schemas
- Tabbed view: Running, Completed, Failed, Logs, Decisions
- Real-time execution cards with status, time, confidence, LLM calls, memory
- Event log with timestamps and worker names
- Decision history with reasoning and outcomes

### Dashboard vs New Architecture
**Current**: Developer tool for engine monitoring  
**Target**: Control Plane for workspace management

**Conclusion**: Dashboard should be KEPT as a developer tool, but separated from the main user-facing Control Plane

---

## 12. Legacy Architecture Risks

### Identified Risks

| Risk | Location | Why Legacy | Referenced? | Action |
|------|----------|------------|-------------|--------|
| Product Journey Model | All pages | Linear product model doesn't match workspace architecture | Yes (router.js) | REFACTOR to workspace model |
| Hardcoded Goals | home.html | 6 predefined goals limit flexibility | Yes | REPLACE with dynamic workspace selection |
| User Type Detection | user-brain.html | Manual selection vs automatic detection | Yes | REFACTOR to ENIGMA PROFILE |
| Phase-based Navigation | sidebar.html | Research → Decisions → Strategy → Execution | Yes | REFACTOR to workspace-based navigation |
| Mixed Concerns | Multiple pages | Product management mixed with engine monitoring | Yes | SEPARATE into workspaces |

### No Critical Risks
- No security vulnerabilities detected
- No performance issues identified
- No broken dependencies
- No deprecated APIs used

---

## 13. Reusable Components Summary

### KEEP (Architecture-Agnostic)
- **API Layer**: `api.js` - Solid HTTP client
- **Authentication**: `auth.js` - Token-based auth working well
- **Router**: `router.js` - ES module loading is good architecture
- **Dashboard**: `dashboard.js` - Valuable developer tool
- **Live Console**: `live-console.js` - Critical for observability
- **UI Components**: All CSS classes and HTML components
- **Design System**: Colors, typography, glass morphism effects

### REFACTOR (Needs Structural Changes)
- **Sidebar**: Convert from phase-based to workspace-based navigation
- **Home Page**: Convert from goal selection to workspace landing
- **Workspace Page**: Convert from activity overview to workspace selector
- **Brain Chat**: Convert to use API contracts
- **User Brain**: Convert to ENIGMA PROFILE contract

### MOVE (Belongs in Different Location)
- **Products**: Move to FREELANCING workspace
- **Research**: Move to FREELANCING workspace
- **Decisions**: Move to FREELANCING workspace
- **Strategy**: Move to FREELANCING workspace
- **Execution**: Move to FREELANCING workspace
- **Analytics**: Move to FREELANCING workspace
- **Learning**: Move to FREELANCING workspace
- **Add Product Modal**: Move to FREELANCING workspace

### REPLACE (Conflicts with Target Architecture)
- **Goal Selection**: Replace with workspace selection
- **Phase Navigation**: Replace with workspace navigation
- **User Type Selection**: Replace with ENIGMA PROFILE detection

### DELETE (None Identified)
No components identified as truly obsolete or unused. All current pages serve a purpose in the existing product journey model.

---

## 14. Missing Components (Required for New Architecture)

### ENIGMA PROFILE
- Profile editing interface
- Capability selection interface
- Evidence vault display
- Readiness score visualization
- Profession focus selection

### FREELANCING Workspace
- Platform connection interface
- Job discovery interface
- Readiness assessment display
- Application management interface
- Active work tracking
- Revenue/events display

### BRAND & MARKETING Workspace
- Brand identity editor
- Content generation interface
- Campaign management interface
- Channel connection interface
- Lead tracking interface

### Workspace Selector
- Workspace activation/deactivation
- Workspace state management
- Workspace switching interface

---

## 15. Files Changed in This Audit

**NONE** - This is a read-only audit. No files were modified.

---

## 16. Tests Run

**Architecture Tests**: `enigma-backend/tests/test_frontend_architecture.py`
- Result: **PASSED** (4/4 tests)
- Frontend has no cognitive core imports
- Cognitive core is isolated from frontend
- State machines documented
- API contracts documented

**Backend Tests**: `test_engine.py`
- Result: **PASSED** (9/9 tests)
- All Sprint 1 and Sprint 2 tests passing

---

## 17. Summary

### Current Frontend State
- **Architecture**: Vanilla JS SPA with fragment loading
- **Design**: Modern dark theme with glass morphism
- **Language**: Arabic (RTL)
- **Model**: Linear product journey
- **Quality**: Solid implementation, no intelligence leakage

### Migration Complexity
- **Low**: Core infrastructure (API, auth, router) is solid
- **Medium**: Navigation structure needs workspace-based reorganization
- **Low**: UI components are reusable and architecture-agnostic
- **Medium**: Business logic needs mapping to workspace contracts

### Key Insight
The existing frontend is **already a proper Control Plane** from an intelligence perspective. The main work is reorganizing the navigation and business logic from a "product journey" model to a "workspace" model, not fixing architectural violations.
