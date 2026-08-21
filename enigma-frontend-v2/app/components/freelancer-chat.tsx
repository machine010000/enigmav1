"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../auth/provider";
import { apiRequest } from "../lib/api";

type Project = { project_id: string; title: string; platform: string; lifecycle_status: string };
type ChatMessage = { message_id: string; role: "user" | "assistant"; content: string; intent?: string; project_id?: string | null; result?: Record<string, unknown> };
type ChatResponse = { conversation_id: string; message_id: string; project_id?: string | null; resolved_intent: string; reply: string; result: Record<string, unknown>; capabilities_invoked: string[] };

const conversationStorageKey = "enigma.freelancerChat.conversationId";

export function FreelancerChat() {
  const { token, logout } = useAuth();
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const stored = window.localStorage.getItem(conversationStorageKey);
    void apiRequest<Project[]>("/api/freelancing/chat/projects", { headers }, logout).then(setProjects).catch(() => setProjects([]));
    if (!stored) return;
    void apiRequest<{ active_project_id?: string | null; messages: ChatMessage[] }>(`/api/freelancing/chat/conversations/${encodeURIComponent(stored)}`, { headers }, logout)
      .then((result) => { setConversationId(stored); setMessages(result.messages); setProjectId(result.active_project_id ?? ""); })
      .catch(() => window.localStorage.removeItem(conversationStorageKey));
  }, [token]); // Auth changes intentionally reload persisted server state.

  const send = async (event: FormEvent) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    setBusy(true); setError(null);
    setMessages((current) => [...current, { message_id: `pending-${Date.now()}`, role: "user", content: message, project_id: projectId || null }]);
    setInput("");
    try {
      const response = await apiRequest<ChatResponse>("/api/freelancing/chat", {
        method: "POST", headers: { "Content-Type": "application/json", ...headers },
        body: JSON.stringify({ message, conversation_id: conversationId, project_id: projectId || null }),
      }, logout);
      setConversationId(response.conversation_id);
      window.localStorage.setItem(conversationStorageKey, response.conversation_id);
      if (response.project_id) setProjectId(response.project_id);
      setMessages((current) => [...current, { message_id: response.message_id, role: "assistant", content: response.reply, intent: response.resolved_intent, project_id: response.project_id, result: response.result }]);
      void apiRequest<Project[]>("/api/freelancing/chat/projects", { headers }, logout).then(setProjects);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Chat request failed.");
    } finally { setBusy(false); }
  };

  return <section className="workspace-panel freelancer-chat-panel">
    <div className="panel-heading"><div><span className="eyebrow">Freelancer Chat</span><h2>Project-aware assistant</h2></div><span className="status">Manual actions only</span></div>
    <p>Paste an opportunity or ask naturally. ENIGMA drafts and analyzes; it never submits proposals or sends client messages.</p>
    <label>Current project (optional)<select value={projectId} onChange={(event) => setProjectId(event.target.value)}><option value="">Resolve from conversation</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.title} · {project.lifecycle_status}</option>)}</select></label>
    <div className="chat-history" aria-live="polite">
      {messages.length === 0 && <p className="empty-state">Start by pasting a job description or asking about an existing project.</p>}
      {messages.map((message) => <article className={`chat-message ${message.role}`} key={message.message_id}><small>{message.role}{message.intent ? ` · ${message.intent}` : ""}</small><p>{message.content}</p>{message.role === "assistant" && message.result && <details><summary>Structured result</summary><pre>{JSON.stringify(message.result, null, 2)}</pre></details>}</article>)}
    </div>
    <form className="chat-composer" onSubmit={send}><textarea aria-label="Freelancer Chat message" maxLength={30000} value={input} onChange={(event) => setInput(event.target.value)} placeholder="Paste an opportunity, client reply, or ask for a proposal..." /><button className="action primary" disabled={busy || !input.trim()}>{busy ? "Working..." : "Send"}</button></form>
    {error && <p className="form-error" role="alert">{error}</p>}
  </section>;
}
