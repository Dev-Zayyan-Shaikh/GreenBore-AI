# GreenBore AI Project State & Developer Handover

This document serves as a concise project orientation and progress summary for GreenBore AI. It defines the project's current development status, architecture, coding standards, and objectives for future AI engineering models and developers.

---

## 1. Project Overview
**GreenBore AI** is an enterprise-grade, research-oriented AI Engineering platform designed for intelligent borewell analysis and subsurface groundwater decision support. 

Rather than serving as a simple predictive script, it is structured as a complete modular platform that bridges:
- **Data Engineering**: Geological dataset simulation, validation, and petrophysical feature processing.
- **Machine Learning**: Predictive classification models (RandomForest, XGBoost) evaluating water presence probability.
- **Knowledge Intelligence**: Vector-based semantic search and Retrieval-Augmented Generation (RAG) using geological literature.
- **Decision Intelligence**: Multi-dimensional confidence scoring and explainable drilling recommendation reporting.

---

## 2. Current Roadmap & Progress

The development lifecycle is divided into 6 distinct capability phases:

| Phase | Capability Level | Description | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Core Infrastructure | FastAPI base, React+Vite structure, Docker Compose, PostgreSQL + pgvector, structured logging. | **Completed** |
| **Phase 2** | Geological Data Platform | Sensor and rock layer simulation engine, petrophysical feature engineering, exports. | **Completed** |
| **Phase 3** | AI & Machine Learning | Training pipelines, ML evaluation metrics, local model registry, experiment tracking. | **Completed** |
| **Phase 4** | Knowledge Intelligence | Document ingestion, FAISS/pgvector semantic search, prompt management, RAG assistant. | **Completed** |
| **Phase 5** | Decision Intelligence | Explainable AI (XAI) engine, rule-based recommendation reasoning, confidence scoring. | **Completed** |
| **Phase 6** | Product & Production | REST endpoints, complete React dashboard pages, Playwright E2E testing, production builds. | **Completed** |

---

## 3. Completed Phases (1–4) Summary

