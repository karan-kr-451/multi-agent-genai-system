import pytest
import os
from unittest.mock import patch, MagicMock
import logging
from src.utils.config import Settings, load_settings, get_settings

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {
        "REDIS_HOST": "test-redis",
        "REDIS_PORT": "6380",
        "REDIS_PASSWORD": "test-password",
        "OLLAMA_HOST": "http://test-ollama:11434",
        "OLLAMA_MODEL": "test-model",
        "LOG_LEVEL": "DEBUG",
        "WORKSPACE_DIR": "test-workspace",
        "MAX_RETRIES": "5",
        "POLLING_INTERVAL": "1000",
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:5173",
        "API_KEY": "test-key",
        "ENABLE_AUTH": "true"
    }):
        yield

def test_settings_defaults():
    settings = Settings()
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    assert settings.REDIS_PASSWORD is None
    assert settings.OLLAMA_MODEL == "llama3"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.MAX_RETRIES == 3
    assert settings.POLLING_INTERVAL == 2000
    assert settings.CORS_ORIGINS == ["*"]
    assert settings.API_KEY is None
    assert settings.ENABLE_AUTH is False

def test_settings_from_env(mock_env):
    settings = Settings()
    assert settings.REDIS_HOST == "test-redis"
    assert settings.REDIS_PORT == 6380
    assert settings.REDIS_PASSWORD == "test-password"
    assert settings.OLLAMA_HOST == "http://test-ollama:11434"
    assert settings.OLLAMA_MODEL == "test-model"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.WORKSPACE_DIR == "test-workspace"
    assert settings.MAX_RETRIES == 5
    assert settings.POLLING_INTERVAL == 1000
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://localhost:5173"]
    assert settings.API_KEY == "test-key"
    assert settings.ENABLE_AUTH is True

def test_validate_log_level():
    with pytest.raises(ValueError, match="Invalid log level"):
        Settings(LOG_LEVEL="INVALID")
    
    settings = Settings(LOG_LEVEL="debug")
    assert settings.LOG_LEVEL == "DEBUG"

def test_parse_cors_origins():
    # Test string input
    settings = Settings(CORS_ORIGINS="http://localhost:3000,http://test.com")
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://test.com"]
    
    # Test wildcard
    settings = Settings(CORS_ORIGINS="*")
    assert settings.CORS_ORIGINS == ["*"]
    
    # Test list input
    settings = Settings(CORS_ORIGINS=["http://localhost:3000"])
    assert settings.CORS_ORIGINS == ["http://localhost:3000"]

def test_get_redis_url():
    # Test with password
    settings = Settings(
        REDIS_HOST="redis-host",
        REDIS_PORT=6379,
        REDIS_PASSWORD="secret"
    )
    assert settings.get_redis_url() == "redis://:secret@redis-host:6379"
    
    # Test without password
    settings = Settings(
        REDIS_HOST="redis-host",
        REDIS_PORT=6379,
        REDIS_PASSWORD=None
    )
    assert settings.get_redis_url() == "redis://redis-host:6379"

@patch('os.makedirs')
@patch('logging.getLogger')
def test_load_settings(mock_logger, mock_makedirs, mock_env):
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance
    
    settings = load_settings()
    
    # Verify workspace directory creation
    mock_makedirs.assert_called_once_with(os.path.abspath("test-workspace"))
    
    # Verify logging setup
    mock_logger_instance.setLevel.assert_called_once_with("DEBUG")
    
    # Verify settings loaded correctly
    assert settings.REDIS_HOST == "test-redis"
    assert settings.LOG_LEVEL == "DEBUG"

def test_get_settings_singleton():
    # First call should create settings
    settings1 = get_settings()
    
    # Second call should return the same instance
    settings2 = get_settings()
    
    assert settings1 is settings2

@patch('os.makedirs')
def test_load_settings_error(mock_makedirs, mock_env):
    mock_makedirs.side_effect = OSError("Permission denied")
    
    with pytest.raises(Exception) as exc_info:
        load_settings()
    assert "Failed to load settings" in str(exc_info.value)

def test_settings_sensitive_data_logging(caplog):
    with caplog.at_level(logging.DEBUG):
        settings = load_settings()
        
        # Check that sensitive data is not logged
        log_records = [r.message for r in caplog.records if r.levelname == "DEBUG"]
        settings_log = next(
            (record for record in log_records if "Current settings" in record),
            None
        )
        
        assert settings_log is not None
        assert "REDIS_PASSWORD" not in settings_log
        assert "API_KEY" not in settings_log