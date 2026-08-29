"""
Simple in-memory job tracker for long-running pipeline runs.
Not persistent across restarts, but sufficient for a hackathon deployment —
avoids any single HTTP request staying open for 2-4 minutes, which trips
proxy timeouts on every hosting platform regardless of their exact limit.
"""
import uuid
import threading
from typing import Any, Optional

_jobs: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def create_job() -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "pending", "progress": "Starting...", "result": None, "error": None}
    return job_id


def update_job(job_id: str, status: Optional[str] = None, progress: Optional[str] = None,
               result: Optional[dict] = None, error: Optional[str] = None):
    with _lock:
        if job_id not in _jobs:
            return
        if status is not None:
            _jobs[job_id]["status"] = status
        if progress is not None:
            _jobs[job_id]["progress"] = progress
        if result is not None:
            _jobs[job_id]["result"] = result
        if error is not None:
            _jobs[job_id]["error"] = error


def get_job(job_id: str) -> Optional[dict]:
    with _lock:
        return _jobs.get(job_id)