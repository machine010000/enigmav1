# Enigma - AI-Powered Freelancing Platform

Enigma is an intelligent freelancing platform that uses AI to discover jobs, understand requirements, generate proposals, and manage applications across multiple marketplaces (starting with Upwork).

## Architecture

### Backend (FastAPI + Python)
- **Framework:** FastAPI with async/await
- **Database:** PostgreSQL (Neon) with SQLAlchemy async
- **AI:** NVIDIA NIM API (Llama 3.3 70B)
- **Cache:** Redis
- **Marketplace:** Upwork (with OAuth 2.0)

### Frontend (Vanilla JS + Tailwind CSS)
- **Framework:** Vanilla ES6 modules
- **Styling:** Tailwind CSS
- **Architecture:** Modular, no build step required

## Project Structure

```
enigma/
├── enigma-backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, logging, database
│   │   ├── marketplace/    # Marketplace adapters (Upwork)
│   │   ├── work_market/    # Work market logic
│   │   └── llm/            # LLM integration
│   ├── tests/              # Test suite
│   └── requirements.txt    # Python dependencies
├── enigma-frontend/         # Frontend
│   ├── js/                 # JavaScript modules
│   ├── css/                # Styles
│   └── index.html          # Entry point
└── docs/                   # Documentation
```

## Key Features

### Safety Mechanisms
- **Human Approval Gate:** All applications require explicit human approval before submission
- **Cost Protection:** Connects/cost checking before any application submission
- **Knowledge Governance:** No fabricated claims, evidence provenance tracking
- **Duplicate Prevention:** Prevents duplicate submissions

### Pipeline
1. **Job Discovery:** Discover jobs from Upwork
2. **Job Intake:** Normalize and classify jobs
3. **Research:** Knowledge gap analysis and evidence gathering
4. **Readiness:** Determine if job is ready for application
5. **Proposal Generation:** Generate proposal with evidence
6. **Human Approval:** Mandatory human review and approval
7. **Submission:** Submit to marketplace
8. **Tracking:** Track application status

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js (for frontend development)
- PostgreSQL database
- Redis server

### Backend Setup

```bash
cd enigma-backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Edit .env with your settings
```

### Frontend Setup

```bash
cd enigma-frontend

# No build step required - just serve static files
python -m http.server 8080
```

### Running the Backend

```bash
cd enigma-backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
cd enigma-backend
pytest tests/ -v
```

## Production Deployment

This project is configured for deployment on Vercel with both frontend and backend services.

### Vercel Setup

1. Push this repository to GitHub
2. Connect the repository to Vercel
3. Configure environment variables in Vercel dashboard
4. Deploy

### Required Environment Variables

```bash
DATABASE_URL=postgresql://...
NVIDIA_API_KEY=nvapi-...
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
AI_MODEL=meta/llama-3.3-70b-instruct
AI_PROVIDER=nvidia
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://...
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://your-domain.com
UPWORK_CLIENT_ID=your-upwork-client-id
UPWORK_CLIENT_SECRET=your-upwork-client-secret
UPWORK_REDIRECT_URI=https://your-domain.com/api/upwork/oauth/callback
```

## Upwork Integration

To enable Upwork integration:

1. Apply for Upwork API credentials at https://www.upwork.com/developer/keys/apply
2. Configure the OAuth redirect URI in Upwork dashboard
3. Set `UPWORK_CLIENT_ID` and `UPWORK_CLIENT_SECRET` environment variables
4. Complete the OAuth flow through the application

See `docs/production/UPWORK_SETUP.md` for detailed instructions.

## Documentation

- [Deployment Guide](docs/production/DEPLOYMENT.md)
- [Environment Configuration](docs/production/ENVIRONMENT.md)
- [Security Guide](docs/production/SECURITY.md)
- [Upwork Setup](docs/production/UPWORK_SETUP.md)
- [Smoke Tests](docs/production/SMOKE_TEST.md)
- [Rollback Procedures](docs/production/ROLLBACK.md)

## License

Proprietary - All rights reserved
