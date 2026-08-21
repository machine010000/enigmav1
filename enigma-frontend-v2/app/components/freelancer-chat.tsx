"use client";

import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../auth/provider";
import { ApiError, apiRequest } from "../lib/api";
import {
  asStrings,
  ChatMessage,
  clientName,
  messagesForProject,
  operationLabel,
  Project,
  projectCandidates,
  projectSnapshot,
  verificationFrom,
} from "./freelancer-chat-model";

type ChatResponse = {
  conversation_id: string;
  message_id: string;
  project_id?: string | null;
  resolved_intent: string;
  reply: string;
  result: Record<string, unknown>;
  capabilities_invoked: string[];
};

type Conversation = { active_project_id?: string | null; messages: ChatMessage[] };
type LoadingState = "idle" | "projects" | "conversation" | "sending";

const conversationStorageKey = "enigma.freelancerChat.conversationId";

function percent(value?: number) {
  return value === undefined ? "Pending" : `${Math.round(value * 100)}%`;
}

function ResultList({ title, values }: { title: string; values: string[] }) {
  if (!values.length) return null;
  return <div className="result-list"><strong>{title}</strong><ul>{values.map((value, index) => <li key={`${value}-${index}`}>{value}</li>)}</ul></div>;
}

function VerificationCard({ result }: { result?: Record<string, unknown> }) {
  const verification = verificationFrom(result);
  if (!verification) return null;
  const verdict = verification.recommendation ?? (verification.allowed ? "pass" : "review");
  return <section className={`structured-card verification-card verdict-${verdict}`}>
    <div className="structured-heading"><strong>Product verification</strong><span className="result-pill">{verdict}</span></div>
    <p>Confidence: <strong>{percent(verification.confidence)}</strong></p>
    <ResultList title="Risks" values={verification.risks} />
    <ResultList title="Missing information" values={verification.missingInformation} />
  </section>;
}

function AnalysisCard({ result, onGenerate }: { result: Record<string, unknown>; onGenerate: () => void }) {
  const examples = Array.isArray(result.relevant_prior_examples) ? result.relevant_prior_examples : [];
  return <section className="structured-card analysis-card">
    <div className="structured-heading"><strong>Opportunity analysis</strong><span className="result-pill">{String(result.recommendation ?? "review")}</span></div>
    {typeof result.title === "string" && <h4>{result.title}</h4>}
    {typeof result.summary === "string" && <p>{result.summary}</p>}
    <div className="metric-row"><span>Suitability <strong>{percent(typeof result.suitability_score === "number" ? result.suitability_score : undefined)}</strong></span><span>Proposal readiness <strong>{result.proposal_readiness === true ? "Ready" : "Review needed"}</strong></span></div>
    <ResultList title="Risks" values={asStrings(result.risks)} />
    <ResultList title="Missing information" values={asStrings(result.missing_information)} />
    {examples.length > 0 && <p className="context-note">{examples.length} relevant prior example{examples.length === 1 ? "" : "s"} informed this analysis.</p>}
    <VerificationCard result={result} />
    <button className="action primary compact-action" type="button" onClick={onGenerate}>Generate proposal</button>
  </section>;
}

function ProposalCard({ result, onCopy, onRevise }: { result: Record<string, unknown>; onCopy: (text: string, label: string) => void; onRevise: () => void }) {
  const proposal = typeof result.proposal_text === "string" ? result.proposal_text : "";
  return <section className="structured-card proposal-card">
    <div className="structured-heading"><strong>Proposal draft</strong><span className="result-pill">Version {String(result.proposal_version ?? 1)}</span></div>
    <p className="manual-notice">Manual copy only — ENIGMA has not submitted this proposal.</p>
    <div className="copyable-text">{proposal || "The draft needs more information."}</div>
    <VerificationCard result={result} />
    <div className="card-actions"><button className="action primary compact-action" type="button" onClick={() => onCopy(proposal, "Proposal copied")} disabled={!proposal}>Copy proposal</button><button className="action secondary compact-action" type="button" onClick={onRevise}>Request revision</button></div>
  </section>;
}

function ClientCard({ intent, result, content, onCopy }: { intent?: string | null; result: Record<string, unknown>; content: string; onCopy: (text: string, label: string) => void }) {
  const response = typeof result.response === "string" ? result.response : content;
  return <section className="structured-card client-card">
    <div className="structured-heading"><strong>{intent === "client_message" ? "Client message review" : "Suggested client reply"}</strong><span className="result-pill">Manual send</span></div>
    <ResultList title="Extracted requirements" values={asStrings(result.requirements)} />
    <ResultList title="Client questions" values={asStrings(result.questions)} />
    <ResultList title="Missing clarification" values={asStrings(result.missing_clarification)} />
    {response && <div className="copyable-text">{response}</div>}
    <button className="action secondary compact-action" type="button" onClick={() => onCopy(response, "Reply copied")}>Copy reply</button>
  </section>;
}

