from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    llm_model: str
    embeddings_model: str
    upload_dir: str
    db_dir: str
    chunk_size: int
    chunk_overlap: int

    class Config:
        env_file = ".env"

settings = Settings()