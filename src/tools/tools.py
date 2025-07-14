import os
import subprocess
import requests
from typing import ClassVar
from langchain_community.tools import BaseTool, ShellTool, DuckDuckGoSearchRun
import importlib.util
import git
import json

# --- Standard Tools ---

# 1. Shell Tool to run any shell command
shell_tool = ShellTool()

# 2. Git operations using gitpython
class CustomGitTool(BaseTool):
    name: ClassVar[str] = "GitTool"
    description: ClassVar[str] = "Interact with git repositories. Input should be a JSON object with 'action' and 'args'."

    def _run(self, tool_input: str) -> str:
        try:
            repo = git.Repo(os.getcwd())
            return f"Git repository at {repo.working_dir}"
        except Exception as e:
            return f"Git error: {str(e)}"

    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("GitTool does not support async")

# 3. Web Search Tool
search_tool = DuckDuckGoSearchRun()

# Create instances of tools
git_tool = CustomGitTool()

# --- Custom Tools ---

class FileSystemTool(BaseTool):
    name: ClassVar[str] = "FileSystemTool"
    description: ClassVar[str] = "Manages files and directories. Input should be a JSON object with 'action' and 'args'."

    def _run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
            action = params.get("action")
            args = params.get("args", {})

            workspace_root = os.path.abspath("workspace")
            if not os.path.exists(workspace_root):
                os.makedirs(workspace_root)

            if "file_path" in args:
                target_path = os.path.abspath(os.path.join(workspace_root, args["file_path"]))
                if not target_path.startswith(workspace_root):
                    return "Error: Path is outside the allowed workspace."
                args["file_path"] = target_path
            
            if "path" in args:
                target_path = os.path.abspath(os.path.join(workspace_root, args["path"]))
                if not target_path.startswith(workspace_root):
                    return "Error: Path is outside the allowed workspace."
                args["path"] = target_path

            if action == "write":
                os.makedirs(os.path.dirname(args["file_path"]), exist_ok=True)
                with open(args["file_path"], "w") as f:
                    f.write(args["content"])
                return f"Successfully wrote to {args['file_path']}"
            
            elif action == "read":
                with open(args["file_path"], "r") as f:
                    return f.read()

            elif action == "list":
                return ", ".join(os.listdir(args["path"]))
            
            else:
                return "Error: Invalid action specified."

        except Exception as e:
            return f"An error occurred: {e}"

    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("FileSystemTool does not support async")

class PlantUMLTool(BaseTool):
    name: ClassVar[str] = "PlantUMLTool"
    description: ClassVar[str] = "Generates a URL to a PlantUML diagram from a text description."

    def _run(self, puml_content: str) -> str:
        from plantuml import PlantUML
        
        pl = PlantUML(url='http://www.plantuml.com/plantuml')
        try:
            url = pl.get_url(puml_content)
            return f"Diagram URL: {url}"
        except Exception as e:
            return f"Error generating diagram: {e}"

    async def _arun(self, puml_content: str) -> str:
        raise NotImplementedError("PlantUMLTool does not support async")

# Instantiate custom tools
filesystem_tool = FileSystemTool()
plantuml_tool = PlantUMLTool()

# Import other tools
from src.tools.arxiv_tool import ArxivTool
arxiv_tool = ArxivTool()

from src.tools.ast_tool import ASTAnalysisTool
ast_tool = ASTAnalysisTool()

from src.tools.domain_expert_tool import DomainExpertTool
domain_expert_tool = DomainExpertTool()

from src.tools.runtime_monitor_tool import RuntimeMonitorTool
runtime_monitor_tool = RuntimeMonitorTool()

from src.tools.pdf_reader_tool import PDFReaderTool
pdf_reader_tool = PDFReaderTool()

from src.tools.ingestion_tool import IngestionTool
ingestion_tool = IngestionTool()

# A dictionary to easily access all tools
ALL_TOOLS = {
    "shell": shell_tool,
    "git": git_tool,
    "search": search_tool,
    "filesystem": filesystem_tool,
    "plantuml": plantuml_tool,
    "arxiv": arxiv_tool,
    "ast": ast_tool,
    "domain_expert": domain_expert_tool,
    "runtime_monitor": runtime_monitor_tool,
    "pdf_reader": pdf_reader_tool,
    "ingestion": ingestion_tool
}

def load_dynamic_tools() -> None:
    """Loads tools dynamically from the src/tools directory."""
    tools_dir = os.path.dirname(__file__)
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename not in [
            "__init__.py", "tools.py", "arxiv_tool.py", "ast_tool.py",
            "domain_expert_tool.py", "runtime_monitor_tool.py",
            "pdf_reader_tool.py", "ingestion_tool.py"
        ]:
            module_name = filename[:-3]
            file_path = os.path.join(tools_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            tool_instance = getattr(module, module_name)
            ALL_TOOLS[module_name] = tool_instance

# Load dynamic tools when this module is imported
load_dynamic_tools()
