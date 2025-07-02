# backend/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

# Define the absolute path to the project's root directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    llm_model: str
    embeddings_model: str
    
    # Define directories as absolute paths
    upload_dir: Path = BASE_DIR / "uploads"
    db_dir: Path = BASE_DIR / "vectorstores"
    jobs_dir: Path = BASE_DIR / "jobs"  # <-- THIS IS THE MISSING LINE

    chunk_size: int
    chunk_overlap: int

    class Config:
        env_file = ".env"

settings = Settings()