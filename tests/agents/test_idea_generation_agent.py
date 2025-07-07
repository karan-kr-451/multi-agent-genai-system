import pytest
from unittest.mock import MagicMock, patch
import json
from src.agents.idea_generation_agent import IdeaGenerationAgent

@pytest.fixture
def mock_search_tool():
    search_tool = MagicMock()
    search_tool._run.return_value = "Found relevant articles about similar projects and technologies"
    return {"search": search_tool}

@pytest.fixture
def idea_generation_agent(mock_search_tool):
    with patch('src.agents.idea_generation_agent.ALL_TOOLS', mock_search_tool):
        agent = IdeaGenerationAgent()
        # Mock the LLM to return valid ideas
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = json.dumps([
            {
                "title": "Test Project",
                "description": "A test project description",
                "features": ["Feature 1", "Feature 2"],
                "technologies": ["Python/FastAPI", "React"]
            },
            {
                "title": "Alternative Project",
                "description": "An alternative approach",
                "features": ["Feature A", "Feature B"],
                "technologies": ["Node.js", "Vue"]
            }
        ])
        return agent

def test_agent_initialization(idea_generation_agent):
    assert len(idea_generation_agent.tools) == 1
    assert idea_generation_agent.prompt is not None
    assert "Idea Generation Agent" in idea_generation_agent.prompt.template

def test_generate_ideas_success(idea_generation_agent, mock_search_tool):
    input_context = {
        "initial_prompt": "Build a social media app"
    }
    
    result = idea_generation_agent.run(json.dumps(input_context))
    
    # Verify search tool was used for research
    mock_search_tool["search"]._run.assert_called_once()
    
    # Verify result structure
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(idea, dict) for idea in result)
    
    # Verify idea contents
    for idea in result:
        assert "title" in idea
        assert "description" in idea
        assert "features" in idea
        assert "technologies" in idea
        assert isinstance(idea["features"], list)
        assert isinstance(idea["technologies"], list)

def test_generate_ideas_with_github_url(idea_generation_agent, mock_search_tool):
    input_context = {
        "initial_prompt": "Build a social media app",
        "github_url": "https://github.com/test/repo"
    }
    
    result = idea_generation_agent.run(json.dumps(input_context))
    
    # Verify search was still performed
    mock_search_tool["search"]._run.assert_called_once()
    assert isinstance(result, list)
    assert len(result) > 0

def test_generate_ideas_with_ingested_files(idea_generation_agent, mock_search_tool):
    input_context = {
        "initial_prompt": "Build a social media app",
        "ingested_files": [
            {"source": "spec.txt", "destination": "workspace/spec.txt", "result": "Success"}
        ]
    }
    
    result = idea_generation_agent.run(json.dumps(input_context))
    
    # Verify search was performed
    mock_search_tool["search"]._run.assert_called_once()
    assert isinstance(result, list)
    assert len(result) > 0

def test_error_handling(idea_generation_agent, mock_search_tool):
    # Simulate a search tool failure
    mock_search_tool["search"]._run.side_effect = Exception("Search failed")
    
    input_context = {
        "initial_prompt": "Build a social media app"
    }
    
    # Should still complete with ideas even if search fails
    result = idea_generation_agent.run(json.dumps(input_context))
    assert isinstance(result, list)
    assert len(result) > 0

def test_invalid_input(idea_generation_agent):
    with pytest.raises(json.JSONDecodeError):
        idea_generation_agent.run("invalid json")

def test_empty_prompt(idea_generation_agent):
    input_context = {
        "initial_prompt": ""
    }
    
    result = idea_generation_agent.run(json.dumps(input_context))
    assert isinstance(result, list)
    assert len(result) > 0

def test_multiple_retries(idea_generation_agent, mock_search_tool):
    # Make the LLM fail twice then succeed
    idea_generation_agent.llm.invoke.side_effect = [
        Exception("First error"),
        Exception("Second error"),
        idea_generation_agent.llm.invoke.return_value  # Original success response
    ]
    
    input_context = {
        "initial_prompt": "Build a social media app"
    }
    
    result = idea_generation_agent.run(json.dumps(input_context))
    
    # Verify we got valid results after retries
    assert isinstance(result, list)
    assert len(result) > 0
    assert idea_generation_agent.llm.invoke.call_count == 3

@pytest.mark.asyncio
async def test_async_not_implemented(idea_generation_agent):
    with pytest.raises(NotImplementedError):
        await idea_generation_agent._arun("test")