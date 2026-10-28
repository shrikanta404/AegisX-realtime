from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.scope import AuthorizedScope
from app.services.monitoring_service import MonitoringService


scheduler = BackgroundScheduler(timezone="UTC")


def monitor_authorized_scopes() -> None:
    db = SessionLocal()
    try:
        scopes = db.scalars(
            select(AuthorizedScope).where(AuthorizedScope.is_active.is_(True))
        ).all()

        for scope in scopes:
            try:
                result = MonitoringService(db).run(scope.domain, actor="scheduler")
                finding_count = len(result.get("findings_created", []))
                change_count = result.get("change_detection", {}).get("change_count", 0)
                print(
                    f"[SCHEDULER] {scope.domain}: "
                    f"snapshot={result.get('snapshot_id')} "
                    f"changes={change_count} findings={finding_count}"
                )
            except PermissionError as exc:
                print(f"[SCHEDULER] Scope blocked: {scope.domain}: {exc}")
            except Exception as exc:
                print(f"[SCHEDULER] Monitoring failed for {scope.domain}: {exc}")
    finally:
        db.close()


def run_scheduled_inventory(domain: str):
    db = SessionLocal()
    try:
        return MonitoringService(db).run(domain, actor="manual")
    finally:
        db.close()


def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        print("[SCHEDULER] Scheduler disabled by configuration.")
        return
    if scheduler.running:
        return

    interval = settings.effective_scheduler_interval_seconds
    scheduler.add_job(
        monitor_authorized_scopes,
        "interval",
        seconds=interval,
        id="authorized-scope-monitor",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    print(f"[SCHEDULER] Started. Interval={interval} second(s).")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[SCHEDULER] Stopped.")
