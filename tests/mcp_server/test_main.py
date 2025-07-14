import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import fakeredis
import json
import logging
from src.mcp_server.main import app, redis_client
from src.utils.config import Settings

# Use fakeredis server for testing
redis_server = fakeredis.FakeServer()
fake_redis = fakeredis.FakeStrictRedis(server=redis_server)

# Patch the redis client
@pytest.fixture(autouse=True)
def mock_redis():
    with patch('src.mcp_server.main.redis_client', fake_redis):
        yield fake_redis

@pytest.fixture
def mock_settings():
    with patch('src.mcp_server.main.settings') as mock:
        mock.ENABLE_AUTH = True
        mock.API_KEY = "test-key"
        mock.CORS_ORIGINS = ["http://localhost:3000"]
        yield mock

@pytest.fixture
def mock_background_tasks():
    with patch('fastapi.BackgroundTasks.add_task') as mock:
        yield mock

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_redis_operations(mock_redis):
    # Test basic Redis operations
    mock_redis.set("test_key", "test_value")
    assert mock_redis.get("test_key") == b"test_value"

def test_start_project_with_auth(client, mock_background_tasks):
    response = client.post(
        "/start_project",
        json={
            "prompt": "Build a todo app",
            "github_url": None,
            "pdf_path": None,
            "files_to_ingest": []
        },
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert "job_id" in response.json()
    assert "message" in response.json()
    mock_background_tasks.assert_called_once()

def test_start_project_without_auth(client, mock_redis):
    response = client.post(
        "/start_project",
        json={
            "prompt": "Build a todo app",
            "github_url": None,
            "pdf_path": None,
            "files_to_ingest": []
        }
    )
    assert response.status_code == 401
    assert "API key is required" in response.json()["detail"]

def test_start_project_invalid_auth(client, mock_redis):
    response = client.post(
        "/start_project",
        json={
            "prompt": "Build a todo app",
            "github_url": None,
            "pdf_path": None,
            "files_to_ingest": []
        },
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

def test_request_logging(client, mock_redis, caplog):
    with caplog.at_level(logging.INFO):
        client.get(
            "/status/123",
            headers={"X-API-Key": "test-key"}
        )
        
        # Verify request logging
        assert any("Request started: GET /status/123" in record.message for record in caplog.records)
        assert any("Request completed: GET /status/123" in record.message for record in caplog.records)

def test_error_handling(client, mock_redis):
    # Simulate a server error
    mock_redis.get.side_effect = Exception("Redis error")
    
    response = client.get(
        "/status/123",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 500
    assert "internal server error" in response.json()["detail"].lower()

def test_cors_headers(client):
    response = client.options(
        "/start_project",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_select_idea_not_found(client, mock_redis):
    response = client.post(
        "/jobs/nonexistent/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 404

def test_select_idea_wrong_state(client, mock_redis):
    job_data = {
        "state": "ANALYZING",
        "context": {}
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = client.post(
        "/jobs/123/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 400
    assert "not in IDEA_SELECTION state" in response.json()["detail"]

def test_select_idea_success(client, mock_redis, mock_background_tasks):
    job_data = {
        "state": "IDEA_SELECTION",
        "context": {
            "generated_ideas": [
                {"title": "Test Idea", "description": "Test Description"}
            ]
        }
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = client.post(
        "/jobs/123/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert "Idea selected" in response.json()["message"]

def test_get_status(client, mock_redis):
    job_data = {
        "job_id": "123",
        "state": "COMPLETED",
        "context": {}
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = client.get(
        "/status/123",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert response.json()["state"] == "COMPLETED"

def test_get_status_not_found(client, mock_redis):
    mock_redis.get.return_value = None
    response = client.get(
        "/status/nonexistent",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_workflow_manager():
    with patch('src.mcp_server.main.redis_client') as mock_redis, \
         patch('src.mcp_server.main.run_agent') as mock_run_agent:
        
        job_data = {
            "job_id": "test_job",
            "state": "IDEA_GENERATION",
            "context": {"initial_prompt": "Test prompt"}
        }
        mock_redis.get.return_value = json.dumps(job_data)
        mock_run_agent.return_value = {"ideas": ["Test idea"]}
        
        from src.mcp_server.main import workflow_manager
        await workflow_manager("test_job")
        
        mock_run_agent.assert_called_once_with(
            "idea_generation",
            job_data["context"]
        )

def test_sensitive_data_logging(client, mock_redis, caplog):
    with caplog.at_level(logging.INFO):
        client.post(
            "/start_project",
            json={
                "prompt": "Build a todo app",
                "github_url": None,
                "pdf_path": None,
                "files_to_ingest": []
            },
            headers={"X-API-Key": "test-key"}
        )
        
        # Verify sensitive data is not logged
        assert not any("test-key" in record.message for record in caplog.records)