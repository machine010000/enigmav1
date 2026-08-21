# TASK-070 — Frontend V2 Vercel Production Readiness

## Decision

**READY_FOR_COMMIT**

Baseline: `20dab50ee5fef0a8db7fe60c95bc9c6327796e7b` on `integration/task-067i-manual-ai-baseline`.

This task changes deployment configuration and one narrow error-resilience boundary. It does not deploy, modify backend behavior, add migrations, redesign Frontend V2, remove language support, or alter marketplace submission behavior.

## Root cause and deployment isolation

The repository contained two independently deployable frontends:

- `enigma-frontend-v2`: the intended Next.js application containing TASK-069.
- `enigma-frontend`: the legacy static application containing “User Brain - Orchestrator”.

The repository-root `vercel.json` explicitly built the old Python Vercel backend and routed every non-API request to `enigma-frontend`. Separately, `enigma-frontend/vercel.json` rewrites every request to its legacy `index.html`. A Vercel project using the repository root could therefore appear to accept `/app/freelancing` while actually serving the legacy single-page application.

The minimum isolation applied is:

1. The repository-root `vercel.json` is now neutral and contains no legacy build, route, backend secret mapping, or frontend destination. A mistakenly root-scoped Vercel project can no longer silently route to the legacy UI.
2. `enigma-frontend-v2/vercel.json` is the app-local Vercel contract and explicitly declares Next.js with `npm run build`.
3. `enigma-frontend/vercel.json` remains untouched. It cannot affect the intended project when Vercel Root Directory is `enigma-frontend-v2`, because Vercel treats that directory as the application root and the app cannot access parent files.

This follows Vercel’s documented monorepo model: configure the application directory as Root Directory and keep `vercel.json` at that application root.

## Verified V2 source and routing

- `/` renders the V2 `LandingPage`, `PublicHeader`, existing locale selector, and `LandingContent`.
- `/app/freelancing` renders `FreelancingPage → FreelancingShell → FreelancingControlCenter → FreelancerChat`.
- `/app` also renders `FreelancingShell` beneath the application introduction.
- The application locale provider and English/Arabic/Spanish/French selector are unchanged.
- No V2 TASK-069 file imports from or depends on `enigma-frontend`.
- The successful production build emitted `/`, `/app`, and `/app/freelancing` as distinct Next.js routes.

## Graceful degradation

Previously, the initial `Promise.all` treated the optional Freelancer.com connection-status request as core data. A failure of only `/api/freelancing/freelancer/connection/status` caused the entire Control Center to return its blocking error screen before `FreelancerChat` could render.

The connection-status request now settles independently:

- core overview, jobs, ENIGMA profile, and manual-opportunity failures remain blocking and visible;
- only connection-status failure produces `connection=null` plus an explicit warning;
- the status badge says `unavailable`, not `not_configured`;
- live sync remains disabled without a confirmed configured connection;
- Freelancer Chat and manual intake remain visible;
- authentication behavior is unchanged; the existing request helper still clears an invalid session before returning an error.

No backend error is silently converted into success. The secondary integration failure is shown to the user.

## Vercel configuration

| Setting | Required value |
|---|---|
| Repository | `machine010000/enigmav1` |
| Branch | `integration/task-067i-manual-ai-baseline` (or the approved TASK-070 descendant) |
| Root Directory | `enigma-frontend-v2` |
| Framework Preset | Next.js |
| Build Command | `npm run build` |
| Output Directory | Next.js framework default; do not override |
| Install Command | Vercel/npm default using the committed lockfile |
| Environment | `NEXT_PUBLIC_API_BASE_URL=https://<public-backend-host>` |

`NEXT_PUBLIC_API_BASE_URL` must be the public backend origin only. Do not append `/api` or a route path. Do not place database URLs, API keys, signing keys, marketplace credentials, or any secret in `NEXT_PUBLIC_*` variables. Production has no localhost fallback; the localhost fallback in `app/lib/api.ts` is development-only.

## Backend deployment contract

Required public origin:

```text
https://<public-backend-host>
```

Verified source routes:

- `POST /auth/login`
- `POST /auth/admin-login`
- `GET /auth/me`
- `GET /api/freelancing/`
- `GET /api/freelancing/jobs`
- `GET /api/freelancing/freelancer/connection/status`
- `POST` and `GET /api/freelancing/manual`
- `POST /api/freelancing/chat`
- `GET /api/freelancing/chat/projects`
- `POST` and `GET /api/freelancing/chat/samples`
- `GET /api/enigma/profile`

The Chat router is included by `app.main`. No real marketplace call was made.

Production CORS must use the exact deployed Vercel origin:

```text
CORS_ORIGINS=https://<actual-vercel-domain>
```

Do not use `*`. Multiple authorized frontends must be listed as comma-separated exact origins. Credentialed CORS and Authorization/Content-Type support remain intact through TASK-069A. No Vercel domain is hardcoded in source.

## Database and migrations

- Alembic has one head: `014_project_aware_freelancer_chat`.
- Linear chain verified: `010 → 011 → 012 → 013 → 014`.
- TASK-070 adds no schema assumption and no migration.
- The backend deployment must run `alembic upgrade head` before application startup, as already encoded by the backend Docker start command.

## Verification checklist after deployment

1. Open `/`: it must show the V2 public landing page and the existing language selector.
2. Sign in and open `/app/freelancing`.
3. Confirm the page shows Freelancer Control Center and the “Freelancer Chat” multi-project interface.
4. Confirm the browser uses the configured `NEXT_PUBLIC_API_BASE_URL` and has no CORS error.
5. If only marketplace connection status fails, confirm Chat/manual intake remain visible with an `unavailable` warning.
6. Confirm “User Brain - Orchestrator” / “عقل المستخدم” never appears. Its appearance proves the deployment is using `enigma-frontend` or a stale deployment/alias.

## Files changed

- `vercel.json`
- `enigma-frontend-v2/vercel.json`
- `enigma-frontend-v2/app/components/freelancing-control-center.tsx`
- `enigma-frontend-v2/tests/task-070-deployment.test.mjs`
- `docs/TASK-070-V2-VERCEL-PRODUCTION-READINESS.md`

Legacy frontend files, backend files, migration files, locale files, and visual design files are unchanged.

## Test results

| Check | Result |
|---|---:|
| Existing TASK-069 Chat model/UI tests | 6 passed |
| TASK-070 deployment/routing/degradation tests | 4 passed |
| Frontend TypeScript (`tsc --noEmit`) | passed |
| Frontend production build (`next build --webpack`) | passed; 8 application routes plus `_not-found` emitted |
| TASK-068 + TASK-069A + TASK-066 backend suites | 109 passed |
| Backend read-only compilation | 302 files passed |
| Backend application + Academy + Creativity + Product Verification imports | passed |
| Alembic head | `014_project_aware_freelancer_chat` |
| `git diff --check` | passed |

No package was installed. The Frontend build used the already-installed dependency tree through a temporary verified junction, removed immediately after validation. The existing Node typeless-module and Pydantic class-based-config deprecation warnings are non-blocking and unchanged.

## Remaining operational requirement

Repository readiness cannot override a Vercel dashboard that points at the wrong Root Directory or a domain alias attached to an old deployment. The Vercel project must still be configured exactly as above and redeployed from the approved commit. Validate the unique deployment URL before promoting its alias.
