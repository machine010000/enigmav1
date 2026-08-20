"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../auth/provider";
import { useLocale } from "../i18n/provider";
import { freelancingCopy } from "../i18n/freelancing";
import { ApiError, apiRequest } from "../lib/api";

type Overview = { status: string; jobs_discovered: number };
type Job = { job_id: string; source: string; title: string; description: string; client_information?: Record<string, unknown>; budget_min?: number; budget_max?: number; currency?: string; skills?: string[]; last_seen_at?: string };
type JobDetail = { job: Job; assessment?: Record<string, unknown> | null };
type Capability = { id?: string; capability_id?: string; name: string; status?: string; readiness_status?: string };
type Assessment = { readiness: string; decision: string; missing_capabilities: string[]; reasoning_summary: string; blocking_capability?: string | null };
type Connection = { state: "not_configured" | "configured" | "connected" | "error"; configured: boolean; sandbox: boolean; last_sync_at?: string | null; last_error_code?: string | null };
type SyncSummary = { state: "success" | "partial_failure"; created: number; updated: number; existing: number; skipped: number; failed: number; discovered: number };
type Workspace = { overview: Overview | null; jobs: Job[]; capabilities: Capability[]; connection: Connection | null; error: string | null; loading: boolean };
type ManualForm = { platform: string; source_url: string; external_project_id: string; title: string; original_description: string; budget_type: string; budget_min: string; budget_max: string; currency: string; required_skills: string; client_name: string; source_language: string; customer_preferred_language: string; proposal_language: string };
type ManualOpportunity = Job & { manual_entry: true; no_live_api_connection: true; original_text: string; normalized_requirements: Record<string, unknown>; source_language: string; customer_preferred_language: string; proposal_language: string; lifecycle_status: string; submission?: { outcome_status: string } | null; assessment?: Record<string, unknown> | null };
const emptyManualForm: ManualForm = { platform: "workana", source_url: "", external_project_id: "", title: "", original_description: "", budget_type: "fixed", budget_min: "", budget_max: "", currency: "USD", required_skills: "", client_name: "", source_language: "en", customer_preferred_language: "en", proposal_language: "en" };

