from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Tuple
from backend import chat_engine

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    transaction_id: str
    # Add an optional field for chat history.
    # It's a list of (human_query, ai_response) tuples.
    chat_history: List[Tuple[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    response: str

@router.post("/chat/", response_model=ChatResponse)
def chat_with_doc(request: ChatRequest):
    try:
        response_text = chat_engine.get_conversational_response(
            query=request.query, 
            txn_id=request.transaction_id,
            chat_history=request.chat_history
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))