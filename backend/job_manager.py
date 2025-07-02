# backend/job_manager.py
import json
from .config import settings

def update_job_status(job_id: str, status: str, details: any = None):
    """Updates the status of a job by writing to a JSON file."""
    try:
        settings.jobs_dir.mkdir(exist_ok=True)
        status_file = settings.jobs_dir / f"{job_id}.json"
        status_data = {"status": status, "details": details}
        with open(status_file, "w") as f:
            json.dump(status_data, f)
        print(f"Job {job_id} updated to: {status}")
    except Exception as e:
        print(f"CRITICAL: Failed to update job status for {job_id}: {e}")

def get_job_status(job_id: str):
    """Retrieves the status of a job by reading from a JSON file."""
    status_file = settings.jobs_dir / f"{job_id}.json"
    if not status_file.exists():
        return {"status": "not_found", "details": "Job ID not found."}
    try:
        with open(status_file, "r") as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        return {"status": "error", "details": f"Could not read status file: {e}"}