"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../auth/provider";
import { useLocale } from "../i18n/provider";
import { freelancingCopy } from "../i18n/freelancing";
import { apiRequest } from "../lib/api";

type Overview = { status: string; platforms_connected: number; platforms_total: number; capabilities_ready: number; jobs_discovered: number; applications_total: number };
type Platform = { platform_id: string; name: string; connection_status: string; auth_status: string; profile_status: string };
type Job = { job_id: string; source: string; title: string; description: string; client_information?: Record<string, unknown>; budget?: number; currency?: string; deadline?: string | null; skills?: string[]; discovered_at?: string; metadata?: Record<string, unknown> };
type JobDetail = { job: Job; classification?: Record<string, unknown> | null; evaluation?: Record<string, unknown> | null; assessment?: Record<string, unknown> | null };
type Capability = { id?: string; capability_id?: string; name: string; status?: string; readiness_status?: string; confidence?: number; evidence_count?: number; execution_available?: boolean; meets_threshold?: boolean };
type Assessment = { readiness: string; decision: string; required_capabilities: Array<Record<string, unknown>>; missing_capabilities: string[]; weak_capabilities: string[]; unmapped_skills: string[]; risk_flags: string[]; reasoning_summary: string; overall_score?: number; blocking_capability?: string | null };

type LoadState = { overview: Overview | null; platforms: Platform[]; jobs: Job[]; capabilities: Capability[]; error: string | null; loading: boolean };

