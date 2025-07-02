# routes/api_process.py
import traceback
import uuid
import shutil
import os
import zipfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from backend import file_processor, job_manager
from backend.config import settings

router = APIRouter()

class ProcessResponse(BaseModel):
    job_id: str
    message: str

@router.post("/process/", response_model=ProcessResponse, status_code=202)
def process_files_endpoint(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    job_id = str(uuid.uuid4())
    
    settings.jobs_dir.mkdir(exist_ok=True)
    job_dir = settings.jobs_dir / job_id
    job_dir.mkdir()
    
    saved_filenames = []
    try:
        for upload_file in files:
            file_path = job_dir / upload_file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)
            saved_filenames.append(file_path)

        for file_path in saved_filenames:
            if file_path.suffix.lower() == ".zip":
                print(f"Unpacking ZIP file: {file_path.name}")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(job_dir)
                os.remove(file_path)
        
        job_manager.update_job_status(job_id, "pending", f"Received {len(files)} file(s).")
        
        # This is the correct line, now active:
        background_tasks.add_task(file_processor.run_processing_job, job_id, str(job_dir))

        return ProcessResponse(
            job_id=job_id,
            message="File processing started in the background. Check status for progress."
        )
    except Exception:
        tb_str = traceback.format_exc()
        job_manager.update_job_status(job_id, "failed", f"Failed to start job: {tb_str}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing job:\n\n{tb_str}")