function AcademyCard({ result }: { result: Record<string, unknown> }) {
  const summary = typeof result.knowledge_summary === "string" ? result.knowledge_summary : undefined;
  if (!summary && typeof result.academy_artifact_id !== "string") return null;
  return <section className="structured-card academy-card"><div className="structured-heading"><strong>Academy learning</strong><span className="result-pill">Project private</span></div>{summary && <p>{summary}</p>}<ResultList title="Execution checklist" values={asStrings(result.execution_checklist)} /><p className="context-note">Knowledge is available to this project because the backend reported a durable Academy artifact.</p></section>;
}

function CreativityNote({ capabilities }: { capabilities: unknown }) {
  const values = asStrings(capabilities);
  if (!values.includes("creativity")) return null;
  return <p className="capability-note"><strong>Creativity:</strong> alternative proposal angles were considered for this draft.</p>;
}

function WorkflowStatus({ result }: { result: Record<string, unknown> }) {
  if (result.status !== "project_required" && result.status !== "blocked") return null;
  return <section className="structured-card workflow-status"><strong>{result.status === "project_required" ? "Choose a project to continue" : "Action blocked safely"}</strong><p>{result.status === "project_required" ? "Select an owned project from the sidebar, then resend the request." : "The backend kept lifecycle, approval, and submission safeguards authoritative."}</p></section>;
}

function MessageResult({ message, onAction, onCopy, onChoose }: {
  message: ChatMessage;
  onAction: (message: string) => void;
  onCopy: (text: string, label: string) => void;
  onChoose: (projectId: string) => void;
}) {
  const result = message.result ?? {};
  const candidates = projectCandidates(result);
  if (candidates.length) return <section className="structured-card ambiguity-card"><strong>Choose the intended project</strong><p>ENIGMA did not select one automatically.</p><div className="candidate-list">{candidates.map((candidate) => <button type="button" className="candidate-button" key={candidate.project_id} onClick={() => onChoose(candidate.project_id)}><span>{candidate.title}</span><small>{candidate.platform ?? "Project"}{candidate.confidence !== undefined ? ` · ${percent(candidate.confidence)}` : ""}</small></button>)}</div><p className="context-note">After choosing, resend or continue the intended action.</p></section>;
  if (message.intent === "new_opportunity" || message.intent === "opportunity_analysis") return <AnalysisCard result={result} onGenerate={() => onAction("Generate a proposal for this project")} />;
  if (message.intent === "proposal_request") return <><ProposalCard result={result} onCopy={onCopy} onRevise={() => onAction("Revise the latest proposal with a clearer, more specific approach")} /><CreativityNote capabilities={result.capabilities_invoked} /></>;
  if (message.intent === "client_message" || message.intent === "client_reply_request") return <ClientCard intent={message.intent} result={result} content={message.content} onCopy={onCopy} />;
  if (message.intent === "learning_request") return <AcademyCard result={result} />;
  return <><WorkflowStatus result={result} /><VerificationCard result={result} />{typeof result.next_action === "string" && <p className="next-action"><strong>Next:</strong> {result.next_action}</p>}</>;
}

