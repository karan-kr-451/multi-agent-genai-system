import pytest
from unittest.mock import MagicMock, patch
import json
from src.agents.analyzer_agent import AnalyzerAgent

@pytest.fixture
def mock_tools():
    git_tool = MagicMock()
    filesystem_tool = MagicMock()
    search_tool = MagicMock()
    arxiv_tool = MagicMock()
    domain_expert_tool = MagicMock()
    pdf_reader_tool = MagicMock()
    
    # Set up mock returns
    search_tool._run.return_value = "Found relevant technology articles"
    arxiv_tool._run.return_value = json.dumps([
        {"title": "Test Paper", "summary": "Relevant research", "url": "http://example.com"}
    ])
    domain_expert_tool._run.return_value = "Domain specific insights for the project"
    
    return {
        "git": git_tool,
        "filesystem": filesystem_tool,
        "search": search_tool,
        "arxiv": arxiv_tool,
        "domain_expert": domain_expert_tool,
        "pdf_reader": pdf_reader_tool
    }

@pytest.fixture
def analyzer_agent(mock_tools):
    with patch('src.agents.analyzer_agent.ALL_TOOLS', mock_tools):
        agent = AnalyzerAgent()
        # Mock the LLM to return a valid analysis
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = json.dumps({
            "summary": "Test summary",
            "analysis": "Test analysis",
            "research_findings": ["Finding 1", "Finding 2"],
            "domain_insights": "Test insights",
            "innovative_suggestions": [
                {"suggestion": "Test suggestion", "justification": "Test justification"}
            ],
            "reasoning_explanation": "Test reasoning"
        })
        return agent

def test_analyzer_initialization(analyzer_agent):
    assert len(analyzer_agent.tools) == 6
    assert analyzer_agent.prompt is not None

def test_analyze_with_github_url(analyzer_agent, mock_tools):
    input_context = {
        "initial_prompt": "Build a web app",
        "github_url": "https://github.com/test/repo"
    }
    
    result = analyzer_agent.run(json.dumps(input_context))
    
    # Verify git tool was used
    mock_tools["git"]._run.assert_called_once()
    assert isinstance(result, dict)
    assert "summary" in result
    assert "analysis" in result
    assert "innovative_suggestions" in result

def test_analyze_with_pdf(analyzer_agent, mock_tools):
    input_context = {
        "initial_prompt": "Build a web app",
        "pdf_path": "/path/to/spec.pdf"
    }
    
    result = analyzer_agent.run(json.dumps(input_context))
    
    # Verify PDF reader was used
    mock_tools["pdf_reader"]._run.assert_called_once()
    assert isinstance(result, dict)
    assert "summary" in result

def test_analyze_with_ingested_files(analyzer_agent, mock_tools):
    input_context = {
        "initial_prompt": "Build a web app",
        "ingested_files": [
            {"source": "test.txt", "destination": "workspace/test.txt"}
        ]
    }
    
    mock_tools["filesystem"]._run.return_value = "Test file content"
    
    result = analyzer_agent.run(json.dumps(input_context))
    
    # Verify filesystem tool was used to read ingested files
    mock_tools["filesystem"]._run.assert_called()
    assert isinstance(result, dict)
    assert "analysis" in result

def test_domain_expert_integration(analyzer_agent, mock_tools):
    input_context = {
        "initial_prompt": "Build a FinTech payment processing system"
    }
    
    result = analyzer_agent.run(json.dumps(input_context))
    
    # Verify domain expert was consulted for FinTech expertise
    mock_tools["domain_expert"]._run.assert_called_with("FinTech security")
    assert isinstance(result, dict)
    assert "domain_insights" in result

def test_research_integration(analyzer_agent, mock_tools):
    input_context = {
        "initial_prompt": "Build an AI-powered recommendation system"
    }
    
    result = analyzer_agent.run(json.dumps(input_context))
    
    # Verify both search and arxiv tools were used for research
    mock_tools["search"]._run.assert_called()
    mock_tools["arxiv"]._run.assert_called()
    assert isinstance(result, dict)
    assert "research_findings" in result

def test_error_handling(analyzer_agent, mock_tools):
    # Simulate a tool failure
    mock_tools["git"]._run.side_effect = Exception("Git error")
    
    input_context = {
        "initial_prompt": "Build a web app",
        "github_url": "https://github.com/test/repo"
    }
    
    # Should still complete analysis even if a tool fails
    result = analyzer_agent.run(json.dumps(input_context))
    assert isinstance(result, dict)
    assert "summary" in result

@pytest.mark.asyncio
async def test_async_execution(analyzer_agent):
    with pytest.raises(NotImplementedError):
        await analyzer_agent._arun("test")