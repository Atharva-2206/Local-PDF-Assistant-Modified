import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from .config import settings

def create_and_save_vector_store(text: str, file_id: str):
    """
    Creates a vector store from text, then saves it locally.
    This function contains the logic from your original create_vector_store function.
    """
    # Ensure the database directory exists
    os.makedirs(settings.db_dir, exist_ok=True)
    
    # 1. Split the text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, 
        chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_text(text)
    
    # 2. Initialize embeddings model
    embeddings = OllamaEmbeddings(model=settings.embeddings_model)
    
    # 3. Create FAISS vector store from text chunks
    try:
        vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    except Exception as e:
        raise Exception(f"Failed to create FAISS vector store: {e}") from e

    # 4. Save the vector store locally
    save_path = os.path.join(settings.db_dir, file_id)
    vector_store.save_local(save_path)
    
    return file_id

# Add this new function to backend/vectorstore_manager.py

def load_vector_store(file_id: str):
    """
    Loads a FAISS vector store from the local disk.
    """
    db_path = os.path.join(settings.db_dir, file_id)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Vector store not found for file_id: {file_id}")

    embeddings = OllamaEmbeddings(model=settings.embeddings_model)
    vector_store = FAISS.load_local(
        db_path, 
        embeddings, 
        allow_dangerous_deserialization=True # This is needed to load FAISS indexes
    )
    return vector_store