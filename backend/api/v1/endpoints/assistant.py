import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.v1.endpoints.predictions import get_assistant_service
from backend.rag.assistant import AIAssistantService
from backend.rag.schema import RAGResponse

router = APIRouter()
logger = logging.getLogger("api.assistant")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The message query for the RAG assistant.")
    k: int = Field(default=3, ge=1, le=10, description="Number of document chunks to retrieve.")


@router.post("/chat", response_model=RAGResponse)
async def chat_with_assistant(
    payload: ChatRequest,
    service: AIAssistantService = Depends(get_assistant_service)
) -> RAGResponse:
    """
    Submits a user query to the RAG pipeline, searches the geological knowledge base,
    and returns a synthesized answer with citations.
    """
    logger.info(f"Received RAG assistant chat request: '{payload.message}'.")
    try:
        # RAG query runs directly against the pipeline
        response = await service.rag_pipeline.query(payload.message, k=payload.k)
        return response
    except Exception as e:
        logger.error(f"RAG assistant query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot failed to retrieve or generate answer: {str(e)}"
        ) from e