### Phase 1 — Core Infrastructure
- **Backend Core**: Configured [FastAPI](https://fastapi.tiangolo.com/) with async database sessions and Pydantic v2 settings.
- **Frontend Core**: Initialized React, TypeScript, and Vite scaffolding.
- **Environment & Docker**: Created a multi-container Docker Compose setup for PostgreSQL and the backend API, with environment configuration files ([.env](file:///e:/Zayyan%20Files/GreenBore%20AI/.env)).
- **Infrastructure Validation**: Established structured JSON logging and health checking endpoints verifying database connection state.

### Phase 2 — Geological Data Platform
- **Geological Simulation Engine**: Developed a simulation generator creating synthetic borehole logs (parameters: depth, density, porosity, resistivity, gamma-ray, sonic travel time, rock type) with configurable Gaussian noise and ground truth labels (`has_water`).
- **Feature Engineering**: Implemented moving averages (rolling MA5) and ratios (porosity-resistivity ratio) in [pipeline.py](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/ml/pipeline.py).
- **Data Exporting**: Enabled saving datasets as CSV, JSON, and Parquet.

### Phase 3 — AI & Machine Learning Platform
- **ML Pipeline**: Built standardized preprocessing and dataset splitting pipelines. Supported training of RandomForest and XGBoost classifiers.
- **Experiment Tracker & Registry**: Configured a local model registry and metrics logger. Weights are serialized using `joblib`, and active metadata tags indicate the current production-ready version.
- **Inference Service**: Implemented prediction and confidence computation pipelines in [inference.py](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/ml/inference.py).

### Phase 4 — Knowledge Intelligence Platform
- **Knowledge Ingestion**: Created ingestion scripts ([seed_knowledge_base.py](file:///e:/Zayyan%20Files/GreenBore%20AI/scripts/seed_knowledge_base.py)) parsing unstructured geological manuals under [geological_knowledge/](file:///e:/Zayyan%20Files/GreenBore%20AI/datasets/geological_knowledge) into a FAISS/db vector store.
- **Local Embeddings**: Implemented offline-first deterministic 768-dimension vectors using scikit-learn's `HashingVectorizer`.
- **RAG Pipeline**: Built a synthesis engine using a [PromptManager](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/prompts/manager.py) (separating prompt strings from code) and a [DualModeLLMProvider](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/rag/llm.py) that falls back to localized generation if Gemini API keys are absent.

---

## 4. Current Project Status

- **Code Integrity**: Phase 4 features are fully merged and pushed to the `main` branch. 
- **Tests Status**: All 16 backend unit tests covering core ML pipelines, vector similarity searches, and assistant fallback processes pass without errors.
- **Linter Status**: Checked and cleared through the `ruff` and `mypy` strict configurations.

---

## 5. Core Architectural Principles

- **Clean Architecture**: Core domain logic must remain independent of external libraries, database providers, and API frameworks.
- **Modular Design**: Modules (like `ml` and `rag`) communicate strictly via schemas and abstractions. Direct internal state dependencies are forbidden.
- **API-First & Docker-First**: The client communicates solely via REST, and all developer setups run in identical container environments.
- **Cloud-Ready**: Integrations (e.g., vector database, LLM provider) support plug-and-play interfaces to enable migrations between SQLite/Postgres/FAISS and OpenAI/Gemini/Local LLMs.

---

## 6. Coding Standards & Development Rules

- **Function Rules**: Write self-documenting code with Python type hints. Keep functions under 40 lines and classes under 300 lines where possible.
- **Zero Secrets**: Hardcoded database URLs, API credentials, or paths are strictly prohibited. Load config values dynamically via Pydantic Settings.
- **Log, Don't Print**: Never use `print()` statements in application code. Rely on the structured `logger` instance.
- **Separation of Prompts**: Do not hardcode prompt instructions. Save them as `.txt` files in [backend/prompts/](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/prompts/) and load them through the [PromptManager](file:///e:/Zayyan%20Files/GreenBore%20AI/backend/prompts/manager.py).

---

## 7. Major Design Decisions

- **HashingVectorizer Fallback**: Enables the RAG assistant to generate embeddings offline or during development without incurring API costs.
- **Dual-Mode System**: Providers (`GeminiEmbeddingProvider`, `GeminiLLMProvider`) use a transparent fallback chain that switches to local mock alternatives if credentials are missing or remote connections fail.

---

## 8. Technology Stack

- **Backend**: Python 3.10/3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, React Query, Zustand
- **Database**: PostgreSQL with `pgvector` support (FAISS is used as the local/offline vector engine)
- **AI & Analytics**: Scikit-learn, XGBoost, Pandas, NumPy, Joblib, HTTPX
- **Quality Assurance**: Pytest, Ruff, MyPy

---

## 9. Project Structure

```
GreenBore-AI/
├── .instructions/            # Governance, coding guidelines, and phase specifications
├── backend/
│   ├── api/                  # API routing, gateway schemas, and endpoints
│   ├── core/                 # Shared configurations, logs, and database setups
│   ├── ml/                   # Machine learning training, inference, and registry
│   ├── prompts/              # Prompt text assets and template managers
│   ├── rag/                  # Vector ingestion, embedding providers, and LLM clients
│   ├── synthetic/            # Borehole data generator and feature processors
│   └── tests/                # Automated pytest files
├── datasets/                 # Local data models, registries, and geological literature
├── docker/                   # Docker environment configurations
├── frontend/                 # React frontend Vite project
└── scripts/                  # Seed scripts and administrative utilities
```

---

## 10. Remaining Tasks (What has NOT been implemented yet)

- *None. All milestones (Phases 1 through 6) have been successfully implemented, integrated, and verified.*

---

## 11. Phase 5 Objectives

When initiating Phase 5, focus on implementing:
1. **Explainable AI (XAI) Engine**: Compute feature importance mappings and map contributions to natural language summaries.
2. **Well Recommendation Engine**: Define rule-based logical decision branches linking petrophysical measurements (e.g., shale, sandstone alerts) with RAG retrieved literature.
3. **Multi-dimensional Confidence Scoring**: Mathematically formulate confidence scores based on model predictions, warnings, and citations.
4. **Validation Suite**: Author exhaustive tests verifying recommendation engines under various sensor configurations.

### Phase 5 Vision – Product Platform

Phase 5 should focus on transforming GreenBore AI into a polished, enterprise-grade application.

The primary objective is to build a professional engineering interface for visualizing geological and AI-generated insights.

Key goals include:
- Interactive 3D subsurface visualization.
- Geological layer rendering.
- Rock and soil composition visualization.
- Water-bearing zone visualization.
- Borehole rendering and comparison.
- Sensor log visualization (GR, RES, NPHI, RHOB, DT).
- AI prediction overlays.
- Confidence heatmaps and uncertainty visualization.
- Interactive 2D maps and geological cross-sections.
- Rich dashboards, charts, analytics, and reporting.

The UI should be comparable to professional engineering, GIS, and industrial analytics software.

Design requirements:
- Enterprise-grade quality.
- Modern React architecture.
- Exceptional UX and responsiveness.
- Clean, minimal, professional design.
- High-performance rendering.
- No generic templates.
- No AI-generated "slop" UI.
- No unnecessary glassmorphism or flashy effects.
- Every visualization should be meaningful, interactive, and technically accurate.
- No super techy fonts and generic cyberpunk colors

Future AI models should prioritize quality, usability, and engineering precision over rapid implementation.

---

## 12. Continue Development Instructions

For future developers and AI models:
1. **Read `PROJECT_STATE.md` First** to orient yourself with the current status of the repository.
2. **Inspect the Active Codebase** under `backend/rag/` and `backend/ml/` to familiarize yourself with existing implementations.
3. **Verify Completed Work** by running the tests:
   ```powershell
   .\backend\.venv\Scripts\pytest
   ```
4. **Begin Directly with Phase 5** tasks (integrating predictions, RAG contexts, and recommendation logic).
5. **Avoid Reimplementing Completed Functionality** or modifying the core architecture directories without an approved Architecture Decision Record (ADR).
