import pytest
import os
import json
import shutil
from src.tools.tools import FileSystemTool

@pytest.fixture
def filesystem_tool():
    return FileSystemTool()

@pytest.fixture
def test_workspace(tmp_path):
    # Create a temporary workspace directory
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # Set up test files and directories
    test_file = workspace / "test.txt"
    test_file.write_text("Test content")
    test_dir = workspace / "testdir"
    test_dir.mkdir()
    
    yield workspace
    
    # Cleanup
    shutil.rmtree(workspace)

def test_read_file(filesystem_tool, test_workspace):
    input_json = json.dumps({
        "action": "read",
        "args": {
            "file_path": "test.txt"
        }
    })
    
    result = filesystem_tool._run(input_json)
    assert result == "Test content"

def test_write_file(filesystem_tool, test_workspace):
    input_json = json.dumps({
        "action": "write",
        "args": {
            "file_path": "new_file.txt",
            "content": "New content"
        }
    })
    
    result = filesystem_tool._run(input_json)
    assert "Successfully wrote to" in result
    
    # Verify file was created with correct content
    with open(os.path.join(test_workspace, "new_file.txt")) as f:
        assert f.read() == "New content"

def test_list_directory(filesystem_tool, test_workspace):
    input_json = json.dumps({
        "action": "list",
        "args": {
            "path": "."
        }
    })
    
    result = filesystem_tool._run(input_json)
    assert "test.txt" in result
    assert "testdir" in result

def test_path_traversal_prevention(filesystem_tool, test_workspace):
    # Try to access file outside workspace
    input_json = json.dumps({
        "action": "read",
        "args": {
            "file_path": "../outside.txt"
        }
    })
    
    result = filesystem_tool._run(input_json)
    assert "Error: Path is outside the allowed workspace" in result

def test_invalid_action(filesystem_tool):
    input_json = json.dumps({
        "action": "invalid_action",
        "args": {}
    })
    
    result = filesystem_tool._run(input_json)
    assert "Error: Invalid action specified" in result

def test_missing_args(filesystem_tool):
    input_json = json.dumps({
        "action": "read"
    })
    
    result = filesystem_tool._run(input_json)
    assert "An error occurred" in result

@pytest.mark.asyncio
async def test_async_not_implemented(filesystem_tool):
    with pytest.raises(NotImplementedError):
        await filesystem_tool._arun("test")