import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
import pytest_asyncio
from backend.core.database import Base, get_db
from backend.main import app
from backend.synthetic import GeologicalSimulator, LayerConfig, SimulationConfig
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# In-memory async SQLite URL for unit testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Creates a session-scoped event loop for async tests.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[Any, None]:  # type: ignore[name-defined]
    engine = create_async_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        # Import models to register them on Base metadata
        from backend.rag.models import DocumentChunkModel  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:  # type: ignore[name-defined]
    AsyncSessionLocal = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Wrap standard app in httpx AsyncClient transport
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def temp_registry_dir() -> Generator[str, None, None]:
    """Creates a temporary directory for isolated model registry testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def synthetic_dataframe() -> pd.DataFrame:
    """Generates a small synthetic borehole dataframe for modeling."""
    config = SimulationConfig(
        total_depth=20.0,
        interval=0.5,
        layers=[
            LayerConfig(
                rock_type="Sandstone",
                depth_start=0.0,
                depth_end=10.0,
                density=2.3,
                porosity=0.2,
                base_resistivity=150.0,
                base_gamma=35.0,
                base_sonic=80.0,
            ),
            LayerConfig(
                rock_type="Limestone",
                depth_start=10.0,
                depth_end=20.0,
                density=2.7,
                porosity=0.1,
                base_resistivity=600.0,
                base_gamma=15.0,
                base_sonic=50.0,
            ),
        ],
    )
    simulator = GeologicalSimulator(config)
    logs = simulator.simulate()

    # Preprocess via pandas to get features
    df = pd.DataFrame(logs)
    sensor_columns = [
        "gamma_ray",
        "resistivity",
        "porosity",
        "density",
        "sonic_travel_time",
    ]
    for col in sensor_columns:
        df[f"{col}_ma5"] = df[col].rolling(window=5, min_periods=1).mean()

    df["porosity_resistivity_ratio"] = df["porosity"] / (df["resistivity"] + 1e-5)
    df["density_porosity_ratio"] = df["density"] / (df["porosity"] + 1e-5)
    df["rock_type_encoded"] = df["rock_type"].map(
        {"Claystone": 0, "Sandstone": 1, "Limestone": 2, "Shale": 3, "Granite": 4}
    )
    return df
