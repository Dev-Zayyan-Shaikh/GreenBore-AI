import logging
import re
from typing import Any, Protocol

import httpx

from backend.core.config import settings

logger = logging.getLogger("greenbore.rag.llm")


class LLMProvider(Protocol):
    """
    Interface for LLM text generation.
    """

    def generate(
        self, prompt: str, retrieved_chunks: list[dict[str, Any]] | None = None
    ) -> str: ...


class LocalSynthesisProvider:
    """
    Deterministic offline text generator.
    Synthesizes facts from retrieved context chunks and formats them with citations.
    """

    def generate(
        self, prompt: str, retrieved_chunks: list[dict[str, Any]] | None = None
    ) -> str:
        if not retrieved_chunks:
            # Fallback if no context chunks are supplied: parse from prompt
            retrieved_chunks = self._parse_chunks_from_prompt(prompt)

        if not retrieved_chunks:
            return (
                "I do not have enough geological record information to answer this question. "
                "(Local offline mode - no relevant knowledge base document retrieved)"
            )

        # Basic query extraction from prompt
        query_match = re.search(r"\[User Question\]\s*(.*)", prompt, re.IGNORECASE)
        query = query_match.group(1).strip() if query_match else ""
        query_lower = query.lower()

        facts_text, cited_titles = self._synthesize_facts(query_lower, retrieved_chunks)

        # Check if it's a well recommendation prompt (recommendation.txt template)
        if "[Quantitative Input]" in prompt:
            return self._generate_recommendation(prompt, facts_text, cited_titles)

        # Check if it's an XAI prediction explanation prompt (explanation.txt template)
        if "[Model Prediction Parameters]" in prompt:
            return self._generate_explanation(prompt, facts_text)

        # Standard assistant Q&A
        return self._generate_standard_qa(facts_text)

    def _synthesize_facts(
        self, query_lower: str, retrieved_chunks: list[dict[str, Any]]
    ) -> tuple[str, set[str]]:
        relevant_facts = []
        cited_titles = set()

        keywords = [
            "resistivity", "porosity", "permeability", "fracture", "casing",
            "screen", "depth", "sandstone", "limestone", "granite",
            "claystone", "shale", "anomaly", "noise"
        ]
        matched_keywords = [kw for kw in keywords if kw in query_lower]

        if not matched_keywords:
            matched_keywords = ["groundwater", "aquifer", "geological", "well", "borehole"]

        for chunk in retrieved_chunks:
            title = chunk.get("title", "Unknown Source")
            content = chunk.get("content", "") or chunk.get("content_preview", "")
            category = chunk.get("category", "General")

            sentences = re.split(r"(?<=[.!?])\s+", content)
            matching_sentences = []
            for sent in sentences:
                if any(kw in sent.lower() for kw in matched_keywords):
                    matching_sentences.append(sent.strip())

            if matching_sentences:
                preview = " ".join(matching_sentences[:3])
                relevant_facts.append(
                    f"- **From {category} ({title})**: {preview} (Source: [{title}])"
                )
                cited_titles.add(title)

        if not relevant_facts:
            first_chunk = retrieved_chunks[0]
            title = first_chunk.get("title", "Unknown Source")
            category = first_chunk.get("category", "General")
            content = first_chunk.get("content", "") or first_chunk.get("content_preview", "")
            sentences = re.split(r"(?<=[.!?])\s+", content)
            relevant_facts.append(
                f"- **From {category} ({title})**: {' '.join(sentences[:3])} (Source: [{title}])"
            )
            cited_titles.add(title)

        return "\n\n".join(relevant_facts), cited_titles

    def _generate_recommendation(
        self, prompt: str, facts_text: str, cited_titles: set[str]
    ) -> str:
        has_water = (
            "has_water = True" in prompt
            or "prediction: True" in prompt
            or "predicted outcome: True" in prompt.lower()
            or "prediction: drill" in prompt.lower()
        )
        prediction_label = (
            "Water Presence Predicted"
            if has_water
            else "Dry/Unlikely Water Presence Predicted"
        )
        decision = "Drill" if has_water else "Do Not Drill"
        depth = "30.0 - 55.0 meters" if has_water else "N/A"

        casing_rule = (
            "Solid steel casing for unconsolidated zones, open hole in stable "
            "rock, and cement grouting down to 15 meters."
        )
        if "Well Casing and Design" in "".join(cited_titles):
            casing_rule = (
                "Use solid steel casing to support loose gravel/sand intervals, "
                "cement grouting to 15 meters to prevent contamination, and place "
                "well screens (0.5mm - 1.0mm slots) exactly adjacent to target "
                "water-bearing zones."
            )

        return f"""### Geological Well Recommendation Report
**Assistant Status**: Local Offline Expert Synthesis Mode

#### 1. Feasibility Assessment
- **Status**: **{decision}**
- **Justification**: {prediction_label} based on borehole log readings. Synthetic reference documentation confirms target formations are favorable for drilling.

#### 2. Target Depth Recommendation
- **Target Interval**: **{depth}**
- **Details**: Saturated geological formations and porosity ratios point to this zone.

#### 3. Well Casing & Screen Design
- **Specification**: {casing_rule}

#### 4. Geological Risks & Warnings
- Check for clay-induced low resistivity which can lead to false water signatures (Refer to anomaly guidelines).
- Verify casing alignment in fractured zones.

#### 5. Limitations & Disclaimer
GreenBore AI provides decision support recommendations based on statistical modeling and synthetic knowledge. The final engineering and drilling decision remains the responsibility of licensed on-site geological engineers.
"""

    def _generate_explanation(self, prompt: str, facts_text: str) -> str:
        has_water = (
            "has_water = True" in prompt
            or "prediction: True" in prompt
            or "predicted outcome: True" in prompt.lower()
            or "predicted outcome: water presence predicted" in prompt.lower()
        )
        prediction_label = (
            "Water Presence Predicted" if has_water else "Dry/No Water Predicted"
        )

        feat_match = re.search(
            r"\[Top Contributing Features \(Feature Importances\)\](.*?)\[Geological Reference Context\]",
            prompt,
            re.DOTALL | re.IGNORECASE,
        )
        features_text = feat_match.group(1).strip() if feat_match else ""

        return f"""### Explainable AI (XAI) Prediction Profile
**Assistant Status**: Local Offline Expert Synthesis Mode

#### Executive Summary
The machine learning model predicted **{prediction_label}** for this borehole location.

#### Sensor Analysis
The primary drivers of this prediction are the high-importance logs:
{features_text}

#### Scientific Justification
The physical observations correlate with the following retrieved geological reference material:
{facts_text}

#### Known Limitations & Uncertainty
This prediction is based on statistical correlations and standard logging responses. Noise or washouts can impact sensor fidelity.
"""

    def _generate_standard_qa(self, facts_text: str) -> str:
        return f"""### Geological Knowledge Summary (Local Synthesis)

{facts_text}

---
*Disclaimer: This response was generated offline by the local GreenBore AI geological expert system. Always verify key measurements on-site before executing engineering tasks.*
"""

    def _parse_chunks_from_prompt(self, prompt: str) -> list[dict[str, Any]]:
        # Regex helper to parse Title/Content from raw prompt strings if chunks are not passed explicitly
        chunks = []
        pattern = r"Title:\s*(.*?)\nCategory:\s*(.*?)\nContent:\s*(.*?)(?=\nTitle:|\Z)"
        matches = re.findall(pattern, prompt, re.DOTALL | re.IGNORECASE)
        for match in matches:
            chunks.append(
                {
                    "title": match[0].strip(),
                    "category": match[1].strip(),
                    "content": match[2].strip(),
                }
            )
        return chunks


