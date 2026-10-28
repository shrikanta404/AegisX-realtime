import axios from "axios";

import type {
  AIAnalysis,
  AuditLog,
  AssetItem,
  AssetSummary,
  Change,
  DashboardSummary,
  Finding,
  FindingDetail,
  MonitoringResult,
  Scope,
  SchedulerStatus,
  SecurityReport,
} from "../types/api";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

/* =========================================================
   ERROR HANDLING
   ========================================================= */

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (
      typeof detail === "object" &&
      detail !== null &&
      "message" in detail
    ) {
      return String(
        (detail as { message?: unknown }).message ??
        "Request failed.",
      );
    }

    if (typeof error.message === "string") {
      return error.message;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Request failed.";
}

export { getErrorMessage };

/* =========================================================
   DASHBOARD
   ========================================================= */

export async function getDashboard(): Promise<DashboardSummary> {
  const { data } =
    await api.get<DashboardSummary>("/dashboard/summary");

  return data;
}

/* =========================================================
   ASSETS
   ========================================================= */

export async function getAssets(
  params: {
    scope_id?: number;
    search?: string;
  } = {},
): Promise<{
  summary: AssetSummary;
  assets: AssetItem[];
}> {
  const { data } = await api.get<{
    summary: AssetSummary;
    assets: AssetItem[];
  }>("/assets", {
    params,
  });

  return data;
}

/* =========================================================
   CHANGES
   ========================================================= */

export async function getChanges(
  params: {
    scope_id?: number;
    domain?: string;
    limit?: number;
  } = {},
): Promise<Change[]> {
  const { data } = await api.get<Change[]>("/changes", {
    params,
  });

  return data;
}

/* =========================================================
   FINDINGS
   ========================================================= */

export async function getFindings(
  params: {
    status?: string;
    severity?: string;
    finding_type?: string;
    limit?: number;
  } = {},
): Promise<Finding[]> {
  const { data } = await api.get<Finding[]>("/findings", {
    params,
  });

  return data;
}

export async function getFinding(
  findingId: number,
): Promise<FindingDetail> {
  const { data } =
    await api.get<FindingDetail>(
      `/findings/${findingId}`,
    );

  return data;
}

export async function addEvidence(
  findingId: number,
  evidenceType: string,
  evidenceData: unknown,
): Promise<void> {
  await api.post(
    `/findings/${findingId}/evidence`,
    {
      evidence_type: evidenceType,
      evidence_data: evidenceData,
    },
  );
}

export async function markFalsePositive(
  findingId: number,
  reason: string,
): Promise<void> {
  await api.patch(
    `/findings/${findingId}/false-positive`,
    {
      reason,
    },
    {
      headers: {
        "X-Actor": "AegisX UI",
      },
    },
  );
}

/* =========================================================
   AUTHORIZED SCOPES
   ========================================================= */

export async function getScopes(): Promise<Scope[]> {
  const { data } =
    await api.get<Scope[]>("/scopes");

  return data;
}

export async function createScope(payload: {
  name: string;
  domain: string;
  allowed_ports?: string;
  allowed_checks?: string;
  description?: string;
}): Promise<Scope> {
  const { data } =
    await api.post<Scope>(
      "/scopes",
      payload,
      {
        headers: {
          "X-Actor": "AegisX UI",
        },
      },
    );

  return data;
}

export async function updateScope(
  scopeId: number,
  payload: Partial<Scope>,
): Promise<Scope> {
  const { data } =
    await api.patch<Scope>(
      `/scopes/${scopeId}`,
      payload,
      {
        headers: {
          "X-Actor": "AegisX UI",
        },
      },
    );

  return data;
}

export async function deactivateScope(
  scopeId: number,
): Promise<void> {
  await api.delete(
    `/scopes/${scopeId}`,
    {
      headers: {
        "X-Actor": "AegisX UI",
      },
    },
  );
}

/* =========================================================
   SCHEDULER
   ========================================================= */

export async function getSchedulerStatus(): Promise<SchedulerStatus> {
  const { data } =
    await api.get<SchedulerStatus>(
      "/scheduler/status",
    );

  return data;
}

export async function startScheduler(): Promise<SchedulerStatus> {
  const { data } =
    await api.post<SchedulerStatus>(
      "/scheduler/start",
    );

  return data;
}

export async function stopScheduler(): Promise<SchedulerStatus> {
  const { data } =
    await api.post<SchedulerStatus>(
      "/scheduler/stop",
    );

  return data;
}

export async function runMonitoring(
  domain: string,
): Promise<MonitoringResult> {
  let normalizedDomain = domain.trim();

  // Accept either:
  // www.example.com
  // or https://www.example.com/
  try {
    if (
      normalizedDomain.startsWith("http://") ||
      normalizedDomain.startsWith("https://")
    ) {
      normalizedDomain = new URL(normalizedDomain).hostname;
    }
  } catch {
    // Fall back to simple normalization below.
  }

  normalizedDomain = normalizedDomain
    .trim()
    .toLowerCase()
    .replace(/\.$/, "");

  if (!normalizedDomain) {
    throw new Error("A valid authorized domain is required.");
  }

  const { data } = await api.post<MonitoringResult>(
    `/scheduler/live/${encodeURIComponent(normalizedDomain)}`,
  );

  return data;
}

/* =========================================================
   REPORTS
   ========================================================= */

export async function getReport(
  days = 7,
  scopeId?: number,
): Promise<SecurityReport> {
  const { data } =
    await api.get<SecurityReport>(
      "/reports/security",
      {
        params: {
          days,
          ...(scopeId !== undefined
            ? { scope_id: scopeId }
            : {}),
        },
      },
    );

  return data;
}

/* =========================================================
   AUDIT LOG
   ========================================================= */

export async function getAuditLogs(
  limit = 100,
): Promise<AuditLog[]> {
  const { data } =
    await api.get<AuditLog[]>(
      "/audit",
      {
        params: {
          limit,
        },
      },
    );

  return data;
}

/* =========================================================
   AI SECURITY ANALYSIS
   ========================================================= */

export async function analyzeFinding(
  findingId: number,
): Promise<AIAnalysis> {
  const { data } =
    await api.get<AIAnalysis>(
      `/ai/unified-analysis/${findingId}`,
    );

  return data;
}