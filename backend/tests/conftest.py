import os
import tempfile

# Must be set BEFORE the app is imported: isolated DB + offline mock LLM
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-that-is-at-least-32-bytes-long"
os.environ["AI_CALLS_PER_HOUR"] = "1000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

RESUME = """Ambati Example
Software Engineer | Python, React, FastAPI, SQL, Docker, Machine Learning
Experience: Built React and Angular web apps at a consulting firm. Created REST APIs with FastAPI.
Trained scikit-learn and PyTorch models for intrusion detection. Used Git and PostgreSQL daily.
Education: MS Computer Science. Certificates in deep learning and databases.
"""

JOB = """AI Engineer
Company: Acme Robotics
Location: Detroit, MI (Hybrid)
Salary: $110,000 - $130,000
Requirements: Python, FastAPI, Docker, Kubernetes, LLMs, RAG and PostgreSQL. Experience with AWS.
Nice to have: React, LangChain
"""


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def signup(client, email="a@example.com"):
    r = client.post("/api/auth/signup", json={"email": email, "password": "password123", "name": "A"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return signup(client)
