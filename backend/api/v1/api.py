from fastapi import APIRouter

from backend.api.v1.endpoints import assistant, health, models, predictions, simulation

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