export function FreelancingControlCenter() {
  const { locale } = useLocale();
  const { token, logout } = useAuth();
  const copy = freelancingCopy[locale.code as keyof typeof freelancingCopy] ?? freelancingCopy.en;
  const [state, setState] = useState<LoadState>({ overview: null, platforms: [], jobs: [], capabilities: [], error: null, loading: true });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<JobDetail | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [actionState, setActionState] = useState<"idle" | "assessing" | "planning">("idle");
  const [actionError, setActionError] = useState<string | null>(null);
  const [planMessage, setPlanMessage] = useState<string | null>(null);

  const loadWorkspace = useCallback(async () => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const [overview, platforms, jobs, capabilities] = await Promise.all([
        apiRequest<Overview>("/api/freelancing/", token ? { headers: { Authorization: `Bearer ${token}` } } : undefined, logout),
        apiRequest<Platform[]>("/api/freelancing/platforms", token ? { headers: { Authorization: `Bearer ${token}` } } : undefined, logout),
        apiRequest<Job[]>("/api/freelancing/jobs", token ? { headers: { Authorization: `Bearer ${token}` } } : undefined, logout),
        apiRequest<{ capabilities?: Capability[] }>("/api/enigma/profile", token ? { headers: { Authorization: `Bearer ${token}` } } : undefined, logout),
      ]);
      setState({ overview, platforms, jobs, capabilities: capabilities.capabilities ?? [], error: null, loading: false });
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error: error instanceof Error ? error.message : copy.error }));
    }
  }, [copy.error, logout, token]);

  useEffect(() => { void loadWorkspace(); }, [loadWorkspace]);

  const selectJob = async (jobId: string) => {
    setSelectedId(jobId); setAssessment(null); setActionError(null); setPlanMessage(null);
    try { setDetail(await apiRequest<JobDetail>(`/api/freelancing/jobs/${encodeURIComponent(jobId)}`, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined, logout)); }
    catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
  };

  const assessJob = async () => {
    if (!selectedId) return;
    setActionState("assessing"); setActionError(null);
    try { setAssessment(await apiRequest<Assessment>(`/api/freelancing/jobs/${encodeURIComponent(selectedId)}/assess`, { method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : undefined }, logout)); }
    catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
    finally { setActionState("idle"); }
  };

  const generatePlan = async () => {
    if (!detail?.job || !assessment) return;
    setActionState("planning"); setActionError(null); setPlanMessage(null);
    try {
      await apiRequest(`/api/freelancing/opportunities/development-plan`, { method: "POST", headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) }, body: JSON.stringify({ opportunity_id: detail.job.job_id, title: detail.job.title, description: detail.job.description, platform: detail.job.source, external_id: detail.job.job_id, budget_max: detail.job.budget, currency: detail.job.currency, required_skills: detail.job.skills ?? [] }) }, logout);
      setPlanMessage(copy.planReady);
    } catch (error) { setActionError(error instanceof Error ? error.message : copy.error); }
    finally { setActionState("idle"); }
  };

  if (state.loading) return <section className="workspace"><div className="eyebrow">{copy.title}</div><h1>{copy.loading}</h1></section>;
  if (state.error) return <section className="workspace"><div className="eyebrow">{copy.title}</div><h1>{copy.error}</h1><p className="form-error">{state.error}</p><button className="action secondary" onClick={() => void loadWorkspace()}>{copy.retry}</button></section>;

  const connected = state.platforms.filter((platform) => platform.connection_status === "connected");
  const selectedJob = state.jobs.find((job) => job.job_id === selectedId);
  const stages = [
    [copy.marketplace, connected.length ? copy.connected : copy.notConnected], [copy.verification, selectedJob ? (assessment ? assessment.readiness : copy.pending) : copy.pending], [copy.provider, detail?.job.client_information && Object.keys(detail.job.client_information).length ? copy.connected : copy.notConnected], [copy.capabilities, state.capabilities.length ? copy.connected : copy.pending], [copy.academy, assessment?.readiness === "learn_first" ? copy.connected : copy.reserved], [copy.creativity, copy.reserved], [copy.decision, assessment?.decision ?? copy.pending], [copy.applications, copy.reserved], [copy.activeWork, copy.reserved],
  ];

  return <section className="workspace control-center"><div className="eyebrow">{copy.title}</div><div className="workspace-header"><div><h1>{copy.title}</h1><p>{copy.intro}</p></div><span className="status">{state.overview?.status ?? copy.pending}</span></div><div className="workflow-strip">{stages.map(([label, status], index) => <div className="workflow-stage" key={label}><span className="module-index">0{index + 1}</span><strong>{label}</strong><span className="stage-status">{status}</span>{index < stages.length - 1 && <span className="stage-arrow" aria-hidden="true">↓</span>}</div>)}</div><div className="control-grid"><section className="workspace-panel jobs-panel"><div className="panel-heading"><div><span className="eyebrow">{copy.marketplace}</span><h2>{copy.jobs}</h2></div><span className="status">{state.jobs.length ? `${state.jobs.length}` : copy.empty}</span></div>{state.jobs.length ? <div className="job-list">{state.jobs.map((job) => <button className={`job-row ${selectedId === job.job_id ? "selected" : ""}`} key={job.job_id} onClick={() => void selectJob(job.job_id)}><span><strong>{job.title}</strong><small>{job.source} / {job.skills?.join(", ") || copy.noData}</small></span><span>{job.budget !== undefined ? `${job.budget} ${job.currency ?? ""}` : copy.noData}</span></button>)}</div> : <p className="empty-state">{copy.empty}</p>}</section><section className="workspace-panel capability-panel"><div className="panel-heading"><div><span className="eyebrow">{copy.capabilities}</span><h2>{copy.capabilities}</h2></div><span className="status">{state.capabilities.length ? copy.connected : copy.pending}</span></div>{state.capabilities.length ? <div className="capability-list">{state.capabilities.slice(0, 8).map((capability) => <div className="capability-row" key={capability.capability_id ?? capability.id ?? capability.name}><span>{capability.name}</span><span className="stage-status">{capability.status ?? capability.readiness_status ?? copy.pending}</span></div>)}</div> : <p className="empty-state">{copy.noData}</p>}</section></div>{detail && <section className="workspace-panel opportunity-detail"><div className="panel-heading"><div><span className="eyebrow">{copy.verification}</span><h2>{detail.job.title}</h2></div><button className="action secondary" onClick={() => { setDetail(null); setSelectedId(null); }}>{copy.backToJobs}</button></div><div className="detail-grid"><div><p><strong>{copy.project}:</strong> {detail.job.title}</p><p><strong>{copy.marketplace}:</strong> {detail.job.source}</p><p><strong>{copy.budget}:</strong> {detail.job.budget !== undefined ? `${detail.job.budget} ${detail.job.currency ?? ""}` : copy.noData}</p><p><strong>{copy.status}:</strong> {detail.assessment ? String(detail.assessment.recommendation ?? copy.pending) : copy.pending}</p></div><div><p><strong>{copy.description}</strong></p><p>{detail.job.description}</p><p><strong>{copy.skills}</strong></p><p>{detail.job.skills?.join(", ") || copy.noData}</p></div></div><div className="workspace-grid"><div className="workspace-panel nested-panel"><h3>{copy.provider}</h3><p>{detail.job.client_information && Object.keys(detail.job.client_information).length ? JSON.stringify(detail.job.client_information) : copy.noProvider}</p></div><div className="workspace-panel nested-panel"><h3>{copy.verification}</h3>{assessment ? <><p><strong>{copy.readiness}:</strong> {assessment.readiness}</p><p><strong>{copy.recommendation}:</strong> {assessment.decision}</p>{assessment.blocking_capability && <p><strong>{copy.blockers}:</strong> {assessment.blocking_capability}</p>}<p>{assessment.reasoning_summary}</p>{assessment.missing_capabilities.length > 0 && <p><strong>{copy.missing}:</strong> {assessment.missing_capabilities.join(", ")}</p>}</> : <p>{copy.noAssessment}</p>}<button className="action primary" onClick={() => void assessJob()} disabled={actionState !== "idle"}>{actionState === "assessing" ? copy.assessing : copy.assess}</button></div></div>{assessment?.readiness === "learn_first" && <div className="workspace-panel handoff-panel"><h3>{copy.plan}</h3><p>{planMessage ?? copy.pending}</p><button className="action secondary" onClick={() => void generatePlan()} disabled={actionState !== "idle"}>{actionState === "planning" ? copy.planLoading : copy.generatePlan}</button></div>}{actionError && <p className="form-error" role="alert">{actionError}</p>}</section>}</section>;
}
