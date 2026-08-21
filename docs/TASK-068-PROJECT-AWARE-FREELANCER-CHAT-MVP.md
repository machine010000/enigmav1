# TASK-068 — Project-Aware Multi-Project Freelancer Chat MVP

## Result

TASK-068 is implemented locally on `integration/task-067i-manual-ai-baseline`, based on exact commit `59f1acbebb1c9b742ace5f84d89fb6a355fcd662`. The implementation is uncommitted, was not pushed, and made no real marketplace, client-messaging, production-database, or external AI/provider calls during validation.

The MVP provides persistent project-aware conversations, manual opportunity copy/paste intake, deterministic intent routing, safe natural-language project resolution, proposal versioning, client-message history, project execution notes, durable Academy links/snapshots, Creativity artifacts, Product Verification decisions, reusable samples, and a minimal Frontend V2 chat surface. It does not submit proposals, send messages, or silently change lifecycle state.

## Architecture reused

- `MarketplaceJob` remains the single opportunity/project registry. No competing project model was introduced.
- `ManualOpportunityService` remains authoritative for manual opportunity creation, canonical dedupe, lifecycle outcomes, and submission safeguards.
- The existing shared `app.ai.gateway` is the only AI gateway used.
- `MasterBrain.decide_capability()` supplies Brain capability decisions where applicable.
- TASK-067 `AcademyLearningService`, `CreativityAIService`, and `ProductVerificationGate` are reused directly.
- Academy continues to submit candidates through Knowledge Governance. Because the current governance store is process-local, Chat additionally persists the governed knowledge ID and complete learning snapshot in the existing application database as a project artifact. This is a durable link/snapshot, not an alternate knowledge-governance system.
- Existing TASK-066 approval, package, Submission Intent, immutable source, transaction, lifecycle, and dedupe code was not replaced.
- Frontend V2 was extended minimally. The legacy frontend was untouched.

## New persistence and migration

Alembic revision `014_project_aware_freelancer_chat` is linear from `013_runtime_url_canonical_dedupe` and is the new head.

New tables:

1. `freelancer_conversations`
   - user/profile ownership
   - active project pointer
   - persistent metadata and timestamps
2. `freelancer_chat_messages`
   - immutable user/assistant content
   - conversation, user, and optional project association
   - resolved intent and structured result
   - durable per-conversation sequence with a database uniqueness constraint
3. `freelancer_project_artifacts`
   - typed/versioned project output
   - private-project or explicitly reusable-global visibility
   - content, structured metadata, source-message link, and timestamps

Artifact types currently used include opportunity analysis, proposal draft, Creativity output, client message, client reply draft, requirement, execution note, Academy learning, outcome, and sample. Foreign keys protect conversation/message ownership of dependent records. Project associations use the established `MarketplaceJob.job_id`; application queries always combine `profile_id="enigma_profile"` with authenticated `user_id` ownership.

Migration validation:

- isolated upgrade: passed
- isolated downgrade: passed
- isolated re-upgrade: passed
- `alembic heads`: one head, `014_project_aware_freelancer_chat`
- offline `013 -> 014`, `014 -> 013`, and re-upgrade SQL generation: passed
- full offline `base -> head` remains unsupported by pre-existing migration `001_initial_schema`, which calls SQLAlchemy inspection against Alembic's mock connection. This is unrelated to revision 014 and is documented as a nonblocking baseline limitation.

## API endpoints

All new endpoints require `require_admin_user` and derive audit ownership from `current_user.id`:

- `POST /api/freelancing/chat`
- `GET /api/freelancing/chat/conversations/{conversation_id}`
- `GET /api/freelancing/chat/projects`
- `POST /api/freelancing/chat/samples`
- `GET /api/freelancing/chat/samples`

The POST boundary owns exactly one commit. Any failure rolls back. The service itself only flushes and never commits. Opportunity payloads have Pydantic length, language, currency, budget, and type validation. All supplied marketplace/client/sample text is explicitly treated as untrusted data in AI system instructions.

Responses expose the conversation/message/project IDs, resolved intent, structured project-resolution result, generated result data, invoked capabilities, and next action where available. AI text remains separate from authoritative database/lifecycle fields.

## Intent routing

The deterministic router recognizes English and Arabic signals for:

