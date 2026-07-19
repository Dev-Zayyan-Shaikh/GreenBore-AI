import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.ml.schema import PredictRequest, PredictResponse
from backend.prompts.manager import PromptManager
from backend.rag.assistant import AIAssistantService
from backend.rag.embeddings import DualModeEmbeddingProvider
from backend.rag.llm import DualModeLLMProvider
from backend.rag.pipeline import RAGPipeline
from backend.rag.schema import DrillingRecommendationResponse, XAIExplanationResponse
from backend.rag.vector_store import DBVectorStore

router = APIRouter()
logger = logging.getLogger("api.predictions")


async def get_assistant_service(db: AsyncSession = Depends(get_db)) -> AIAssistantService:
    """Dependency that initializes the full AI Assistant RAG/ML integration pipeline."""
    # Lithological model dimension is 768 for HashingVectorizer and text-embedding-004
    embedding_provider = DualModeEmbeddingProvider(dimension=768)
    vector_store = DBVectorStore(session=db, embedding_provider=embedding_provider)
    llm_provider = DualModeLLMProvider()
    prompt_manager = PromptManager()

    rag_pipeline = RAGPipeline(
        vector_store=vector_store,
        llm_provider=llm_provider,
        prompt_manager=prompt_manager
    )
    return AIAssistantService(rag_pipeline=rag_pipeline)


class ExplainRequest(BaseModel):
    sensor_data: PredictRequest
    model_id: str | None = None


class RecommendRequest(BaseModel):
    sensor_data: PredictRequest
    model_id: str | None = None


@router.post("/predict", response_model=PredictResponse)
async def predict_water_presence(
    payload: PredictRequest,
    model_id: str | None = None,
    service: AIAssistantService = Depends(get_assistant_service)
) -> PredictResponse:
    """
    Computes real-time water presence prediction and confidence probability using
    the active production model (or a specific model ID).
    """
    logger.info(f"Received prediction request (Model ID: {model_id}).")
    try:
        response = service.inference_service.predict(payload, model_id)
        return response
    except Exception as e:
        logger.error(f"Inference execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        ) from e


@router.post("/explain", response_model=XAIExplanationResponse)
async def explain_inference(
    payload: ExplainRequest,
    service: AIAssistantService = Depends(get_assistant_service)
) -> XAIExplanationResponse:
    """
    Computes inference, maps feature importances, and retrieves RAG research literature
    to synthesize a full geological prediction explanation profile (XAI).
    """
    logger.info(f"Generating XAI explanation profile (Model ID: {payload.model_id}).")
    try:
        response = await service.explain_prediction(payload.sensor_data, payload.model_id)
        return response
    except Exception as e:
        logger.error(f"Failed to generate prediction explanation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation synthesis failed: {str(e)}"
        ) from e


@router.post("/recommend", response_model=DrillingRecommendationResponse)
async def recommend_drilling(
    payload: RecommendRequest,
    service: AIAssistantService = Depends(get_assistant_service)
) -> DrillingRecommendationResponse:
    """
    Synthesizes model outcomes, warnings, and geological context to yield drilling feasibility,
    casing specifications, and confidence scoring reports.
    """
    logger.info(f"Generating drilling recommendations (Model ID: {payload.model_id}).")
    try:
        response = await service.get_recommendation(payload.sensor_data, payload.model_id)
        return response
    except Exception as e:
        logger.error(f"Failed to generate drilling recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation synthesis failed: {str(e)}"
        ) from e
