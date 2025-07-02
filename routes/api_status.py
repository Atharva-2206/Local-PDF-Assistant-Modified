# routes/api_status.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend import job_manager
from typing import Any # Import the 'Any' type

router = APIRouter()

class JobStatusResponse(BaseModel):
    status: str
    # --- THIS IS THE FIX ---
    # Allow the 'details' field to be any type (string or dictionary)
    details: Any | None = None 

@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    """Endpoint to check the status of a processing job."""
    status_info = job_manager.get_job_status(job_id)
    if status_info["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(**status_info)