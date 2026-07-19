import pandas as pd  # type: ignore[import-untyped]
import pytest
from backend.ml import MLPipeline
from backend.prompts.manager import PromptManager
from backend.rag.assistant import AIAssistantService
from backend.rag.embeddings import DualModeEmbeddingProvider, LocalEmbeddingProvider
from backend.rag.ingester import DocumentIngester
from backend.rag.llm import DualModeLLMProvider, LocalSynthesisProvider
from backend.rag.pipeline import RAGPipeline
from backend.rag.vector_store import DBVectorStore
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_embeddings_providers() -> None:
    """Verifies that offline embedding providers generate deterministic vectors."""
    local_provider = LocalEmbeddingProvider(dimension=768)
    vec1 = local_provider.get_embedding("Groundwater resistivity measurement")
    vec2 = local_provider.get_embedding("Groundwater resistivity measurement")
    vec3 = local_provider.get_embedding("Different geological term")

    assert len(vec1) == 768
    assert vec1 == vec2
    assert vec1 != vec3

    # Test DualMode fallback with no key
    dual_provider = DualModeEmbeddingProvider(api_key="")
    vec_dual = dual_provider.get_embedding("Porosity testing sandstone")
    assert len(vec_dual) == 768


@pytest.mark.asyncio
async def test_llm_providers() -> None:
    """Verifies that LocalSynthesisProvider parses prompt context and synthesizes.

    Allows offline deterministic answer validation.
    """
    local_llm = LocalSynthesisProvider()

    # Test simple Q&A
    prompt = """
[Context]
Title: Standard Casing Manual
Category: Casing
Content: Steel well casing prevents borehole wall collapses in loose sand gravel.

[User Question]
What material is used for well casing?
"""
    retrieved = [
        {
            "title": "Standard Casing Manual",
            "category": "Casing",
            "content_preview": (
                "Steel well casing prevents borehole wall collapses in loose sand gravel."
            ),
        }
    ]

    response = local_llm.generate(prompt, retrieved)
    assert "Standard Casing Manual" in response
    assert "casing" in response.lower()

    # Test DualMode LLM fallback
    dual_llm = DualModeLLMProvider(api_key=None)
    response_dual = dual_llm.generate(prompt, retrieved)
    assert "Standard Casing Manual" in response_dual


@pytest.mark.asyncio
async def test_vector_store_and_ingestion(db_session: AsyncSession) -> None:
    """Tests document chunking, indexing, and exact nearest neighbor vector search."""
    local_embed = LocalEmbeddingProvider(dimension=768)
    vector_store = DBVectorStore(session=db_session, embedding_provider=local_embed)
    ingester = DocumentIngester(
        vector_store=vector_store, chunk_size=200, chunk_overlap=20
    )

    # Check parsing of metadata
    raw_doc = """Title: Aquifer Depth Report 2026
Author: Hydrogeological Bureau
Category: Aquifers
Status: Synthetic

The sandstone aquifer in this region lies at a depth of 35 to 55 meters.
This formation exhibits moderate porosity and high water yield.
"""
    metadata, clean_body = ingester.parse_document(raw_doc, "aquifer_report.txt")
    assert metadata["title"] == "Aquifer Depth Report 2026"
    assert metadata["author"] == "Hydrogeological Bureau"
    assert metadata["category"] == "Aquifers"
    assert "sandstone" in clean_body

    # Check ingestion
    chunks_count = ingester.chunk_text(clean_body)
    assert len(chunks_count) > 0

    # Save a test chunk directly
    await vector_store.add_document_chunk(
        title="Aquifer Depth Report 2026",
        content=(
            "The sandstone aquifer in this region lies at a depth of "
            "35 to 55 meters."
        ),
        metadata=metadata,
    )

    # Verify similarity search matches
    matches = await vector_store.similarity_search("sandstone aquifer depth", k=1)
    assert len(matches) == 1
    assert matches[0]["title"] == "Aquifer Depth Report 2026"
    assert matches[0]["score"] > 0.0


