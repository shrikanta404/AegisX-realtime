"""Harden asset inventory schema.

Revision ID: f3b7c1d8e4a2
Revises: bd73d1bdcd0f
"""
from alembic import op
import sqlalchemy as sa


revision = "f3b7c1d8e4a2"
down_revision = "bd73d1bdcd0f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "hosts",
        "ip_address",
        existing_type=sa.String(length=100),
        nullable=True,
    )

    index_specs = [
        ("ix_domains_last_seen_at", "domains", "last_seen_at"),
        ("ix_hosts_hostname", "hosts", "hostname"),
        ("ix_hosts_last_seen_at", "hosts", "last_seen_at"),
        ("ix_dns_records_last_seen_at", "dns_records", "last_seen_at"),
        ("ix_tls_certificates_last_checked_at", "tls_certificates", "last_checked_at"),
        ("ix_services_last_seen_at", "services", "last_seen_at"),
        ("ix_inventory_snapshots_started_at", "inventory_snapshots", "started_at"),
        ("ix_inventory_snapshots_completed_at", "inventory_snapshots", "completed_at"),
        ("ix_changes_detected_at", "changes", "detected_at"),
        ("ix_findings_asset_identifier", "findings", "asset_identifier"),
        ("ix_findings_finding_type", "findings", "finding_type"),
        ("ix_findings_severity", "findings", "severity"),
        ("ix_findings_status", "findings", "status"),
        ("ix_findings_false_positive", "findings", "false_positive"),
        ("ix_findings_created_at", "findings", "created_at"),
        ("ix_evidence_finding_id", "evidence", "finding_id"),
        ("ix_evidence_collected_at", "evidence", "collected_at"),
        ("ix_audit_logs_action", "audit_logs", "action"),
        ("ix_audit_logs_created_at", "audit_logs", "created_at"),
    ]
    for name, table, column in index_specs:
        op.create_index(name, table, [column], unique=False)


def downgrade() -> None:
    index_specs = [
        ("ix_audit_logs_created_at", "audit_logs"),
        ("ix_audit_logs_action", "audit_logs"),
        ("ix_evidence_collected_at", "evidence"),
        ("ix_evidence_finding_id", "evidence"),
        ("ix_findings_created_at", "findings"),
        ("ix_findings_false_positive", "findings"),
        ("ix_findings_status", "findings"),
        ("ix_findings_severity", "findings"),
        ("ix_findings_finding_type", "findings"),
        ("ix_findings_asset_identifier", "findings"),
        ("ix_changes_detected_at", "changes"),
        ("ix_inventory_snapshots_completed_at", "inventory_snapshots"),
        ("ix_inventory_snapshots_started_at", "inventory_snapshots"),
        ("ix_services_last_seen_at", "services"),
        ("ix_tls_certificates_last_checked_at", "tls_certificates"),
        ("ix_dns_records_last_seen_at", "dns_records"),
        ("ix_hosts_last_seen_at", "hosts"),
        ("ix_hosts_hostname", "hosts"),
        ("ix_domains_last_seen_at", "domains"),
    ]
    for name, table in index_specs:
        op.drop_index(name, table_name=table)

    op.alter_column(
        "hosts",
        "ip_address",
        existing_type=sa.String(length=100),
        nullable=False,
    )
