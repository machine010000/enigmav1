"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../auth/provider";
import { useLocale } from "../i18n/provider";
import { freelancingCopy } from "../i18n/freelancing";
import { apiRequest } from "../lib/api";

type Overview = { status: string; jobs_discovered: number };
type Job = { job_id: string; source: string; title: string; description: string; client_information?: Record<string, unknown>; budget_min?: number; budget_max?: number; currency?: string; skills?: string[]; last_seen_at?: string };
type JobDetail = { job: Job; assessment?: Record<string, unknown> | null };
type Capability = { id?: string; capability_id?: string; name: string; status?: string; readiness_status?: string };
type Assessment = { readiness: string; decision: string; missing_capabilities: string[]; reasoning_summary: string; blocking_capability?: string | null };
type Connection = { state: "not_configured" | "configured" | "connected" | "error"; configured: boolean; sandbox: boolean; last_sync_at?: string | null; last_error_code?: string | null };
type SyncSummary = { state: "success" | "partial_failure"; created: number; updated: number; existing: number; skipped: number; failed: number; discovered: number };
type Workspace = { overview: Overview | null; jobs: Job[]; capabilities: Capability[]; connection: Connection | null; error: string | null; loading: boolean };

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
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

  const loadWorkspace = useCallback(async () => {
    setWorkspace((current) => ({ ...current, loading: true, error: null }));
    try {
      const [overview, jobs, capabilities, connection] = await Promise.all([
        apiRequest<Overview>("/api/freelancing/", { headers }, logout),
        apiRequest<Job[]>("/api/freelancing/jobs", { headers }, logout),
        apiRequest<{ capabilities?: Capability[] }>("/api/enigma/profile", { headers }, logout),
        apiRequest<Connection>("/api/freelancing/freelancer/connection/status", { headers }, logout),
      ]);
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

  if (workspace.loading) return <section className="workspace"><div className="eyebrow">{copy.title}</div><h1>{copy.loading}</h1></section>;
  if (workspace.error) return <section className="workspace"><h1>{copy.error}</h1><p className="form-error">{workspace.error}</p><button className="action secondary" onClick={() => void loadWorkspace()}>{copy.retry}</button></section>;

  return <section className="workspace control-center">
    <div className="workspace-header"><div><span className="eyebrow">{copy.title}</span><h1>{copy.title}</h1><p>{copy.intro}</p></div><span className="status">{workspace.overview?.status ?? copy.pending}</span></div>
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
