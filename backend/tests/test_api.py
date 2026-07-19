import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Verifies that the /health endpoint responds successfully."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_simulation_workflow(client: AsyncClient) -> None:
    """Tests synthetic dataset generation, listing, retrieval, and downloads."""
    # 1. POST /generate
    config_payload = {
        "total_depth": 10.0,
        "interval": 1.0,
        "layers": [
            {
                "rock_type": "Sandstone",
                "depth_start": 0.0,
                "depth_end": 5.0,
                "density": 2.2,
                "porosity": 0.25,
                "base_resistivity": 100.0,
                "base_gamma": 40.0,
                "base_sonic": 85.0
            },
            {
                "rock_type": "Limestone",
                "depth_start": 5.0,
                "depth_end": 10.0,
                "density": 2.6,
                "porosity": 0.12,
                "base_resistivity": 500.0,
                "base_gamma": 20.0,
                "base_sonic": 55.0
            }
        ],
        "fractures": [],
        "water_zones": [
            {
                "depth_start": 3.0,
                "depth_end": 7.0,
                "flow_rate": 2.5,
                "salinity": 1500.0
            }
        ],
        "noise": {
            "gamma_std": 0.0,
            "resistivity_std": 0.0,
            "porosity_std": 0.0,
            "density_std": 0.0,
            "sonic_std": 0.0
        }
    }

    response = await client.post("/api/v1/simulation/generate", json=config_payload)
    assert response.status_code == 201
    gen_data = response.json()
    assert gen_data["status"] == "success"
    assert gen_data["records_count"] == 11  # 0.0 to 10.0 inclusive is 11 steps
    dataset_name = gen_data["dataset_name"]

    # 2. GET /datasets
    response = await client.get("/api/v1/simulation/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert any(d["dataset_name"] == dataset_name for d in datasets)

    # 3. GET /datasets/{filename}
    response = await client.get(f"/api/v1/simulation/datasets/{dataset_name}")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 11

    # 4. GET /datasets/{filename}/download
    response = await client.get(f"/api/v1/simulation/datasets/{dataset_name}/download?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_models_and_inference_workflows(client: AsyncClient) -> None:
    """Verifies model training, promotion to production, and real-time XAI predictions."""
    # 1. Make sure we have a dataset to train on
    config_payload = {
        "total_depth": 10.0,
        "interval": 2.0,
        "layers": [
            {
                "rock_type": "Sandstone",
                "depth_start": 0.0,
                "depth_end": 10.0,
                "density": 2.3,
                "porosity": 0.22,
                "base_resistivity": 120.0,
                "base_gamma": 30.0,
                "base_sonic": 80.0
            }
        ]
    }
    res_gen = await client.post("/api/v1/simulation/generate", json=config_payload)
    dataset_name = res_gen.json()["dataset_name"]

    # 2. POST /models/train
    train_payload = {
        "model_type": "RandomForest",
        "hyperparameters": {"n_estimators": 3},
        "dataset_name": dataset_name,
        "set_prod": True
    }
    response = await client.post("/api/v1/models/train", json=train_payload)
    assert response.status_code == 201
    model_data = response.json()
    assert model_data["model_type"] == "RandomForest"
    assert model_data["is_production"] is True
    model_id = model_data["model_id"]

    # 3. GET /models
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    models_list = response.json()
    assert any(m["model_id"] == model_id for m in models_list)

    # 4. POST /predictions/predict
    predict_payload = {
        "density": 2.3,
        "porosity": 0.22,
        "resistivity": 120.0,
        "gamma_ray": 30.0,
        "sonic_travel_time": 80.0,
        "density_ma5": 2.3,
        "porosity_ma5": 0.22,
        "resistivity_ma5": 120.0,
        "gamma_ray_ma5": 30.0,
        "sonic_travel_time_ma5": 80.0,
        "porosity_resistivity_ratio": 0.0018,
        "density_porosity_ratio": 10.45,
        "rock_type_encoded": 1
    }
    response = await client.post(f"/api/v1/predictions/predict?model_id={model_id}", json=predict_payload)
    assert response.status_code == 200
    pred_data = response.json()
    assert pred_data["model_id"] == model_id
    assert "prediction" in pred_data
    assert "confidence" in pred_data

    # 5. POST /predictions/explain
    explain_payload = {
        "sensor_data": predict_payload,
        "model_id": model_id
    }
    response = await client.post("/api/v1/predictions/explain", json=explain_payload)
    assert response.status_code == 200
    explain_data = response.json()
    assert explain_data["model_id"] == model_id
    assert "explanation" in explain_data
    assert "citations" in explain_data

    # 6. POST /predictions/recommend
    response = await client.post("/api/v1/predictions/recommend", json=explain_payload)
    assert response.status_code == 200
    rec_data = response.json()
    assert "drill_decision" in rec_data
    assert "report" in rec_data


@pytest.mark.asyncio
async def test_assistant_chat_endpoint(client: AsyncClient) -> None:
    """Verifies that RAG chatbot assistant queries respond with geological facts."""
    chat_payload = {
        "message": "Which casing design standards should I use for a limestone aquifer?",
        "k": 2
    }
    response = await client.post("/api/v1/assistant/chat", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "citations" in data
