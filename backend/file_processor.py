# backend/file_processor.py
import os
import io
import zipfile
import traceback
import shutil
from pathlib import Path
import time
import uuid

# Import necessary libraries and modules
import fitz, docx, pandas as pd
from . import vectorstore_manager, job_manager
from .config import settings

# --- Text Extraction Helper Functions (These remain the same) ---
def _extract_text_from_pdf(file_path: Path) -> str:
    try:
        with fitz.open(file_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        print(f"ERROR processing PDF {file_path.name}: {e}")
        return ""

# ... (add your other _extract... functions here: docx, txt, csv, xlsx, etc.)
def _extract_text_from_docx(file_path: Path) -> str:
    doc = docx.Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)

def _extract_text_from_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors='ignore')

def _extract_text_from_csv(file_path: Path) -> str:
    return pd.read_csv(file_path).to_string()

def _extract_text_from_xlsx(file_path: Path) -> str:
    xls, full_text = pd.ExcelFile(file_path), ""
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        full_text += f"--- Sheet: {sheet_name} ---\n{df.to_string()}\n\n"
    return full_text

# --- New Multi-Document Background Task Logic ---
# In backend/file_processor.py, replace the run_processing_job function

def run_processing_job(job_id: str, job_dir_str: str):
    job_path = Path(job_dir_str)
    try:
        job_manager.update_job_status(job_id, "processing", "Starting file analysis...")
        time.sleep(1)

        files_to_process = [p for p in job_path.glob("**/*") if p.is_file() and not p.name.startswith('._') and p.name != '.DS_Store']
        
        if not files_to_process:
            raise ValueError("No files were found in the uploaded archive to process.")

        processed_files_info = []
        in_memory_stores = []

        for i, file_path in enumerate(files_to_process):
            filename = file_path.name
            job_manager.update_job_status(job_id, "processing", f"Processing file {i+1}/{len(files_to_process)}: {filename}")
            
            ext = file_path.suffix.lower()
            text = ""
            
            if ext == ".pdf": text = _extract_text_from_pdf(file_path)
            elif ext == ".docx": text = _extract_text_from_docx(file_path)
            # ... all your other file type handlers ...
            else:
                print(f"DEBUG: Skipping unsupported file type: {filename}")
                continue
            
            if text and text.strip():
                individual_store = vectorstore_manager.create_vector_store_from_text(text)
                if individual_store:
                    individual_id = str(uuid.uuid4())
                    individual_store.save_local(str(settings.db_dir / individual_id))
                    processed_files_info.append({"filename": filename, "transaction_id": individual_id})
                    in_memory_stores.append(individual_store)
        
        if not in_memory_stores:
            raise ValueError("No usable text could be extracted from any of the provided files.")

        job_manager.update_job_status(job_id, "processing", "Merging knowledge bases...")
        master_store = in_memory_stores[0]
        if len(in_memory_stores) > 1:
            master_store.merge_from(in_memory_stores[1:])
        
        master_id = str(uuid.uuid4())
        master_store.save_local(str(settings.db_dir / master_id))

        final_result = { "master_id": master_id, "files": processed_files_info }
        job_manager.update_job_status(job_id, "complete", final_result)

    except Exception as e:
        # --- THIS IS THE NEW, MORE AGGRESSIVE ERROR HANDLING ---
        print("--- BACKGROUND TASK FAILED ---")
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION DETAILS: {e}")
        
        tb_str = traceback.format_exc()
        job_manager.update_job_status(job_id, "failed", f"An error occurred: {e}\n\n{tb_str}")
        
        # Re-raise the exception to ensure it's logged by the main server process
        raise
        # ----------------------------------------------------
    finally:
        # The finally block will still run even with the 'raise'
        if job_path.exists():
            shutil.rmtree(job_path)