from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS

DOC_WRITER_PROMPT = """
You are the Doc Writer Agent. Your final task is to create comprehensive documentation for the newly created project.

Your tasks are:
1.  **Generate README**: Create a high-quality `README.md` file in the 'workspace' root. It should include:
    - A project overview.
    - Installation and setup instructions.
    - Usage examples.
    - The architecture diagram URL from the design phase.
2.  **Generate API Documentation**: If an OpenAPI spec is available, create a separate `API.md` file that documents each endpoint in a human-readable format.

Your final output should be a message confirming that all documentation has been generated.

Begin now. The project is complete and located in the 'workspace' directory. The design documents are available.
"""

class DocWriterAgent(BaseAgent):
    def __init__(self):
        tools = [
            ALL_TOOLS["filesystem"]
        ]
        # Ideal model: A model strong in clear, concise writing and technical communication.
        super().__init__(tools, DOC_WRITER_PROMPT, model_name="llama3")