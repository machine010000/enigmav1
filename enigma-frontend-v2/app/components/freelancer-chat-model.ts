export type Project = {
  project_id: string;
  title: string;
  platform: string;
  lifecycle_status: string;
  client?: Record<string, unknown>;
};

export type ChatMessage = {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string | null;
  project_id?: string | null;
  result?: Record<string, unknown>;
  created_at?: string;
  pending?: boolean;
};

export type CandidateProject = {
  project_id: string;
  title: string;
  platform?: string;
  confidence?: number;
};

export type Verification = {
  recommendation?: string;
  confidence?: number;
  risks: string[];
  missingInformation: string[];
  allowed?: boolean;
};

export type ProjectSnapshot = {
  suitabilityScore?: number;
  recommendation?: string;
  proposalVersions: number;
  proposalReady?: boolean;
  verification?: Verification;
  lastActivity?: string;
};

export function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined;
}

export function asStrings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.trim().length > 0) : [];
}

export function asNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

export function messagesForProject(messages: ChatMessage[], projectId: string): ChatMessage[] {
  if (!projectId) return messages;
  return messages.filter((message) => message.project_id === projectId);
}

export function projectCandidates(result?: Record<string, unknown>): CandidateProject[] {
  const resolution = asRecord(result?.project_resolution);
  const candidates = resolution?.candidate_projects;
  if (!Array.isArray(candidates)) return [];
  return candidates.flatMap((candidate) => {
    const item = asRecord(candidate);
    if (!item || typeof item.project_id !== "string" || typeof item.title !== "string") return [];
    return [{
      project_id: item.project_id,
      title: item.title,
      platform: typeof item.platform === "string" ? item.platform : undefined,
      confidence: asNumber(item.confidence),
    }];
  });
}

export function verificationFrom(result?: Record<string, unknown>): Verification | undefined {
  const raw = asRecord(result?.product_verification) ?? asRecord(result?.verification);
  if (!raw) return undefined;
  return {
    recommendation: typeof raw.recommendation === "string" ? raw.recommendation : undefined,
    confidence: asNumber(raw.confidence),
    risks: asStrings(raw.risks),
    missingInformation: asStrings(raw.missing_information),
    allowed: typeof raw.allowed === "boolean" ? raw.allowed : undefined,
  };
}

export function projectSnapshot(projectId: string, messages: ChatMessage[]): ProjectSnapshot {
  const scoped = messages.filter((message) => message.project_id === projectId && message.role === "assistant");
  let suitabilityScore: number | undefined;
  let recommendation: string | undefined;
  let proposalReady: boolean | undefined;
  let verification: Verification | undefined;
  let proposalVersions = 0;
  let lastActivity: string | undefined;

  for (const message of scoped) {
    const result = message.result;
    suitabilityScore = asNumber(result?.suitability_score) ?? suitabilityScore;
    recommendation = typeof result?.recommendation === "string" ? result.recommendation : recommendation;
    proposalReady = typeof result?.proposal_readiness === "boolean" ? result.proposal_readiness : proposalReady;
    verification = verificationFrom(result) ?? verification;
    if (typeof result?.proposal_version === "number") proposalVersions = Math.max(proposalVersions, result.proposal_version);
    if (message.created_at) lastActivity = message.created_at;
  }

  return { suitabilityScore, recommendation, proposalVersions, proposalReady, verification, lastActivity };
}

export function clientName(project?: Project): string | undefined {
  const value = project?.client?.name ?? project?.client?.username;
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function operationLabel(message: string): string {
  const normalized = message.toLowerCase();
  if (normalized.includes("proposal") || normalized.includes("عرض")) return "Generating a proposal draft…";
  if (normalized.includes("client") || normalized.includes("عميل") || normalized.includes("رد")) return "Reviewing the client message…";
  if (normalized.includes("learn") || normalized.includes("study") || normalized.includes("اتعلم") || normalized.includes("ادرس")) return "Studying the required topic…";
  if (message.length >= 180) return "Analyzing the opportunity…";
  return "ENIGMA is working…";
}
