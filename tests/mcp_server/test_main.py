import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import fakeredis
import json
import logging
from src.mcp_server.main import app, redis_client
from src.utils.config import Settings

@pytest.fixture
def mock_settings():
    with patch('src.mcp_server.main.settings') as mock:
        mock.ENABLE_AUTH = True
        mock.API_KEY = "test-key"
        mock.CORS_ORIGINS = ["http://localhost:3000"]
        yield mock

@pytest.fixture
def mock_redis():
    with patch('src.mcp_server.main.redis_client') as mock:
        mock.return_value = fakeredis.FakeRedis()
        yield mock

@pytest.fixture
def mock_background_tasks():
    with patch('fastapi.BackgroundTasks.add_task') as mock:
        yield mock

@pytest.fixture
def test_client(mock_settings):
    return TestClient(app)

def test_start_project_with_auth(test_client, mock_redis, mock_background_tasks):
    response = test_client.post(
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

def test_start_project_without_auth(test_client, mock_redis):
    response = test_client.post(
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

def test_start_project_invalid_auth(test_client, mock_redis):
    response = test_client.post(
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

def test_request_logging(test_client, mock_redis, caplog):
    with caplog.at_level(logging.INFO):
        test_client.get(
            "/status/123",
            headers={"X-API-Key": "test-key"}
        )
        
        # Verify request logging
        assert any("Request started: GET /status/123" in record.message for record in caplog.records)
        assert any("Request completed: GET /status/123" in record.message for record in caplog.records)

def test_error_handling(test_client, mock_redis):
    # Simulate a server error
    mock_redis.get.side_effect = Exception("Redis error")
    
    response = test_client.get(
        "/status/123",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 500
    assert "internal server error" in response.json()["detail"].lower()

def test_cors_headers(test_client):
    response = test_client.options(
        "/start_project",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_select_idea_not_found(test_client, mock_redis):
    response = test_client.post(
        "/jobs/nonexistent/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 404

def test_select_idea_wrong_state(test_client, mock_redis):
    job_data = {
        "state": "ANALYZING",
        "context": {}
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = test_client.post(
        "/jobs/123/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 400
    assert "not in IDEA_SELECTION state" in response.json()["detail"]

def test_select_idea_success(test_client, mock_redis, mock_background_tasks):
    job_data = {
        "state": "IDEA_SELECTION",
        "context": {
            "generated_ideas": [
                {"title": "Test Idea", "description": "Test Description"}
            ]
        }
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = test_client.post(
        "/jobs/123/select_idea?idea_index=0",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert "Idea selected" in response.json()["message"]

def test_get_status(test_client, mock_redis):
    job_data = {
        "job_id": "123",
        "state": "COMPLETED",
        "context": {}
    }
    mock_redis.get.return_value = json.dumps(job_data)
    
    response = test_client.get(
        "/status/123",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
    assert response.json()["state"] == "COMPLETED"

def test_get_status_not_found(test_client, mock_redis):
    mock_redis.get.return_value = None
    response = test_client.get(
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

def test_sensitive_data_logging(test_client, mock_redis, caplog):
    with caplog.at_level(logging.INFO):
        test_client.post(
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