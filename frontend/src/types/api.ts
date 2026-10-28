export type AssetType = "Domain" | "Host" | "Service" | "DNS" | "TLS";

export interface AssetItem {
  id: string;
  type: AssetType;
  name: string;
  address: string;
  status: string;
  last_seen: string;
  details: string;
  scope_id: number;
}

export interface AssetSummary {
  domains: number;
  hosts: number;
  services: number;
  dns_records: number;
  tls_certificates: number;
}

export interface DashboardSummary {
  scope_count: number;
  assets: AssetSummary;
  open_findings: number;
  high_priority_findings: number;
  recent_changes: number;
  last_scan_at: string | null;
  scheduler: { running: boolean; job_count: number };
  recent_events: Array<{
    type: "finding" | "change";
    id: number;
    title: string;
    asset_identifier: string;
    severity: string;
    timestamp: string;
  }>;
}

export interface Scope {
  id: number;
  name: string;
  domain: string;
  allowed_ports: string | null;
  allowed_checks: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Change {
  id: number;
  snapshot_id: number;
  asset_type: string;
  asset_identifier: string;
  change_type: string;
  previous_state: string | null;
  current_state: string | null;
  detected_at: string;
}

export interface Finding {
  id: number;
  change_id: number | null;
  asset_identifier: string;
  finding_type: string;
  severity: string;
  title: string;
  description: string | null;
  status: string;
  false_positive: boolean;
  false_positive_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: number;
  evidence_type: string;
  evidence_data: string;
  collected_at: string;
}

export interface FindingDetail extends Finding {
  evidence: Evidence[];
}

export interface SchedulerStatus {
  running: boolean;
  jobs: Array<{ id: string; next_run_time: string | null }>;
}

export interface MonitoringResult {
  status: string;
  domain: string;
  scope_id: number;
  snapshot_id: number;
  collected_at: string | null;
  live_inventory: {
    ip_address: string | null;
    dns_records: Array<Record<string, unknown>>;
    tls_certificate: Record<string, unknown> | null;
    services: Array<Record<string, unknown>>;
    open_service_count: number;
  };
  change_detection: {
    status: string;
    domain: string;
    previous_snapshot_id?: number;
    current_snapshot_id?: number;
    change_count?: number;
    changes: Change[];
  };
  findings_created: Array<{
    id: number;
    finding_type: string;
    severity: string;
    title: string;
    asset_identifier: string;
  }>;
}

export interface SecurityReport {
  generated_at: string;
  period_days: number;
  scope_id: number | null;
  summary: {
    active_scopes: number;
    snapshots: number;
    changes: number;
    findings: number;
    open_findings: number;
    false_positives: number;
    evidence_records: number;
  };
  severity_counts: Record<string, number>;
  finding_type_counts: Record<string, number>;
  change_type_counts: Record<string, number>;
  recent_changes: Change[];
  recent_findings: Finding[];
}

export interface AuditLog {
  id: number;
  action: string;
  target: string | null;
  actor: string | null;
  details: string | null;
  created_at: string;
}

export interface AIAnalysis {
  finding_id: number;
  ai_status: string;
  ai_analysis: string;
  threat_intelligence: {
    virustotal: Record<string, unknown> | null;
    abuseipdb: Record<string, unknown> | null;
  };
}