export function FreelancingControlCenter() {
  const { locale } = useLocale();
  const { token, logout } = useAuth();
  const copy = freelancingCopy[locale.code as keyof typeof freelancingCopy] ?? freelancingCopy.en;
  const [workspace, setWorkspace] = useState<Workspace>({ overview: null, jobs: [], capabilities: [], connection: null, error: null, loading: true });
  const [detail, setDetail] = useState<JobDetail | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [busy, setBusy] = useState<"idle" | "sync" | "assess" | "plan">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SyncSummary | null>(null);
  const [query, setQuery] = useState("");
  const [skills, setSkills] = useState("");
  const [manualForm, setManualForm] = useState<ManualForm>(emptyManualForm);
  const [manualJobs, setManualJobs] = useState<ManualOpportunity[]>([]);
  const [manualDetail, setManualDetail] = useState<ManualOpportunity | null>(null);
  const [manualError, setManualError] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [editingJobId, setEditingJobId] = useState<string | null>(null);
  const [proposalText, setProposalText] = useState("");
  const [submittedPrice, setSubmittedPrice] = useState("");
  const [outcome, setOutcome] = useState("client_replied");
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

  const loadWorkspace = useCallback(async () => {
    setWorkspace((current) => ({ ...current, loading: true, error: null }));
    try {
      const [overview, jobs, capabilities, connection, manual] = await Promise.all([
        apiRequest<Overview>("/api/freelancing/", { headers }, logout),
        apiRequest<Job[]>("/api/freelancing/jobs", { headers }, logout),
        apiRequest<{ capabilities?: Capability[] }>("/api/enigma/profile", { headers }, logout),
        apiRequest<Connection>("/api/freelancing/freelancer/connection/status", { headers }, logout),
        apiRequest<ManualOpportunity[]>("/api/freelancing/manual", { headers }, logout),
      ]);
      setManualJobs(manual);
      setWorkspace({ overview, jobs, capabilities: capabilities.capabilities ?? [], connection, error: null, loading: false });
    } catch (error) {
      setWorkspace((current) => ({ ...current, loading: false, error: error instanceof Error ? error.message : copy.error }));
    }
  }, [copy.error, logout, token]);

  useEffect(() => { void loadWorkspace(); }, [loadWorkspace]);

  const syncOpportunities = async () => {
    setBusy("sync"); setActionError(null); setSummary(null);
    try {
      const result = await apiRequest<SyncSummary>("/api/freelancing/freelancer/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ query: query.trim() || null, skills: skills.split(",").map((item) => item.trim()).filter(Boolean), limit: 25 }),
      }, logout);
      setSummary(result);
      await loadWorkspace();
    } catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
    finally { setBusy("idle"); }
  };

  const selectJob = async (jobId: string) => {
    setAssessment(null); setActionError(null);
    try { setDetail(await apiRequest<JobDetail>(`/api/freelancing/jobs/${encodeURIComponent(jobId)}`, { headers }, logout)); }
    catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
  };

  const assessJob = async () => {
    if (!detail) return;
    setBusy("assess"); setActionError(null);
    try { setAssessment(await apiRequest<Assessment>(`/api/freelancing/jobs/${encodeURIComponent(detail.job.job_id)}/assess`, { method: "POST", headers }, logout)); }
    catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
    finally { setBusy("idle"); }
  };

  const saveManual = async (analyze: boolean) => {
    if (!manualForm.title.trim() || !manualForm.original_description.trim()) { setManualError("Title and original description are required."); return; }
    if (manualForm.source_url && !/^https?:\/\//i.test(manualForm.source_url)) { setManualError("Source URL must start with http:// or https://."); return; }
    if (manualForm.currency.length !== 3) { setManualError("Currency must be a three-letter code."); return; }
    if (manualForm.budget_min && manualForm.budget_max && Number(manualForm.budget_min) > Number(manualForm.budget_max)) { setManualError("Minimum budget cannot exceed maximum budget."); return; }
    setManualError(null); setDuplicateWarning(null); setBusy("plan");
    const payload = { platform: manualForm.platform, source_url: manualForm.source_url || null, external_project_id: manualForm.external_project_id || null, title: manualForm.title.trim(), original_description: manualForm.original_description, budget_type: manualForm.budget_type, budget_min: manualForm.budget_min ? Number(manualForm.budget_min) : null, budget_max: manualForm.budget_max ? Number(manualForm.budget_max) : null, currency: manualForm.currency.toUpperCase(), required_skills: manualForm.required_skills.split(",").map((item) => item.trim()).filter(Boolean), client_info: manualForm.client_name ? { name: manualForm.client_name.trim() } : {}, source_language: manualForm.source_language, customer_preferred_language: manualForm.customer_preferred_language, proposal_language: manualForm.proposal_language, normalized_requirements: { requirements: [], summary: "Pending analysis" }, translation_metadata: { detected_language_is_suggestion: true }, analyze };
    try {
      const saved = editingJobId
        ? await apiRequest<ManualOpportunity>(`/api/freelancing/manual/${encodeURIComponent(editingJobId)}`, { method: "PATCH", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(payload) }, logout)
        : await apiRequest<ManualOpportunity>("/api/freelancing/manual", { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(payload) }, logout);
      if (editingJobId && analyze) await apiRequest(`/api/freelancing/manual/${encodeURIComponent(editingJobId)}/analyze`, { method: "POST", headers }, logout);
      setManualForm(emptyManualForm); setEditingJobId(null); setManualDetail(saved); await loadWorkspace();
    }
    catch (error) { if (error instanceof ApiError && error.status === 409) setDuplicateWarning("Duplicate warning: this matches an existing opportunity; the existing record was not overwritten."); else setManualError(error instanceof Error ? error.message : copy.error); }
    finally { setBusy("idle"); }
  };

  const selectManual = async (jobId: string) => {
    try { setManualDetail(await apiRequest<ManualOpportunity>(`/api/freelancing/manual/${encodeURIComponent(jobId)}`, { headers }, logout)); }
    catch (error) { setManualError(error instanceof Error ? error.message : copy.error); }
  };

  const editManual = (job: ManualOpportunity) => {
    setEditingJobId(job.job_id); setManualForm({ ...emptyManualForm, platform: job.source, source_url: "", title: job.title, original_description: job.original_text, budget_min: job.budget_min?.toString() ?? "", budget_max: job.budget_max?.toString() ?? "", currency: job.currency ?? "USD", required_skills: job.skills?.join(", ") ?? "", source_language: job.source_language, customer_preferred_language: job.customer_preferred_language, proposal_language: job.proposal_language });
  };

  const prepareProposal = async () => {
    if (!manualDetail) return; setBusy("plan"); setManualError(null);
    try { await apiRequest(`/api/freelancing/manual/${encodeURIComponent(manualDetail.job_id)}/proposal-package`, { method: "POST", headers }, logout); await selectManual(manualDetail.job_id); }
    catch (error) { setManualError(error instanceof Error ? error.message : copy.error); } finally { setBusy("idle"); }
  };

  const recordSubmission = async () => {
    if (!manualDetail || !proposalText.trim()) { setManualError("The exact manually submitted proposal text is required."); return; }
    setBusy("plan");
    try { await apiRequest(`/api/freelancing/manual/${encodeURIComponent(manualDetail.job_id)}/submission`, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify({ proposal_text: proposalText, submitted_price: submittedPrice ? Number(submittedPrice) : null, currency: manualDetail.currency ?? "USD" }) }, logout); setProposalText(""); await selectManual(manualDetail.job_id); }
    catch (error) { setManualError(error instanceof Error ? error.message : copy.error); } finally { setBusy("idle"); }
  };

  const recordOutcome = async () => {
    if (!manualDetail) return; setBusy("plan");
    try { await apiRequest(`/api/freelancing/manual/${encodeURIComponent(manualDetail.job_id)}/outcome`, { method: "PATCH", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify({ outcome }) }, logout); await selectManual(manualDetail.job_id); }
    catch (error) { setManualError(error instanceof Error ? error.message : copy.error); } finally { setBusy("idle"); }
  };

  if (workspace.loading) return <section className="workspace"><div className="eyebrow">{copy.title}</div><h1>{copy.loading}</h1></section>;
  if (workspace.error) return <section className="workspace"><h1>{copy.error}</h1><p className="form-error">{workspace.error}</p><button className="action secondary" onClick={() => void loadWorkspace()}>{copy.retry}</button></section>;

  return <section className="workspace control-center">
    <div className="workspace-header"><div><span className="eyebrow">{copy.title}</span><h1>{copy.title}</h1><p>{copy.intro}</p></div><span className="status">{workspace.overview?.status ?? copy.pending}</span></div>
    <section className="workspace-panel manual-intake-panel">
      <div className="panel-heading"><div><span className="eyebrow">Manual entry</span><h2>Multi-platform opportunity intake</h2></div><span className="status">No live API connection</span></div>
      <p>Paste public project details for analysis. ENIGMA will not connect to an account, submit a proposal, or send a message.</p>
      {duplicateWarning && <p className="duplicate-warning" role="alert">{duplicateWarning}</p>}
      <div className="manual-form">
        <label>Platform<select value={manualForm.platform} onChange={(e) => setManualForm({ ...manualForm, platform: e.target.value })}><option value="workana">Workana</option><option value="peopleperhour">PeoplePerHour</option><option value="upwork">Upwork</option><option value="freelancer">Freelancer.com</option><option value="mostaql">Mostaql</option><option value="other">Other/manual source</option></select></label>
        <label>Source URL<input maxLength={2000} value={manualForm.source_url} onChange={(e) => setManualForm({ ...manualForm, source_url: e.target.value })} placeholder="https://..." /></label>
        <label>External project ID<input maxLength={200} value={manualForm.external_project_id} onChange={(e) => setManualForm({ ...manualForm, external_project_id: e.target.value })} /></label>
        <label className="wide">Title<input required maxLength={500} value={manualForm.title} onChange={(e) => setManualForm({ ...manualForm, title: e.target.value })} /></label>
        <label className="wide">Original project description<textarea required maxLength={30000} value={manualForm.original_description} onChange={(e) => setManualForm({ ...manualForm, original_description: e.target.value })} /></label>
        <label>Budget type<select value={manualForm.budget_type} onChange={(e) => setManualForm({ ...manualForm, budget_type: e.target.value })}><option value="fixed">Fixed</option><option value="hourly">Hourly</option><option value="negotiable">Negotiable</option></select></label>
        <label>Min budget<input type="number" min="0" value={manualForm.budget_min} onChange={(e) => setManualForm({ ...manualForm, budget_min: e.target.value })} /></label><label>Max budget<input type="number" min="0" value={manualForm.budget_max} onChange={(e) => setManualForm({ ...manualForm, budget_max: e.target.value })} /></label><label>Currency<input maxLength={3} value={manualForm.currency} onChange={(e) => setManualForm({ ...manualForm, currency: e.target.value })} /></label>
        <label>Skills<input value={manualForm.required_skills} onChange={(e) => setManualForm({ ...manualForm, required_skills: e.target.value })} placeholder="Python, FastAPI" /></label><label>Public customer information<input maxLength={200} value={manualForm.client_name} onChange={(e) => setManualForm({ ...manualForm, client_name: e.target.value })} /></label>
        {(["source_language", "customer_preferred_language", "proposal_language"] as const).map((field) => <label key={field}>{field.replaceAll("_", " ")}<select value={manualForm[field]} onChange={(e) => setManualForm({ ...manualForm, [field]: e.target.value })}><option value="ar">Arabic</option><option value="en">English</option><option value="es">Spanish</option><option value="fr">French</option></select></label>)}
      </div>
      {manualError && <p className="form-error" role="alert">{manualError}</p>}<div className="manual-actions"><button className="action secondary" disabled={busy !== "idle"} onClick={() => void saveManual(false)}>Save Draft</button><button className="action primary" disabled={busy !== "idle"} onClick={() => void saveManual(true)}>Save and Analyze</button></div>
      <div className="job-list manual-jobs">{manualJobs.map((job) => <button className="job-row" key={job.job_id} onClick={() => void selectManual(job.job_id)}><span><strong>{job.title}</strong><small>{job.source} · Manual entry · {job.lifecycle_status}</small></span><span>{job.submission ? "Submitted manually" : "Not submitted"}</span></button>)}</div>
      {manualDetail && <div className="manual-detail"><h3>{manualDetail.title}</h3><p><strong>{manualDetail.submission ? "Submitted manually" : "Not submitted"}</strong> · {manualDetail.lifecycle_status}</p><h3>Original source content</h3><p className="untrusted-description">{manualDetail.original_text}</p><h3>Normalized requirements</h3><pre>{JSON.stringify(manualDetail.normalized_requirements, null, 2)}</pre><p><strong>Assessment/readiness:</strong> {manualDetail.assessment ? JSON.stringify(manualDetail.assessment) : "Pending"}</p><p><strong>Economics, risks, capability gaps, Academy and Creativity:</strong> populated by the existing analysis workflow when applicable.</p><p><strong>Outcome/learning:</strong> {manualDetail.submission?.outcome_status ?? "Not submitted"}</p></div>}
      {manualDetail && <div className="manual-tracking-actions">
        <button className="action secondary" onClick={() => editManual(manualDetail)} disabled={Boolean(manualDetail.submission)}>Edit before submission</button>
        <button className="action secondary" onClick={() => void prepareProposal()} disabled={busy !== "idle" || Boolean(manualDetail.submission)}>Prepare proposal package</button>
        {!manualDetail.submission && <><label>Exact submitted proposal snapshot<textarea maxLength={30000} value={proposalText} onChange={(e) => setProposalText(e.target.value)} /></label><label>Submitted price<input type="number" min="0" value={submittedPrice} onChange={(e) => setSubmittedPrice(e.target.value)} /></label><button className="action primary" onClick={() => void recordSubmission()} disabled={busy !== "idle"}>Record manual submission</button></>}
        {manualDetail.submission && <><label>Outcome<select value={outcome} onChange={(e) => setOutcome(e.target.value)}><option value="client_replied">Client replied</option><option value="won">Won</option><option value="lost">Lost</option><option value="withdrawn">Withdrawn</option><option value="expired">Expired</option></select></label><button className="action primary" onClick={() => void recordOutcome()} disabled={busy !== "idle"}>Record outcome</button></>}
      </div>}
    </section>
    <section className="workspace-panel sync-panel">
      <div className="panel-heading"><div><span className="eyebrow">Freelancer.com</span><h2>Live opportunity discovery</h2></div><span className="status">{workspace.connection?.state ?? "not_configured"}</span></div>
      <p>Credentials remain server-side. Discovery runs only after this Admin action.</p>
      <div className="sync-controls"><input aria-label="Discovery query" maxLength={200} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Project keywords" /><input aria-label="Discovery skills" value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Skills, comma separated" /><button className="action primary" onClick={() => void syncOpportunities()} disabled={!workspace.connection?.configured || busy !== "idle"}>{busy === "sync" ? "Syncing..." : "Sync opportunities"}</button></div>
      {!workspace.connection?.configured && <p className="empty-state">Freelancer integration is not configured on the server.</p>}
      {workspace.connection?.state === "error" && <p className="form-error">Last sync error: {workspace.connection.last_error_code}</p>}
      {summary && <div className={`sync-summary ${summary.state}`} role="status"><strong>{summary.state === "partial_failure" ? "Sync completed with partial failures" : "Sync completed"}</strong><span>Discovered {summary.discovered}</span><span>Created {summary.created}</span><span>Updated {summary.updated}</span><span>Existing {summary.existing}</span><span>Skipped {summary.skipped}</span><span>Failed {summary.failed}</span></div>}
    </section>
    <div className="control-grid"><section className="workspace-panel jobs-panel"><div className="panel-heading"><div><span className="eyebrow">Freelancer.com</span><h2>{copy.jobs}</h2></div><span className="status">{workspace.jobs.length}</span></div>{workspace.jobs.length ? <div className="job-list">{workspace.jobs.map((job) => <button className={`job-row ${detail?.job.job_id === job.job_id ? "selected" : ""}`} key={job.job_id} onClick={() => void selectJob(job.job_id)}><span><strong>{job.title}</strong><small>{job.source} / {job.skills?.join(", ") || copy.noData}</small><small>Last seen: {job.last_seen_at ? new Date(job.last_seen_at).toLocaleString() : copy.noData}</small></span><span>{job.budget_max !== undefined ? `${job.budget_min ?? ""}–${job.budget_max} ${job.currency ?? ""}` : copy.noData}</span></button>)}</div> : <p className="empty-state">{copy.empty}</p>}</section><section className="workspace-panel capability-panel"><div className="panel-heading"><h2>{copy.capabilities}</h2><span className="status">{workspace.capabilities.length}</span></div>{workspace.capabilities.length ? <div className="capability-list">{workspace.capabilities.slice(0, 8).map((capability) => <div className="capability-row" key={capability.capability_id ?? capability.id ?? capability.name}><span>{capability.name}</span><span>{capability.status ?? capability.readiness_status ?? copy.pending}</span></div>)}</div> : <p className="empty-state">{copy.noData}</p>}</section></div>
    {detail && <section className="workspace-panel opportunity-detail"><div className="panel-heading"><div><span className="eyebrow">{detail.job.source}</span><h2>{detail.job.title}</h2></div><button className="action secondary" onClick={() => { setDetail(null); setAssessment(null); }}>{copy.backToJobs}</button></div><div className="detail-grid"><div><p><strong>{copy.budget}:</strong> {detail.job.budget_max !== undefined ? `${detail.job.budget_min ?? ""}–${detail.job.budget_max} ${detail.job.currency ?? ""}` : copy.noData}</p><p><strong>Last seen:</strong> {detail.job.last_seen_at ? new Date(detail.job.last_seen_at).toLocaleString() : copy.noData}</p><p><strong>{copy.provider}:</strong> {detail.job.client_information ? JSON.stringify(detail.job.client_information) : copy.noProvider}</p></div><div><p>{detail.job.description}</p><p><strong>{copy.skills}:</strong> {detail.job.skills?.join(", ") || copy.noData}</p></div></div><button className="action primary" onClick={() => void assessJob()} disabled={busy !== "idle"}>{busy === "assess" ? copy.assessing : "Analyze project"}</button>{assessment && <div className="workspace-panel nested-panel"><p><strong>{copy.readiness}:</strong> {assessment.readiness}</p><p><strong>{copy.recommendation}:</strong> {assessment.decision}</p><p>{assessment.reasoning_summary}</p></div>}</section>}
    {actionError && <p className="form-error" role="alert">{actionError}</p>}
  </section>;
}
