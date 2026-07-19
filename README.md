# GreenBore AI: Subsurface Exploration & Groundwater Decision Support Platform

GreenBore AI is a production-ready, research-oriented AI Engineering suite designed for deep well logging analysis, subsurface geological modeling, and intelligent groundwater decision support. 

The platform bridges physics-based telemetry logs simulation, machine learning (ML) classification models (RandomForest and XGBoost), and Retrieval-Augmented Generation (RAG) semantic search pipelines over geological literature to yield comprehensive drilling recommendations with explainable AI (XAI) justifications.

---

## 🚀 Key Features

1. **Interactive 3D Subsurface Column (WebGL)**
   * High-performance 3D rendering powered by **React Three Fiber (R3F) and ThreeJS**.
   * Translucent rock layers matching geological standards with wireframe outline grids.
   * **3D CAD Model Inspector Panel**: Interactively adjust layer opacity, vertically separate block boundaries (exploded view slider), and toggle individual structures (Strata, Wellbore, Fractures, Aquifers, AI predictions, and Coordinate Axes).
2. **Multi-Track Petrophysical Logs**
   * Viewport-scrollable, high-contrast SVG curves plotting Gamma-Ray (GR), Resistivity (RES), Porosity (NPHI), Bulk Density (RHOB), and Acoustic Sonic (DT) telemetry.
   * Real-time selection depth indicators cross-linked to the 3D block and AI explanations.
3. **Geological Logging Simulator Engine**
   * Configurable generator simulating realistic strata beds, fractures, aquifers, and Gaussian sensor noise.
   * Performs real-time feature engineering (e.g., 5-point moving averages, porosity-resistivity ratios, density-porosity ratios).
   * Supports structured dataset exports in **CSV, JSON, and Parquet** formats.
4. **Machine Learning Model Catalog & Registry**
   * Interactive training console for RandomForest and XGBoost classifiers.
   * Logs hyperparameter configurations and registers metrics (Accuracy, Precision, Recall, F1).
   * Models catalog with promotion mechanisms for tagging and serving the production-ready model.
5. **RAG Decision Co-Pilot & Chatbot**
   * Direct integration with a **self-healing PostgreSQL vector database** storing geological references.
   * Dual-mode LLM execution (remote Google Gemini API client with fallback to deterministic local rules-based synthesis).
   * Fully styled markdown chat bubbles and console block rendering for logs tables.

---

## 🏗️ System Architecture

```
                                  [ React + Vite Frontend Client ]
                                                 │
                                 (REST API calls over JSON/CORS)
                                                 │
                                                 ▼
                                     [ FastAPI Gateway Router ]
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
       [ Geological Simulator ]          [ ML Model Center ]           [ RAG Decision Co-Pilot ]
       * Strata & Aquifer Generation     * Scikit-Learn / XGBoost      * pgvector DB Store
       * Feature Engineering Pipeline    * Joblib Local Registry       * Gemini API (gemini-flash-latest)
       * CSV/JSON/Parquet Exports        * Real-time Inference         * Dual-Mode Offline Fallbacks
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 ▼
                                     [ PostgreSQL / SQLAlchemy ]
```

---

## 🛠️ Installation & Setup

### Prerequisites
* **Python 3.10 or 3.12**
* **Node.js (v18+) & npm**
* **Docker & Docker Compose** (optional, for database containerization)

### Environment Configuration
1. Clone the repository and navigate to the project root.
2. Create a `.env` file at the root using the template below:

```bash
# Application Metadata
PROJECT_NAME="GreenBore AI"
ENV=development
API_V1_STR="/api/v1"

# Security & CORS
BACKEND_CORS_ORIGINS='["http://localhost", "http://localhost:5173", "http://localhost:80", "http://127.0.0.1:5173", "http://127.0.0.1:80"]'

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=greenbore
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@127.0.0.1:5432/greenbore

# Gemini API Integration
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🏃 Running the Application

### 1. Database Scaffolding
If you have Docker installed, you can spin up the PostgreSQL database container:
```bash
docker-compose -f docker/docker-compose.yml up -d
```
*Note: The FastAPI application features a self-healing lifespan hook that automatically initializes the database tables and embeds the seed geological knowledge files on first startup.*

### 2. Backend Server Setup
From the root directory:
```bash
# Navigate to the backend
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scriptsctivate` on Windows

# Install dependencies
pip install -e .

# Start the FastAPI reload server
uvicorn backend.main:app --reload
```
The API Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend Client Setup
From the root directory:
```bash
# Navigate to the frontend
cd frontend

# Install Node modules
npm install

# Run the local Vite dev server
npm run dev
```
Open your browser and navigate to [http://localhost:5173](http://localhost:5173).

---

## 🧪 Testing and Verification

To run the automated backend test suites (covering ML pipeline training, predictions, vector similarities, and offline synthesis fallbacks):

From the `backend` folder:
```bash
# Run tests
.venv/Scripts/pytest
```

---

## 🛡️ Core Development Rules

* **Abstractions First**: The core ML and RAG architectures use strict Pydantic models and SQLAlchemy schemas. 
* **Zero Hardcoded Secrets**: Load all database URLs and API keys dynamically via Pydantic settings.
* **Logger Precedence**: Always print structured events using Python's `logging` system; direct `print()` calls in endpoints are prohibited.

---
