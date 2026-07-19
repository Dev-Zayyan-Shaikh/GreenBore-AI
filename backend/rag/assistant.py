import logging
from typing import Any, Literal

from backend.ml.inference import InferenceService
from backend.ml.registry import ModelRegistry
from backend.ml.schema import PredictRequest
from backend.rag.pipeline import RAGPipeline
from backend.rag.schema import (
    Citation,
    DrillingRecommendationResponse,
    FeatureContribution,
    XAIExplanationResponse,
)

logger = logging.getLogger("greenbore.rag.assistant")


class AIAssistantService:
    """
    Coordinates machine learning predictions, explainable AI (XAI) feature analysis,
    geological knowledge retrieval, and decision recommendation reports.
    """

    def __init__(
        self, rag_pipeline: RAGPipeline, registry_dir: str = "datasets/model_registry"
    ) -> None:
        self.rag_pipeline = rag_pipeline
        self.inference_service = InferenceService(registry_dir)
        self.model_registry = ModelRegistry(registry_dir)

    def _load_model_metadata(
        self, model_id: str | None
    ) -> tuple[Any, list[str], str, int, str]:
        if model_id:
            model_obj, _, features = self.model_registry.load_model(model_id)
            metadata_list = self.model_registry.get_all_metadata()
            meta_record = next(
                (m for m in metadata_list if m["model_id"] == model_id), None
            )
            model_version = meta_record.get("version", 1) if meta_record else 1
            model_type = (
                meta_record.get("model_type", "RandomForest")
                if meta_record
                else "RandomForest"
            )
        else:
            model_obj, _, prod_meta = self.model_registry.load_production_model()
            features = prod_meta.features
            model_id = prod_meta.model_id
            model_version = prod_meta.version
            model_type = prod_meta.model_type

        return model_obj, features, model_id, model_version, model_type

    def _calculate_feature_contributions(
        self, request: PredictRequest, model_obj: Any, features: list[str]
    ) -> list[FeatureContribution]:
        feature_importances = getattr(model_obj, "feature_importances_", None)
        contributions = []

        if feature_importances is not None:
            for feat, importance in zip(features, feature_importances, strict=True):
                val = getattr(request, feat, 0.0)
                contributions.append(
                    FeatureContribution(
                        feature_name=feat,
                        value=float(val),
                        importance=float(importance),
                    )
                )
            contributions.sort(key=lambda x: x.importance, reverse=True)
        else:
            for feat in features:
                val = getattr(request, feat, 0.0)
                contributions.append(
                    FeatureContribution(
                        feature_name=feat,
                        value=float(val),
                        importance=1.0 / len(features),
                    )
                )
        return contributions

    async def explain_prediction(
        self,
        sensor_data: dict[str, Any] | PredictRequest,
        model_id: str | None = None,
    ) -> XAIExplanationResponse:
        """
        Runs ML inference, performs feature importance attribution,
        retrieves matching scientific context, and generates a detailed explanation.
        """
        logger.info("Generating explainable AI (XAI) prediction profile.")

        if isinstance(sensor_data, dict):
            request = PredictRequest(**sensor_data)
        else:
            request = sensor_data

        pred_response = self.inference_service.predict(request)
        prediction = pred_response.prediction
        probability = pred_response.confidence

        model_obj, features, model_id, model_version, model_type = (
            self._load_model_metadata(model_id)
        )
        contributions = self._calculate_feature_contributions(
            request, model_obj, features
        )

        top_features = [c.feature_name for c in contributions[:3]]
        query_str = " ".join(top_features) + " groundwater aquifer"
        retrieved_chunks = await self.rag_pipeline.vector_store.similarity_search(
            query_str, k=3
        )

        context_parts = []
        for chunk in retrieved_chunks:
            part = (
                f"Title: {chunk['title']}\n"
                f"Category: {chunk['category']}\n"
                f"Content: {chunk['content']}"
            )
            context_parts.append(part)
        context_str = "\n\n".join(context_parts)

        sensor_str = ""
        for feat in features:
            val = getattr(request, feat, 0.0)
            sensor_str += f"- {feat}: {val:.4f}\n"

        top_contrib_str = ""
        for c in contributions[:3]:
            top_contrib_str += f"- {c.feature_name} (Value: {c.value:.4f}, Importance Weight: {c.importance:.4f})\n"

        formatted_prompt = self.rag_pipeline.prompt_manager.format_prompt(
            "explanation.txt",
            model_type=model_type,
            model_version=str(model_version),
            prediction_label="Water Presence Predicted"
            if prediction
            else "Dry/No Water Predicted",
            prediction_val=str(prediction),
            probability_pct=f"{probability * 100:.1f}",
            sensor_readings=sensor_str,
            feature_importances=top_contrib_str,
            context=context_str,
        )

        explanation_text = self.rag_pipeline.llm_provider.generate(
            formatted_prompt, retrieved_chunks
        )

        citations = []
        seen_titles = set()
        for chunk in retrieved_chunks:
            title = chunk["title"]
            if title not in seen_titles:
                citations.append(
                    Citation(
                        title=title,
                        category=chunk["category"],
                        content_preview=chunk["content"][:150].strip() + "...",
                    )
                )
                seen_titles.add(title)

        return XAIExplanationResponse(
            model_id=model_id,
            model_version=model_version,
            prediction=prediction,
            probability=probability,
            feature_contributions=contributions,
            explanation=explanation_text.strip(),
            citations=citations,
        )

    def _get_rock_type_spec(
        self, rock_type_code: int
    ) -> tuple[str, str, str, list[str]]:
        rock_layers_label = "Unknown Rock Type"
        recommended_depth = "35.0 - 55.0 meters"
        casing_design = "Standard steel casing with fine slot screens."
        warnings = []

        if rock_type_code == 1:
            rock_layers_label = "Sandstone Formation (Highly Permeable)"
            recommended_depth = "25.0 - 45.0 meters"
            casing_design = (
                "Threaded PVC well casing with 0.75 mm screen slots, gravel pack, "
                "and 15m sanitary cement grout seal."
            )
        elif rock_type_code == 2:
            rock_layers_label = "Limestone Formation (Fracture/Secondary Porosity)"
            recommended_depth = "50.0 - 85.0 meters"
            casing_design = (
                "Steel surface casing down to 15 meters with cement grout seal; "
                "open hole completion through stable limestone target aquifer."
            )
        elif rock_type_code == 4:
            rock_layers_label = "Granite Crystalline Bedrock"
            recommended_depth = "70.0 - 110.0 meters"
            casing_design = (
                "Heavy steel casing through loose overburden; open-hole completion "
                "in hard granite, with screens aligned to water-filled fractures."
            )
        elif rock_type_code in [0, 3]:
            rock_layers_label = "Claystone / Shale (Aquitard)"
            recommended_depth = "N/A - Confining layer"
            casing_design = (
                "Solid casing required through this zone to seal off clay/shale mud "
                "intrusion; do not place screens here."
            )
            warnings.append(
                "High clay content detected. Risk of well siltation and muddy water "
                "if screens are installed."
            )

        return rock_layers_label, recommended_depth, casing_design, warnings

    def _evaluate_feasibility(
        self, prediction: bool, probability: float, warnings: list[str]
    ) -> Literal["Drill", "Do Not Drill", "Investigate"]:
        if prediction:
            return "Drill"
        elif probability > 0.35:
            warnings.append(
                "Borderline probability. Verify fracture connectivity or run a local "
                "pumping test before drilling."
            )
            return "Investigate"
        else:
            return "Do Not Drill"

    async def get_recommendation(
        self,
        sensor_data: dict[str, Any] | PredictRequest,
        model_id: str | None = None,
    ) -> DrillingRecommendationResponse:
        """
        Synthesizes model predictions, sensor thresholds, and RAG context
        to generate well design and drilling recommendations.
        """
        logger.info("Assembling geological well design recommendations.")

        xai_profile = await self.explain_prediction(sensor_data, model_id)
        prediction = xai_profile.prediction
        probability = xai_profile.probability

        if isinstance(sensor_data, dict):
            request = PredictRequest(**sensor_data)
        else:
            request = sensor_data

        rock_type_code = request.rock_type_encoded
        resistivity_val = request.resistivity
        gamma_ray_val = request.gamma_ray

        rock_layers_label, recommended_depth, casing_design, warnings = (
            self._get_rock_type_spec(int(rock_type_code))
        )

        if resistivity_val < 15.0 and gamma_ray_val < 50.0:
            warnings.append(
                "Extremely low resistivity without matching clay gamma signature. "
                "Possible borehole washout anomaly."
            )
        if resistivity_val < 50.0 and int(rock_type_code) in [0, 3]:
            warnings.append(
                "Low resistivity is likely clay-induced rather than water-bearing sand."
            )

        drill_decision = self._evaluate_feasibility(
            prediction, probability, warnings
        )

        confidence = probability if prediction else (1.0 - probability)
        if len(xai_profile.citations) > 0:
            confidence += 0.1

        if warnings:
            confidence -= 0.15

        confidence = max(0.05, min(0.99, confidence))

        citations = xai_profile.citations
        limitations = [
            "Statistical predictions are based on localized log profiles and subject to measurement noise.",
            "Does not account for seasonal water table fluctuations or long-term depletion rates.",
        ]

        formatted_prompt = self.rag_pipeline.prompt_manager.format_prompt(
            "recommendation.txt",
            prediction_label="Water Presence Predicted"
            if prediction
            else "Dry/No Water Predicted",
            confidence_score=f"{confidence:.2f}",
            rock_layers=rock_layers_label,
            anomalies="; ".join(warnings) if warnings else "None detected",
            context="\n\n".join(
                [f"Title: {c.title}\nContent: {c.content_preview}" for c in citations]
            ),
        )

        recommendation_report = self.rag_pipeline.llm_provider.generate(
            formatted_prompt, [c.model_dump() for c in citations]
        )

        return DrillingRecommendationResponse(
            drill_decision=drill_decision,
            recommended_depth=recommended_depth,
            casing_design=casing_design,
            confidence_score=confidence,
            evidence_citations=citations,
            warnings=warnings,
            limitations=limitations,
            report=recommendation_report,
        )
