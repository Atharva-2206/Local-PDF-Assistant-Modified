# backend/vectorstore_manager.py
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from .config import settings

def create_vector_store_from_text(text: str) -> FAISS | None:
    """
    Creates and returns an in-memory FAISS vector store from text.
    """
    if not text or not text.strip():
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, 
        chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_text(text)

    if not chunks:
        return None

    # Initialize without the unsupported timeout argument
    embeddings = OllamaEmbeddings(model=settings.embeddings_model)
    
    print(f"--- Creating embeddings for {len(chunks)} chunks... ---")
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    print("--- Finished creating embeddings. ---")
    
    return vector_store

def load_vector_store(file_id: str):
    """
    Loads a FAISS vector store from the local disk.
    """
    db_path = settings.db_dir / file_id
    if not db_path.exists():
        raise FileNotFoundError(f"Vector store not found for file_id: {file_id}")

    # Initialize without the unsupported timeout argument
    embeddings = OllamaEmbeddings(model=settings.embeddings_model)
    
    vector_store = FAISS.load_local(
        str(db_path), 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    return vector_store