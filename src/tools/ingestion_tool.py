import os
import shutil
from langchain.tools import BaseTool

class IngestionTool(BaseTool):
    name = "IngestionTool"
    description = "Copies a file from a specified absolute source path on the user's system to the project workspace. Input is a JSON object with 'source_path' (absolute path) and 'destination_filename' (filename in workspace)."

    def _run(self, tool_input: str):
        import json
        try:
            params = json.loads(tool_input)
            source_path = params.get("source_path")
            destination_filename = params.get("destination_filename")

            if not source_path or not destination_filename:
                return "Error: 'source_path' and 'destination_filename' are required."

            if not os.path.isabs(source_path):
                return "Error: 'source_path' must be an absolute path."

            if not os.path.exists(source_path):
                return f"Error: Source file not found at {source_path}"

            workspace_root = os.path.abspath("workspace")
            os.makedirs(workspace_root, exist_ok=True)
            
            destination_path = os.path.join(workspace_root, destination_filename)
            
            # Security check: Ensure the destination is within the workspace
            if not os.path.abspath(destination_path).startswith(workspace_root):
                return "Error: Attempted to write outside the allowed workspace."

            shutil.copy(source_path, destination_path)
            return f"Successfully copied {source_path} to {destination_path}"

        except Exception as e:
            return f"An error occurred during file ingestion: {e}"

    async def _arun(self, tool_input: str):
        raise NotImplementedError("IngestionTool does not support async")

# Instantiate the tool
ingestion_tool = IngestionTool()