@pytest.mark.asyncio
async def test_rag_pipeline(db_session: AsyncSession) -> None:
    """Verifies that RAGPipeline successfully coordinates vector retrieval and Q&A."""
    local_embed = LocalEmbeddingProvider(dimension=768)
    vector_store = DBVectorStore(session=db_session, embedding_provider=local_embed)
    local_llm = LocalSynthesisProvider()

    # Create a temporary prompts directory structure for test
    prompts_manager = PromptManager()

    pipeline = RAGPipeline(
        vector_store=vector_store,
        llm_provider=local_llm,
        prompt_manager=prompts_manager,
    )

    # Seed document
    await vector_store.add_document_chunk(
        title="Resistivity Study",
        content=(
            "Low electrical resistivity indicates saturated fresh-water "
            "sandstone zones."
        ),
        metadata={"category": "Resistivity"},
    )

    result = await pipeline.query("How does resistivity indicate water?", k=1)
    assert result.query == "How does resistivity indicate water?"
    assert len(result.citations) == 1
    assert result.citations[0].title == "Resistivity Study"
    assert "Low electrical resistivity" in result.answer


@pytest.mark.asyncio
async def test_ai_assistant_service(
    db_session: AsyncSession, temp_registry_dir: str, synthetic_dataframe: pd.DataFrame
) -> None:
    """Tests ML-integrated Explainable AI (XAI) and decision recommendations."""
    # 1. Train and register RandomForest production model
    ml_pipeline = MLPipeline(registry_dir=temp_registry_dir, dataset_name="test_well")
    ml_pipeline.run_training_pipeline(
        df=synthetic_dataframe,
        model_type="RandomForest",
        hyperparameters={"n_estimators": 5},
        set_prod=True,
    )

    # 2. Setup RAG pipeline
    local_embed = LocalEmbeddingProvider(dimension=768)
    vector_store = DBVectorStore(session=db_session, embedding_provider=local_embed)
    local_llm = LocalSynthesisProvider()
    prompts_manager = PromptManager()
    rag_pipeline = RAGPipeline(
        vector_store=vector_store,
        llm_provider=local_llm,
        prompt_manager=prompts_manager,
    )

    # Seed well casing standards document
    await vector_store.add_document_chunk(
        title="Well Casing and Design",
        content=(
            "Use solid steel casing to support loose gravel/sand intervals, "
            "cement grouting to 15 meters to prevent contamination, and place "
            "well screens exactly adjacent to target water-bearing zones."
        ),
        metadata={"category": "Well Design"},
    )

    # 3. Instantiate Assistant
    assistant = AIAssistantService(
        rag_pipeline=rag_pipeline, registry_dir=temp_registry_dir
    )

    # 4. Perform XAI Prediction Explanation
    sensor_input = {
        "density": 2.3,
        "porosity": 0.25,
        "resistivity": 120.0,
        "gamma_ray": 40.0,
        "sonic_travel_time": 80.0,
        "density_ma5": 2.3,
        "porosity_ma5": 0.25,
        "resistivity_ma5": 120.0,
        "gamma_ray_ma5": 40.0,
        "sonic_travel_time_ma5": 80.0,
        "porosity_resistivity_ratio": 0.002,
        "density_porosity_ratio": 9.2,
        "rock_type_encoded": 1.0,  # Sandstone
    }

    xai_response = await assistant.explain_prediction(sensor_input)
    assert xai_response.model_id == "model_randomforest_v1"
    assert xai_response.model_version == 1
    assert len(xai_response.feature_contributions) > 0
    assert xai_response.explanation != ""
    assert len(xai_response.citations) >= 1

    # 5. Generate Well Recommendation Report
    rec_response = await assistant.get_recommendation(sensor_input)
    assert rec_response.drill_decision in ["Drill", "Do Not Drill", "Investigate"]
    assert rec_response.recommended_depth == "25.0 - 45.0 meters"  # Sandstone rule
    assert "sanitary cement grout seal" in rec_response.casing_design.lower()
    assert 0.0 <= rec_response.confidence_score <= 1.0
    assert len(rec_response.evidence_citations) >= 1
