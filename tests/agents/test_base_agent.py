import pytest
from unittest.mock import MagicMock, patch
from src.agents.base_agent import BaseAgent, AgentCallbackHandler
import logging

@pytest.fixture
def mock_tools():
    tool1 = MagicMock()
    tool2 = MagicMock()
    return [tool1, tool2]

@pytest.fixture
def base_agent(mock_tools):
    return BaseAgent(
        tools=mock_tools,
        system_prompt="Test prompt",
        model_name="test_model",
        max_retries=3
    )

def test_agent_initialization(base_agent, mock_tools):
    assert base_agent.tools == mock_tools
    assert base_agent.prompt.template == "Test prompt"
    assert base_agent.max_retries == 3
    assert base_agent.callback_handler is not None
    assert isinstance(base_agent.callback_handler, AgentCallbackHandler)

def test_llm_initialization_retry_success(mock_tools):
    with patch('src.agents.base_agent.Ollama') as mock_ollama:
        # Make the first attempt fail, second succeed
        mock_ollama.side_effect = [Exception("Connection error"), MagicMock()]
        
        agent = BaseAgent(mock_tools, "Test prompt", max_retries=3)
        assert agent.llm is not None  # Should succeed on second attempt

def test_llm_initialization_retry_failure(mock_tools):
    with patch('src.agents.base_agent.Ollama') as mock_ollama:
        # Make all attempts fail
        mock_ollama.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception) as exc_info:
            BaseAgent(mock_tools, "Test prompt", max_retries=3)
        assert "Connection error" in str(exc_info.value)

def test_run_success(base_agent):
    base_agent.executor = MagicMock()
    base_agent.executor.invoke.return_value = {"result": "success"}
    
    result = base_agent.run("test task")
    assert result == {"result": "success"}
    base_agent.executor.invoke.assert_called_once_with({"input": "test task"})

def test_run_retry_success(base_agent):
    base_agent.executor = MagicMock()
    base_agent.executor.invoke.side_effect = [
        Exception("First error"),
        Exception("Second error"),
        {"result": "success"}
    ]
    
    result = base_agent.run("test task")
    assert result == {"result": "success"}
    assert base_agent.executor.invoke.call_count == 3

def test_run_retry_failure(base_agent):
    base_agent.executor = MagicMock()
    base_agent.executor.invoke.side_effect = Exception("Persistent error")
    
    with pytest.raises(Exception) as exc_info:
        base_agent.run("test task")
    assert "Persistent error" in str(exc_info.value)
    assert base_agent.executor.invoke.call_count == base_agent.max_retries

def test_callback_handler_logging():
    handler = AgentCallbackHandler("TestAgent")
    with patch('logging.getLogger') as mock_logger:
        mock_logger.return_value = MagicMock()
        
        # Test LLM start logging
        handler.on_llm_start(None)
        mock_logger.return_value.info.assert_called_with("TestAgent starting LLM call")
        
        # Test LLM error logging
        error = Exception("Test error")
        handler.on_llm_error(error)
        mock_logger.return_value.error.assert_called_with("TestAgent LLM error: Test error")
        
        # Test tool start logging
        handler.on_tool_start("test_tool")
        mock_logger.return_value.info.assert_called_with("TestAgent using tool: test_tool")
        
        # Test tool error logging
        handler.on_tool_error(error)
        mock_logger.return_value.error.assert_called_with("TestAgent tool error: Test error")

@pytest.mark.asyncio
async def test_async_not_implemented(base_agent):
    with pytest.raises(NotImplementedError):
        await base_agent._arun("test")