- `new_opportunity`
- `opportunity_analysis`
- `proposal_request`
- `client_message`
- `client_reply_request`
- `project_requirement`
- `project_work`
- `project_switch`
- `record_win`
- `record_loss`
- `add_sample`
- `learning_request`
- `general_freelancer_chat`

Long pasted job descriptions are detected even when the current conversation already has an active project. AI output never selects authoritative lifecycle transitions.

## Project resolution

Resolution is limited to manual `MarketplaceJob` rows owned by the authenticated user and profile. It applies, in order:

1. explicit owned `project_id`;
2. normalized title, platform project ID, platform, and public client metadata matches;
3. token-overlap scoring;
4. active conversation project fallback.

Candidates within 0.08 of the top plausible score produce an ambiguity response. The service asks the user to choose and does not guess. A missing required project produces a structured `project_required` response. Multiple conversations and multiple active projects are independently durable.

## Opportunity flow

- Uses `ManualOpportunityService.create()`.
- Preserves pasted marketplace content in `MarketplaceJob.original_text`.
- Stores normalized/derived requirements separately.
- Uses the shared AI gateway for structured analysis.
- Retrieves up to five owned, project-private or explicitly global examples ranked by token relevance.
- Records the Brain decision when a capability is selected.
- Produces Product Verification confidence, risks, missing information, evidence context, recommendation, and proposal readiness.
- A duplicate links to the existing owned opportunity without overwriting immutable source content. The conversation is safely rehydrated if the established concurrent-dedupe rollback path rolls back a newly created conversation.

## Proposal, client, and execution flows

- Proposals use immutable source, normalized project context, relevant samples, existing private Academy learning, Creativity proposal angles, the shared AI gateway, and Product Verification.
- Proposal drafts are immutable, project-scoped, and monotonically versioned.
- Every proposal is marked `manual_copy_only`; no submission API is called.
- Original client messages are stored as immutable project artifacts.
- Client replies are drafts marked `manual_send_only`.
- Requirements and execution plans become typed project artifacts.
- Product Verification is used for opportunity/proposal readiness and execution/final-delivery planning; it does not auto-deliver.
- Win/loss requests call the existing manual lifecycle service. Without the required valid lifecycle and manual submission snapshot they return a blocked result. Chat contains no submission path.

## Academy, Creativity, and Product Verification

- Academy: explicit learning requests are routed through Brain capability selection and `AcademyLearningService.learn(store=True)`. The governance knowledge ID and material are durably linked to the correct project; private artifacts are not returned to another project.
- Creativity: invoked for proposal strategy, not for every message. Structured ideas/angles/risks are stored as project artifacts and referenced by the proposal version.
- Product Verification: structured gate results determine proposal readiness and accompany execution review output. The result includes confidence, risks, missing information, evidence context, and pass/review/fail recommendation.

No new AI client, provider, memory database, or alternate orchestrator was introduced.

## Samples and retrieval

Samples store type, project association, content, outcome/skills/other supplied metadata, visibility, and version. Private samples remain project-local. Only samples explicitly marked `reusable_global` can be retrieved for another project owned by the same user. Other users' global samples are never returned. Retrieval ranks accessible samples against project title, skills, and request tokens; it is context retrieval, not fine-tuning.

## Frontend V2

The existing Freelancer control center now includes a compact Chat panel with:

- natural-language/paste input;
- persistent conversation restoration;
- server-loaded message history;
- visible optional current-project selector;
- automatic project resolution when no selector is used;
- assistant/user messages and structured-result details;
- explicit “manual actions only” and no-live-send language.

React renders all user/AI text as text; no raw HTML injection path was added. The backend is authoritative for project and conversation state. Browser storage contains only the conversation ID pointer, never project memory or credentials.

## Isolation and safety

- All project reads require `profile_id="enigma_profile"`, `created_by_user_id=user_id`, and manual-ingestion scope.
- Conversations, messages, artifacts, and samples are filtered by authenticated `user_id`.
- Project A client messages, proposals, and private Academy artifacts do not appear in Project B context.
- Cross-user explicit project IDs are rejected.
- Ambiguous references do not select a project.
- The service has no `commit()`, external HTTP client, `record_submission()`, marketplace submit, or client-send call.
- The HTTP router commits once or rolls back once.
- Original marketplace text is never updated by Chat.
- Win/loss cannot bypass the TASK-066 state machine or manual submission snapshot.

## Files changed

