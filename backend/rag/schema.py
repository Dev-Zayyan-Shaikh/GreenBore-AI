from typing import Literal

from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    query: str = Field(..., description="The user's question or search query")
    k: int = Field(3, description="Number of document chunks to retrieve")


class Citation(BaseModel):
    title: str = Field(..., description="Title of the cited source document")
    category: str = Field(..., description="Category classification of the document")
    content_preview: str = Field(
        ..., description="Preview snippet of the cited content"
    )


class RAGResponse(BaseModel):
    query: str = Field(..., description="The original query")
    answer: str = Field(..., description="The generated response from RAG pipeline")
    citations: list[Citation] = Field(
        default_factory=list, description="References cited in the response"
    )


class FeatureContribution(BaseModel):
    feature_name: str = Field(..., description="Name of the sensor feature")
    value: float = Field(..., description="Actual value of the sensor feature")
    importance: float = Field(
        ..., description="Global model importance score of the feature"
    )


class XAIExplanationResponse(BaseModel):
    model_id: str = Field(..., description="The unique ID of the model used")
    model_version: int = Field(..., description="The version of the model used")
    prediction: bool = Field(..., description="The boolean outcome (has_water)")
    probability: float = Field(
        ..., description="The prediction probability (0.0 to 1.0)"
    )
    feature_contributions: list[FeatureContribution] = Field(
        ..., description="Analysis of individual features"
    )
    explanation: str = Field(
        ...,
        description=(
            "Detailed markdown explanation correlating findings with documentation"
        ),
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Geological references cited in the explanation",
    )


class DrillingRecommendationResponse(BaseModel):
    drill_decision: Literal["Drill", "Do Not Drill", "Investigate"] = Field(
        ..., description="The high-level action recommendation"
    )
    recommended_depth: str = Field(
        ..., description="The target depth interval (e.g. '15.0 - 25.0 meters')"
    )
    casing_design: str = Field(
        ..., description="Recommended casing, screen placements, and gravel packing"
    )
    confidence_score: float = Field(
        ..., description="Overall confidence score (0.0 to 1.0)"
    )
    evidence_citations: list[Citation] = Field(
        default_factory=list, description="Citations supporting the decision"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Identified hazards or sensor anomalies"
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Model limits and statistical uncertainties",
    )
    report: str = Field(
        ..., description="Detailed well-drilling recommendation report text"
    )
