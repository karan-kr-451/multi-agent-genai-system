
import os
import subprocess
import requests
from langchain.tools import BaseTool, ShellTool, DuckDuckGoSearchRun
from langchain_community.tools import GitTool
import importlib.util

# --- Standard Tools ---

# 1. Shell Tool to run any shell command
shell_tool = ShellTool()

# 2. Git Tool (requires gitpython)
# Make sure to handle the case where the git tool needs a specific directory
git_tool = GitTool()

# 3. Web Search Tool
search_tool = DuckDuckGoSearchRun()

# --- Custom Tools ---

class FileSystemTool(BaseTool):
    name = "FileSystemTool"
    description = "Manages files and directories. Input should be a JSON object with 'action' and 'args'. Actions: 'read', 'write', 'list'. Args for 'write': {'file_path': 'path', 'content': 'text'}. Args for 'read': {'file_path': 'path'}. Args for 'list': {'path': 'dir_path'}."

    def _run(self, tool_input: str):
        import json
        try:
            params = json.loads(tool_input)
            action = params.get("action")
            args = params.get("args", {})

            # Ensure paths are within the project's workspace for security
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

    async def _arun(self, tool_input: str):
        raise NotImplementedError("FileSystemTool does not support async")

class PlantUMLTool(BaseTool):
    name = "PlantUMLTool"
    description = "Generates a URL to a PlantUML diagram from a text description. Input is the PlantUML syntax."

    def _run(self, puml_content: str):
        from plantuml import PlantUML
        
        pl = PlantUML(url='http://www.plantuml.com/plantuml')
        try:
            # The tool generates a URL pointing to the rendered diagram
            url = pl.get_url(puml_content)
            return f"Diagram URL: {url}"
        except Exception as e:
            return f"Error generating diagram: {e}"

    async def _arun(self, puml_content: str):
        raise NotImplementedError("PlantUMLTool does not support async")

# Instantiate custom tools
filesystem_tool = FileSystemTool()
plantuml_tool = PlantUMLTool()

# We will keep the ArxivTool from before
from src.tools.arxiv_tool import ArxivTool
arxiv_tool = ArxivTool()

# And the AST tool
from src.tools.ast_tool import ASTAnalysisTool
ast_tool = ASTAnalysisTool()

# And the Domain Expert tool
from src.tools.domain_expert_tool import DomainExpertTool
domain_expert_tool = DomainExpertTool()

# And the Runtime Monitor tool
from src.tools.runtime_monitor_tool import RuntimeMonitorTool
runtime_monitor_tool = RuntimeMonitorTool()

# And the PDF Reader tool
from src.tools.pdf_reader_tool import PDFReaderTool
pdf_reader_tool = PDFReaderTool()

# And the Ingestion tool
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

def load_dynamic_tools():
    """Loads tools dynamically from the src/tools directory."""
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "tools.py", "arxiv_tool.py", "ast_tool.py", "domain_expert_tool.py", "runtime_monitor_tool.py", "pdf_reader_tool.py", "ingestion_tool.py"]:
            module_name = filename[:-3]
            file_path = os.path.join(tools_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Assuming each tool file defines a single tool instance named after the file (e.g., my_tool.py defines my_tool)
            tool_instance = getattr(module, module_name)
            ALL_TOOLS[module_name] = tool_instance

# Load dynamic tools when this module is imported
load_dynamic_tools()