- `enigma-backend/alembic/versions/014_project_aware_freelancer_chat.py`
- `enigma-backend/app/freelancing/project_chat.py`
- `enigma-backend/app/main.py`
- `enigma-backend/app/models/__init__.py`
- `enigma-backend/app/models/freelancer_chat.py`
- `enigma-backend/app/routers/freelancer_chat.py`
- `enigma-backend/tests/test_068_project_aware_freelancer_chat.py`
- `enigma-frontend-v2/app/components/freelancer-chat.tsx`
- `enigma-frontend-v2/app/components/freelancing-control-center.tsx`
- `enigma-frontend-v2/app/globals.css`
- `docs/TASK-068-PROJECT-AWARE-FREELANCER-CHAT-MVP.md`

No legacy-frontend, TASK-063, existing lifecycle, package-approval, Submission Intent, or marketplace-integration file was modified.

## Validation results

No real external service was contacted. Tests use injected fake AI/Academy/Creativity implementations and isolated in-memory SQLite.

| Validation | Result |
|---|---:|
| TASK-068 focused suite | 32 passed |
| TASK-066 focused suite | 53 passed |
| TASK-067 focused suite | 4 passed |
| Combined TASK-066/067/068 + Freelancer durable/security + relevant Brain tests | 191 passed |
| Pipeline orchestrator suite included in a broader run | 194 passed, 5 failed |
| Obsolete Submission Intent boundary test collection | 1 collection error |
| Migration 014 isolated upgrade/downgrade/upgrade | passed (included in TASK-068 suite) |
| Python compilation/import | 6 changed Python files compiled; 5 routes imported |
| Frontend V2 TypeScript | passed |
| Frontend V2 production build | passed with Next.js Webpack |
| `git diff --check` | passed; only existing Windows LF/CRLF notices |

The five pipeline failures are pre-existing sync/async incompatibilities: synchronous `PipelineOrchestrator._update_enigma_profile()` calls async `EnigmaProfileManager.update_profile()` without awaiting it. TASK-068 neither calls nor modifies that path. The obsolete Submission Intent test imports missing `app.auth.dependencies`; the active authentication dependency lives in `app.routers.auth`. Neither known issue was fixed in this task.

The default Turbopack build rejected the temporary local dependency junction because it pointed outside the worktree filesystem root. Re-running the same production build with Next.js' supported Webpack mode passed. The temporary `.next` output and dependency junction were removed after validation.

## Known limitations

- Intent and project resolution are deterministic heuristics, not semantic embeddings. Low-confidence/ambiguous references require user clarification.
- Retrieval is token-ranked and capped at five examples; there is no vector index.
- Knowledge Governance itself remains process-local in the inherited TASK-067 implementation. Freelancer Chat closes the durability requirement for generated learning by storing the governed ID and complete immutable learning snapshot in the project-artifact table. Making the governance registry globally database-backed remains a separate architecture task.
- The UI restores the last conversation known to the browser. A conversation-list/search UI is not included in this minimum MVP, although conversation state is durable and retrievable by ID.
- The MVP is Admin-only, matching TASK-066 manual-intake authorization.
- AI/provider availability and output quality still depend on deployed gateway configuration. Tests intentionally used no real provider.
- Concurrent message/version inserts are protected by unique sequence/version indexes and return a conflict at the HTTP boundary; automatic retry is future work.
- The five unrelated legacy pipeline tests and obsolete Submission Intent test remain as described above.

## Exact remaining work before marketplace API integration

1. Independently validate this uncommitted TASK-068 diff from a clean worktree/commit once commit authorization is provided.
2. Decide and document which marketplace operations are officially supported and permitted; keep unsupported platforms manual-only.
3. Add server-side provider credentials/OAuth handling without exposing tokens to Frontend V2.
4. Add a read-only discovery adapter first, with official-contract fixtures, rate-limit handling, idempotency, and zero-write smoke validation.
5. Map remote opportunities into the existing `MarketplaceJob`/canonical-dedupe contract; do not create a second project registry.
6. Preserve explicit human approval, approved package ownership, and active Submission Intent before any supported external submission.
7. Add provider-specific submission audit snapshots, idempotency keys, reconciliation/webhook polling, and failure recovery without changing Chat's authoritative lifecycle boundary.
8. Add end-to-end sandbox tests and an operational kill switch before enabling any live marketplace action.

Subject to independent validation, this local implementation is ready to serve as the TASK-068 MVP baseline. It is not authorization to enable live marketplace APIs or external messaging.
