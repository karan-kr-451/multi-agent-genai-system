import pytest
import os
import shutil
from unittest.mock import patch, mock_open
from src.system_modifier import SystemModifier

VALID_TOOL_CODE = '''
from langchain.tools import BaseTool

class TestTool(BaseTool):
    name = "test_tool"
    description = "A test tool"
    
    def _run(self, input_str: str) -> str:
        return "test output"
        
    async def _arun(self, input_str: str) -> str:
        raise NotImplementedError
'''

VALID_AGENT_CODE = '''
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS

TEST_PROMPT = """
You are a Test Agent. Your role is to test things.
Begin now. The input is: {input}
"""

class TestAgent(BaseAgent):
    def __init__(self):
        tools = [ALL_TOOLS["filesystem"]]
        super().__init__(tools, TEST_PROMPT)
'''

INVALID_TOOL_CODE = '''
class InvalidTool:
    def some_method(self):
        pass
'''

INVALID_AGENT_CODE = '''
class InvalidAgent:
    def __init__(self):
        pass
'''

@pytest.fixture
def test_dirs(tmp_path):
    # Create temporary directories mimicking the project structure
    base_dir = tmp_path / "test_project"
    src_dir = base_dir / "src"
    tools_dir = src_dir / "tools"
    agents_dir = src_dir / "agents"
    
    for dir_path in [base_dir, src_dir, tools_dir, agents_dir]:
        dir_path.mkdir()
    
    yield {
        "base": str(base_dir),
        "tools": str(tools_dir),
        "agents": str(agents_dir)
    }
    
    # Cleanup
    shutil.rmtree(str(base_dir))

@pytest.fixture
def system_modifier(test_dirs):
    return SystemModifier(test_dirs["base"])

def test_initialization(system_modifier, test_dirs):
    assert system_modifier.tools_dir == test_dirs["tools"]
    assert system_modifier.agents_dir == test_dirs["agents"]

def test_initialization_missing_dirs(test_dirs):
    # Remove required directories
    shutil.rmtree(test_dirs["tools"])
    shutil.rmtree(test_dirs["agents"])
    
    with pytest.raises(ValueError, match="Required directory not found"):
        SystemModifier(test_dirs["base"])

def test_validate_python_code(system_modifier):
    assert system_modifier.validate_python_code("x = 1")
    with pytest.raises(SyntaxError):
        system_modifier.validate_python_code("x = ")

def test_validate_class_structure(system_modifier):
    valid_code = "class Test(BaseClass): pass"
    assert system_modifier.validate_class_structure(valid_code, "BaseClass")
    
    invalid_code = "class Test: pass"
    assert not system_modifier.validate_class_structure(invalid_code, "BaseClass")

def test_validate_tool_code(system_modifier):
    assert system_modifier.validate_tool_code(VALID_TOOL_CODE)
    assert not system_modifier.validate_tool_code(INVALID_TOOL_CODE)

def test_validate_agent_code(system_modifier):
    assert system_modifier.validate_agent_code(VALID_AGENT_CODE)
    assert not system_modifier.validate_agent_code(INVALID_AGENT_CODE)

def test_safe_write_file(system_modifier, test_dirs):
    test_file = os.path.join(test_dirs["tools"], "test.py")
    content = "test content"
    
    # Test normal write
    system_modifier.safe_write_file(test_file, content)
    assert os.path.exists(test_file)
    with open(test_file) as f:
        assert f.read() == content
    
    # Test backup creation
    new_content = "new content"
    system_modifier.safe_write_file(test_file, new_content)
    assert os.path.exists(test_file + ".bak")
    with open(test_file) as f:
        assert f.read() == new_content

def test_safe_write_file_error(system_modifier, test_dirs):
    test_file = os.path.join(test_dirs["tools"], "test.py")
    content = "test content"
    
    # Write initial content
    system_modifier.safe_write_file(test_file, content)
    
    # Mock an error during write
    mock_open_instance = mock_open()
    mock_open_instance.write.side_effect = IOError("Write error")
    
    with patch("builtins.open", mock_open_instance):
        with pytest.raises(IOError):
            system_modifier.safe_write_file(test_file, "new content")
        
        # Verify backup was restored
        with open(test_file) as f:
            assert f.read() == content

def test_apply_modifications_success(system_modifier):
    plan = {
        "new_tools": {
            "test_tool.py": VALID_TOOL_CODE
        },
        "new_agents": {
            "test_agent.py": VALID_AGENT_CODE
        },
        "mcp_modifications": [
            "Add new state TEST_STATE"
        ]
    }
    
    report = system_modifier.apply_modifications(plan)
    assert "Added new tool: test_tool.py" in report
    assert "Added new agent: test_agent.py" in report
    assert "MCP Modification: Add new state TEST_STATE" in report

def test_apply_modifications_invalid_plan(system_modifier):
    with pytest.raises(ValueError, match="Plan must be a dictionary"):
        system_modifier.apply_modifications("not a dict")

def test_apply_modifications_invalid_code(system_modifier):
    plan = {
        "new_tools": {
            "invalid_tool.py": INVALID_TOOL_CODE
        }
    }
    
    with pytest.raises(ValueError, match="Invalid tool code"):
        system_modifier.apply_modifications(plan)

def test_test_new_component(system_modifier, test_dirs):
    # Write a valid Python module
    test_file = os.path.join(test_dirs["tools"], "test_module.py")
    with open(test_file, "w") as f:
        f.write("def test_function(): return True")
    
    assert system_modifier.test_new_component(test_file) is None
    
    # Test with invalid Python code
    invalid_file = os.path.join(test_dirs["tools"], "invalid.py")
    with open(invalid_file, "w") as f:
        f.write("this is not valid python")
    
    assert system_modifier.test_new_component(invalid_file) is not None

def test_full_modification_workflow(system_modifier):
    plan = {
        "new_tools": {
            "calculator_tool.py": '''
from langchain.tools import BaseTool

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Performs basic calculations"
    
    def _run(self, input_str: str) -> str:
        try:
            return str(eval(input_str))
        except:
            return "Error in calculation"
            
    async def _arun(self, input_str: str) -> str:
        raise NotImplementedError
'''
        },
        "new_agents": {
            "math_agent.py": '''
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS

MATH_PROMPT = """
You are the Math Agent. Your role is to solve mathematical problems.
Begin now. The problem is: {input}
"""

class MathAgent(BaseAgent):
    def __init__(self):
        tools = [ALL_TOOLS["calculator"]]
        super().__init__(tools, MATH_PROMPT)
'''
        },
        "mcp_modifications": [
            "Add MATH_PROCESSING state",
            "Update workflow to handle mathematical tasks"
        ]
    }
    
    # Apply modifications
    report = system_modifier.apply_modifications(plan)
    
    # Verify files were created
    assert os.path.exists(os.path.join(system_modifier.tools_dir, "calculator_tool.py"))
    assert os.path.exists(os.path.join(system_modifier.agents_dir, "math_agent.py"))
    
    # Verify report contains all modifications
    assert "Added new tool: calculator_tool.py" in report
    assert "Added new agent: math_agent.py" in report
    assert "MCP Modification: Add MATH_PROCESSING state" in report
    
    # Test importing new components
    assert system_modifier.test_new_component(
        os.path.join(system_modifier.tools_dir, "calculator_tool.py")
    ) is None
    assert system_modifier.test_new_component(
        os.path.join(system_modifier.agents_dir, "math_agent.py")
    ) is None