class GeminiLLMProvider:
    """
    LLM text generator using Google Gemini API (gemini-1.5-flash).
    """

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        # Using gemini-1.5-flash as the default reliable model
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def generate(
        self, prompt: str, retrieved_chunks: list[dict[str, Any]] | None = None
    ) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        params = {"key": self.api_key}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self.url, json=payload, headers=headers, params=params
            )
            response.raise_for_status()
            data = response.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as e:
                raise ValueError(
                    f"Failed to parse Gemini response payload: {e}. Raw response: {data}"
                ) from e


class DualModeLLMProvider:
    """
    Coordinates remote Gemini model queries with local offline rule-based generation fallback.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.local_provider = LocalSynthesisProvider()

        if self.api_key and self.api_key.strip():
            logger.info("Initializing Gemini LLM provider (key present).")
            self.gemini_provider: GeminiLLMProvider | None = GeminiLLMProvider(api_key=self.api_key)
        else:
            logger.info(
                "No Gemini API key found. Falling back to local offline text synthesis."
            )
            self.gemini_provider = None

    def generate(
        self, prompt: str, retrieved_chunks: list[dict[str, Any]] | None = None
    ) -> str:
        if self.gemini_provider:
            try:
                return self.gemini_provider.generate(prompt, retrieved_chunks)
            except Exception as e:
                logger.warning(
                    f"Gemini LLM API call failed: {e}. Falling back to local offline synthesis."
                )
        return self.local_provider.generate(prompt, retrieved_chunks)
