from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from backend import file_processor, vectorstore_manager
import uuid

router = APIRouter()

class ProcessResponse(BaseModel):
    transaction_id: str
    filenames: List[str]
    message: str

@router.post("/process/", response_model=ProcessResponse)
def process_files_endpoint(files: List[UploadFile] = File(...)):
    """
    Endpoint to process one or more uploaded files (.pdf, .docx, .txt).
    Combines text from all files into a single knowledge base.
    """
    combined_text = ""
    processed_filenames = []
    
    for file in files:
        try:
            # Step 1: Extract text from each file
            combined_text += file_processor.get_text_from_file(file) + "\n\n"
            processed_filenames.append(file.filename)
        except ValueError as e:
            # Handle unsupported file types
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Handle other processing errors
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {e}")

    if not combined_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted from the provided files.")

    # Step 2: Create a single vector store for the combined text
    try:
        # We generate one transaction_id for the whole batch
        transaction_id = str(uuid.uuid4())
        vectorstore_manager.create_and_save_vector_store(combined_text, transaction_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector store: {e}")

    return ProcessResponse(
        transaction_id=transaction_id,
        filenames=processed_filenames,
        message=f"Successfully processed and combined {len(processed_filenames)} files."
    )