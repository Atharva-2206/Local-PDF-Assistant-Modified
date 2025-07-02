# backend/chat_engine.py
from langchain.chains import ConversationalRetrievalChain
from langchain_ollama import OllamaLLM  # Use the new OllamaLLM class
from typing import List, Tuple
from .config import settings
from . import vectorstore_manager

def get_conversational_response(query: str, txn_id: str, chat_history: List[Tuple[str, str]]) -> str:
    """
    Generates a conversational response, remembering past interactions.
    """
    try:
        vector_store = vectorstore_manager.load_vector_store(txn_id)
    except FileNotFoundError:
        return "Error: The specified transaction ID does not exist. Please process the document(s) first."
    
    # Use the new, correct class name: OllamaLLM
    llm = OllamaLLM(model=settings.llm_model)
    
    retriever = vector_store.as_retriever()
    
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=False
    )
    
    result = qa_chain.invoke({
        "question": query,
        "chat_history": chat_history
    })
    
    return result["answer"]