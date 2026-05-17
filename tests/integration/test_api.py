"""
Integration tests for FastAPI endpoints.
Uses TestClient to test the full request/response cycle.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(scope="module")
def client():
    """Create a test client with mocked LM Studio."""
    mock_result = MagicMock()
    mock_result.content = "Test response from agent"
    mock_result.tools_used = []
    mock_result.execution_time = 0.5
    mock_result.error = None
    mock_result.to_dict = MagicMock(return_value={
        "content": "Test response",
        "agent_id": "test-01",
        "task_id": "t-001",
        "tools_used": [],
        "execution_time": 0.5,
        "error": None,
        "timestamp": "2024-01-01T00:00:00Z",
    })

    with patch("backend.core.lm_studio_client.AsyncOpenAI"), \
         patch("backend.agents.base_agent.lm_client") as mock_lm:
        mock_lm.health_check = AsyncMock(return_value=True)
        mock_lm.list_models = AsyncMock(return_value=["local-model"])
        mock_lm.current_model = "local-model"

        from backend.api.app import app
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "agents" in data

    def test_health_has_agent_count(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert isinstance(data["agents"], int)
        assert data["agents"] >= 0


class TestAgentsEndpoint:
    def test_list_agents_returns_200(self, client):
        resp = client.get("/agents")
        assert resp.status_code == 200

    def test_list_agents_has_agents_key(self, client):
        resp = client.get("/agents")
        data = resp.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_get_specific_agent(self, client):
        resp = client.get("/agents/coding")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data

    def test_get_nonexistent_agent_returns_404(self, client):
        resp = client.get("/agents/nonexistent-agent-xyz")
        assert resp.status_code == 404


class TestTasksEndpoint:
    def test_create_task(self, client):
        resp = client.post("/tasks", json={"prompt": "test task", "agent": "coding"})
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    def test_list_tasks(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data

    def test_get_task_by_id(self, client):
        create_resp = client.post("/tasks", json={"prompt": "lookup test", "agent": "research"})
        task_id = create_resp.json()["task_id"]

        resp = client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id

    def test_get_nonexistent_task(self, client):
        resp = client.get("/tasks/nonexistent-id-xyz")
        assert resp.status_code == 404


class TestMemoryEndpoint:
    def test_store_memory(self, client):
        resp = client.post("/memory", json={
            "text": "FastAPI is a modern Python web framework",
            "collection": "long_term",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data

    def test_query_memory(self, client):
        client.post("/memory", json={"text": "Python asyncio is powerful", "collection": "long_term"})
        resp = client.post("/memory/query", json={
            "query": "Python async",
            "collection": "long_term",
            "n_results": 3,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data

    def test_list_memory_collections(self, client):
        resp = client.get("/memory")
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data

    def test_clear_memory_collection(self, client):
        resp = client.delete("/memory/short_term")
        assert resp.status_code == 200


class TestModelsEndpoint:
    def test_list_models(self, client):
        resp = client.get("/models")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert "current" in data


class TestLogsEndpoint:
    def test_get_logs(self, client):
        resp = client.get("/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_logs_with_limit(self, client):
        resp = client.get("/logs?lines=10")
        assert resp.status_code == 200