export function FreelancerChat() {
  const { token, logout } = useAuth();
  const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState<LoadingState>("projects");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [operation, setOperation] = useState("ENIGMA is working…");
  const historyRef = useRef<HTMLDivElement>(null);

  const loadProjects = useCallback(async () => {
    setLoading((current) => current === "conversation" || current === "sending" ? current : "projects");
    try {
      const result = await apiRequest<Project[]>("/api/freelancing/chat/projects", { headers }, logout);
      setProjects(result);
      return result;
    } catch (reason) {
      setProjects([]);
      setError(reason instanceof Error ? reason.message : "Could not load projects.");
      return [];
    } finally { setLoading((current) => current === "projects" ? "idle" : current); }
  }, [headers, logout]);

  const loadConversation = useCallback(async (id: string) => {
    setLoading("conversation");
    try {
      const result = await apiRequest<Conversation>(`/api/freelancing/chat/conversations/${encodeURIComponent(id)}`, { headers }, logout);
      setConversationId(id);
      setMessages(result.messages);
      setProjectId(result.active_project_id ?? "");
      setError(null);
    } catch (reason) {
      window.localStorage.removeItem(conversationStorageKey);
      setConversationId(null);
      setMessages([]);
      if (!(reason instanceof ApiError && reason.status === 404)) setError(reason instanceof Error ? reason.message : "Could not restore the conversation.");
    } finally { setLoading("idle"); }
  }, [headers, logout]);

  useEffect(() => {
    const stored = window.localStorage.getItem(conversationStorageKey);
    void loadProjects();
    if (stored) void loadConversation(stored);
  }, [loadConversation, loadProjects]);

  useEffect(() => { historyRef.current?.scrollTo({ top: historyRef.current.scrollHeight, behavior: "smooth" }); }, [messages, projectId, loading]);

  const sendMessage = useCallback(async (message: string, explicitProjectId = projectId) => {
    const trimmed = message.trim();
    if (!trimmed || loading === "sending") return;
    const pendingId = `pending-${Date.now()}`;
    setOperation(operationLabel(trimmed));
    setLoading("sending");
    setError(null);
    setNotice(null);
    setMessages((current) => [...current, { message_id: pendingId, role: "user", content: trimmed, project_id: explicitProjectId || null, created_at: new Date().toISOString(), pending: true }]);
    setInput("");
    try {
      const response = await apiRequest<ChatResponse>("/api/freelancing/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ message: trimmed, conversation_id: conversationId, project_id: explicitProjectId || null }),
      }, logout);
      setConversationId(response.conversation_id);
      window.localStorage.setItem(conversationStorageKey, response.conversation_id);
      if (response.project_id) setProjectId(response.project_id);
      setMessages((current) => [...current.filter((item) => item.message_id !== pendingId),
        { message_id: pendingId, role: "user", content: trimmed, intent: response.resolved_intent, project_id: (response.project_id ?? explicitProjectId) || null, created_at: new Date().toISOString() },
        { message_id: response.message_id, role: "assistant", content: response.reply, intent: response.resolved_intent, project_id: response.project_id, result: response.result, created_at: new Date().toISOString() },
      ]);
      await loadProjects();
    } catch (reason) {
      setMessages((current) => current.filter((item) => item.message_id !== pendingId));
      if (reason instanceof ApiError && reason.status === 409 && reason.code === "duplicate_opportunity") {
        setError(`This opportunity already exists${reason.existingJobId ? ` as project ${reason.existingJobId}` : ""}. The existing record was not overwritten.`);
        if (reason.existingJobId && projects.some((project) => project.project_id === reason.existingJobId)) setProjectId(reason.existingJobId);
      } else if (reason instanceof ApiError && reason.status === 422) setError(`Please check the message or opportunity details. ${reason.message}`);
      else if (reason instanceof ApiError && reason.status >= 500) setError("ENIGMA or its AI provider is temporarily unavailable. Your project data was not submitted externally.");
      else setError(reason instanceof Error ? reason.message : "Chat request failed.");
    } finally { setLoading("idle"); }
  }, [conversationId, headers, loadProjects, loading, logout, projectId, projects]);

  const send = (event: FormEvent) => { event.preventDefault(); void sendMessage(input); };
  const selectedProject = projects.find((project) => project.project_id === projectId);
  const visibleMessages = messagesForProject(messages, projectId);
  const snapshot = projectId ? projectSnapshot(projectId, messages) : undefined;

  const startGeneral = () => {
    setProjectId(""); setConversationId(null); setMessages([]); setError(null); setNotice("A new general Chat will begin with your next message.");
    window.localStorage.removeItem(conversationStorageKey);
  };

  const chooseProject = (id: string) => { setProjectId(id); setError(null); setNotice("Project selected. Continue or resend the intended action."); };

  const copyText = async (text: string, label: string) => {
    try { await navigator.clipboard.writeText(text); setNotice(label); }
    catch { setError("Copy was blocked by the browser. Select the text and copy it manually."); }
  };

  const client = clientName(selectedProject);

  return <section className="freelancer-chat-workspace">
    <header className="chat-titlebar">
      <div><span className="eyebrow">Freelancer Chat</span><h2>Work across projects without losing context</h2><p>Analyze, draft, learn, and plan. Every proposal and client reply remains a manual action.</p></div>
      <span className="status">No automatic submission</span>
    </header>

    <div className="chat-layout">
      <aside className="project-sidebar" aria-label="Freelancer projects">
        <div className="sidebar-heading"><div><strong>Projects</strong><small>{projects.length} available</small></div><button type="button" className="icon-action" onClick={() => void loadProjects()} aria-label="Refresh projects">↻</button></div>
        <button type="button" className={`project-card general ${!projectId ? "selected" : ""}`} onClick={startGeneral}><strong>New opportunity / general Chat</strong><small>Paste a job or start a clean thread</small></button>
        {loading === "projects" && <p className="sidebar-state">Loading projects…</p>}
        {loading !== "projects" && projects.length === 0 && <p className="sidebar-state">No projects yet. Paste your first opportunity in Chat.</p>}
        <div className="project-list">{projects.map((project) => {
          const projectView = projectSnapshot(project.project_id, messages);
          return <button type="button" className={`project-card ${project.project_id === projectId ? "selected" : ""}`} key={project.project_id} onClick={() => chooseProject(project.project_id)}>
            <span className="project-card-top"><strong>{project.title}</strong><span className="lifecycle-chip">{project.lifecycle_status}</span></span>
            <small>{project.platform || "Unknown platform"}{clientName(project) ? ` · ${clientName(project)}` : ""}</small>
            <small>{projectView.lastActivity ? `Last activity ${new Date(projectView.lastActivity).toLocaleString()}` : "No activity in this conversation yet"}</small>
          </button>;
        })}</div>
      </aside>

      <main className="chat-main">
        <section className="project-context" aria-label="Current project context">
          {selectedProject ? <>
            <div className="context-title"><div><span className="eyebrow">Current project</span><h3>{selectedProject.title}</h3></div><span className="lifecycle-chip prominent">{selectedProject.lifecycle_status}</span></div>
            <div className="context-metrics"><span>Platform<strong>{selectedProject.platform || "Unknown"}</strong></span><span>Client<strong>{client ?? "Not provided"}</strong></span><span>Suitability<strong>{percent(snapshot?.suitabilityScore)}</strong></span><span>Recommendation<strong>{snapshot?.recommendation ?? "Pending"}</strong></span><span>Proposals<strong>{snapshot?.proposalVersions ? `${snapshot.proposalVersions} in this chat` : "None in this chat"}</strong></span><span>Verification<strong>{snapshot?.verification?.recommendation ?? "Pending"}</strong></span></div>
            <div className="quick-actions"><button type="button" onClick={() => void sendMessage("Analyze whether this project is worth applying to")}>Analyze</button><button type="button" onClick={() => void sendMessage("Generate a proposal for this project")}>Generate proposal</button><button type="button" onClick={() => { setInput("Client said: "); document.getElementById("freelancer-chat-input")?.focus(); }}>Paste client reply</button>{selectedProject.lifecycle_status === "won" && <button type="button" onClick={() => void sendMessage("Create an execution plan for this won project")}>Continue project work</button>}</div>
          </> : <div className="general-context"><span className="eyebrow">General Freelancer Chat</span><h3>Paste a new opportunity or ask about your freelance work</h3><p>No project is selected. ENIGMA will ask rather than guess when a reference is ambiguous.</p></div>}
        </section>

        <div className="chat-history" ref={historyRef} aria-live="polite" aria-busy={loading === "conversation" || loading === "sending"}>
          {loading === "conversation" && <p className="empty-state">Loading durable conversation history…</p>}
          {loading !== "conversation" && visibleMessages.length === 0 && <div className="chat-empty"><strong>{selectedProject ? "No messages for this project in the current conversation." : "Start your Freelancer conversation."}</strong><p>{selectedProject ? "Use a quick action or write naturally below." : "Paste a job description, ask for analysis, or select an existing project."}</p></div>}
          {visibleMessages.map((message) => <article className={`chat-message ${message.role} intent-${message.intent ?? "message"}`} key={message.message_id}>
            <small>{message.role === "assistant" ? "ENIGMA" : message.intent === "client_message" ? "Client message (pasted by you)" : "You"}{message.intent ? ` · ${message.intent.replaceAll("_", " ")}` : ""}</small>
            <p>{message.content}</p>
            {message.role === "assistant" && message.result && <MessageResult message={message} onAction={(value) => void sendMessage(value)} onCopy={copyText} onChoose={chooseProject} />}
          </article>)}
          {loading === "sending" && <div className="processing-state" role="status"><span className="processing-dot" />{operation}</div>}
        </div>

        <form className="chat-composer" onSubmit={send}>
          <label htmlFor="freelancer-chat-input">Message, opportunity, or client reply</label>
          <textarea id="freelancer-chat-input" maxLength={30000} value={input} onChange={(event) => setInput(event.target.value)} placeholder={selectedProject ? `Continue ${selectedProject.title}…` : "Paste a job description or ask ENIGMA…"} />
          <div className="composer-footer"><span>{selectedProject ? `Working in ${selectedProject.title}` : "General / new opportunity"}</span><button className="action primary" disabled={loading === "sending" || !input.trim()}>{loading === "sending" ? "Working…" : "Send"}</button></div>
        </form>
        <p className="manual-notice persistent">ENIGMA never submits proposals or sends client messages from this Chat. Copy reviewed drafts manually.</p>
        {notice && <p className="chat-notice" role="status">{notice}</p>}
        {error && <div className="chat-error" role="alert"><strong>Could not complete that action</strong><p>{error}</p><button type="button" className="action secondary compact-action" onClick={() => setError(null)}>Dismiss</button></div>}
      </main>
    </div>
  </section>;
}
