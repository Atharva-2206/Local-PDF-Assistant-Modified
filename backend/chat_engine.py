from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import Ollama
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
    
    llm = Ollama(model=settings.llm_model)
    retriever = vector_store.as_retriever()
    
    # Use the ConversationalRetrievalChain which is designed for chat history
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=False # Set to True if you want to see the source chunks
    )
    
    # The chain expects a dictionary with 'question' and 'chat_history' keys
    result = qa_chain.invoke({
        "question": query,
        "chat_history": chat_history
    })
    
    return result["answer"]