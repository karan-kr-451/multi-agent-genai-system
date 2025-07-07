import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import logging
from src.mcp_server.middleware import (
    auth_middleware,
    error_handling_middleware,
    request_logging_middleware
)

@pytest.fixture
def app():
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app

@pytest.fixture
def test_client(app):
    return TestClient(app)

@pytest.fixture
def mock_settings():
    with patch("src.mcp_server.middleware.settings") as mock:
        mock.ENABLE_AUTH = True
        mock.API_KEY = "test-key"
        yield mock

async def test_auth_middleware_valid_key(mock_settings):
    request = Request({"type": "http", "headers": [(b"x-api-key", b"test-key")], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        return "success"
    
    response = await auth_middleware(request, mock_call_next)
    assert response == "success"

async def test_auth_middleware_invalid_key(mock_settings):
    request = Request({"type": "http", "headers": [(b"x-api-key", b"wrong-key")], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        return "success"
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware(request, mock_call_next)
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail

async def test_auth_middleware_missing_key(mock_settings):
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        return "success"
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_middleware(request, mock_call_next)
    assert exc_info.value.status_code == 401
    assert "API key is required" in exc_info.value.detail

async def test_auth_middleware_auth_disabled(mock_settings):
    mock_settings.ENABLE_AUTH = False
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        return "success"
    
    response = await auth_middleware(request, mock_call_next)
    assert response == "success"

async def test_error_handling_middleware_success():
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        return "success"
    
    response = await error_handling_middleware(request, mock_call_next)
    assert response == "success"

async def test_error_handling_middleware_http_exception():
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        raise HTTPException(status_code=404, detail="Not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await error_handling_middleware(request, mock_call_next)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Not found"

async def test_error_handling_middleware_unexpected_error():
    request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
    
    async def mock_call_next(request):
        raise ValueError("Unexpected error")
    
    response = await error_handling_middleware(request, mock_call_next)
    assert response.status_code == 500
    assert "internal server error" in response.body.decode().lower()

async def test_request_logging_middleware(caplog):
    with caplog.at_level(logging.INFO):
        request = Request({"type": "http", "headers": [], "client": ("127.0.0.1", 8000)})
        
        async def mock_call_next(request):
            return MagicMock(status_code=200)
        
        await request_logging_middleware(request, mock_call_next)
        
        # Check if request was logged
        assert any("Request started:" in record.message for record in caplog.records)
        assert any("Request completed:" in record.message for record in caplog.records)
        assert any("Status: 200" in record.message for record in caplog.records)

def test_middleware_integration(app, test_client, mock_settings):
    # Add middleware to app
    app.middleware("http")(auth_middleware)
    app.middleware("http")(error_handling_middleware)
    app.middleware("http")(request_logging_middleware)
    
    # Test with valid API key
    response = test_client.get("/test", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    
    # Test with invalid API key
    response = test_client.get("/test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    
    # Test error endpoint
    response = test_client.get("/error", headers={"X-API-Key": "test-key"})
    assert response.status_code == 500
    assert "internal server error" in response.json()["detail"].lower()

def test_middleware_order(app, test_client, mock_settings):
    # Test that middleware is executed in the correct order:
    # 1. Request logging
    # 2. Error handling
    # 3. Authentication
    
    logged_steps = []
    
    async def custom_auth_middleware(request: Request, call_next):
        logged_steps.append("auth")
        return await auth_middleware(request, call_next)
    
    async def custom_error_middleware(request: Request, call_next):
        logged_steps.append("error")
        return await error_handling_middleware(request, call_next)
    
    async def custom_logging_middleware(request: Request, call_next):
        logged_steps.append("logging")
        return await request_logging_middleware(request, call_next)
    
    app.middleware("http")(custom_auth_middleware)
    app.middleware("http")(custom_error_middleware)
    app.middleware("http")(custom_logging_middleware)
    
    test_client.get("/test", headers={"X-API-Key": "test-key"})
    
    # Verify middleware execution order
    assert logged_steps == ["logging", "error", "auth"]