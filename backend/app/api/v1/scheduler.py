from fastapi import APIRouter, HTTPException

from app.services.scheduler_service import (
    run_scheduled_inventory,
    scheduler,
    start_scheduler,
    stop_scheduler,
)


router = APIRouter(prefix="/scheduler", tags=["Scheduled Monitoring"])


@router.get("/status")
def scheduler_status():
    jobs = [
        {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
    return {"running": scheduler.running, "jobs": jobs}


def _status_payload(status: str):
    jobs = [
        {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
    return {
        "status": status,
        "running": scheduler.running,
        "jobs": jobs,
    }


@router.post("/start")
def start_monitoring():
    start_scheduler()
    return _status_payload("started")


@router.post("/stop")
def stop_monitoring():
    stop_scheduler()
    return _status_payload("stopped")


@router.post("/run/{domain}")
def run_monitoring_now(domain: str):
    try:
        return run_scheduled_inventory(domain)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {exc}") from exc


@router.post("/live/{domain}")
def run_live_monitoring(domain: str):
    """Run one fresh authorized collection cycle immediately."""
    try:
        return run_scheduled_inventory(domain)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Live monitoring failed: {exc}") from exc
