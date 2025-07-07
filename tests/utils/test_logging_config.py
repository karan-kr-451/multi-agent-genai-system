import pytest
import logging
import json
import os
from unittest.mock import patch, MagicMock
from src.utils.logging_config import setup_logging, get_logger, JsonFormatter

@pytest.fixture
def temp_log_dir(tmp_path):
    log_dir = tmp_path / "logs"
    return str(log_dir)

@pytest.fixture
def json_formatter():
    return JsonFormatter()

def test_setup_logging_creates_directory(temp_log_dir):
    setup_logging(temp_log_dir)
    assert os.path.exists(temp_log_dir)

def test_setup_logging_creates_handlers():
    logger = logging.getLogger("test_logger")
    assert len(logger.handlers) > 0

def test_get_logger():
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"

def test_json_formatter_basic(json_formatter):
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = json_formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["name"] == "test_logger"
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test message"
    assert "timestamp" in parsed
    assert "pathname" in parsed
    assert "lineno" in parsed
    assert "function" in parsed

def test_json_formatter_with_exception(json_formatter):
    try:
        raise ValueError("Test error")
    except ValueError:
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=True
        )
        
        formatted = json_formatter.format(record)
        parsed = json.loads(formatted)
        
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"
        assert parsed["exception"]["message"] == "Test error"
        assert "traceback" in parsed["exception"]

def test_json_formatter_with_extra_fields(json_formatter):
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Processing job",
        args=(),
        exc_info=None
    )
    record.job_id = "123"
    record.agent = "idea_generation"
    record.state = "PROCESSING"
    record.duration = 1.5
    
    formatted = json_formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["job_id"] == "123"
    assert parsed["agent"] == "idea_generation"
    assert parsed["state"] == "PROCESSING"
    assert parsed["duration"] == 1.5

def test_json_formatter_filters_sensitive_data(json_formatter):
    # Test with sensitive data in message
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Connected with password=secret123 and api_key=abc123",
        args=(),
        exc_info=None
    )
    record.sensitive_field = "password123"
    
    formatted = json_formatter.format(record)
    parsed = json.loads(formatted)
    
    assert "secret123" not in parsed["message"]
    assert "abc123" not in parsed["message"]
    assert "***REDACTED***" in parsed["message"]
    assert parsed["sensitive_field"] == "***REDACTED***"

def test_json_formatter_nested_sensitive_data(json_formatter):
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    record.config = {
        "database": {
            "password": "secret123",
            "host": "localhost"
        },
        "api": {
            "key": "abc123"
        }
    }
    
    formatted = json_formatter.format(record)
    parsed = json.loads(formatted)
    
    assert parsed["config"]["database"]["password"] == "***REDACTED***"
    assert parsed["config"]["database"]["host"] == "localhost"
    assert parsed["config"]["api"]["key"] == "***REDACTED***"

@pytest.mark.parametrize("log_level", [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL
])
def test_logger_levels(temp_log_dir, log_level):
    setup_logging(temp_log_dir)
    logger = get_logger("test_logger")
    logger.setLevel(log_level)
    
    with patch.object(logger, 'handle') as mock_handle:
        logger.log(log_level, "Test message")
        assert mock_handle.called

def test_logging_with_large_messages(json_formatter):
    large_msg = "x" * 1000000  # 1MB of data
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg=large_msg,
        args=(),
        exc_info=None
    )
    
    formatted = json_formatter.format(record)
    parsed = json.loads(formatted)
    assert len(parsed["message"]) == len(large_msg)

def test_logging_configuration_fallback():
    with patch('logging.config.dictConfig', side_effect=Exception("Test error")):
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            mock_basic_config.assert_called_once()

def test_rotating_file_handler_rotation(temp_log_dir):
    setup_logging(temp_log_dir)
    logger = get_logger("test_logger")
    
    # Write enough data to trigger rotation
    large_msg = "x" * 1000000  # 1MB message
    for _ in range(15):  # Should create multiple log files
        logger.info(large_msg)
    
    log_files = [f for f in os.listdir(temp_log_dir) if f.endswith('.log')]
    assert len(log_files) > 1  # Should have main log file and at least one backup