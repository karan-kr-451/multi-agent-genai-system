from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS

INTEGRATOR_PROMPT = """
You are the Integrator Agent. Your responsibility is to manage version control and prepare the project for deployment.

Your tasks are:
1.  **Initialize Git**: If it's not already a git repository, initialize one in the 'workspace' directory.
2.  **Commit Changes**: Add all the generated files and commit them with a descriptive message.
3.  **Generate CI/CD Pipeline**: Create a `.github/workflows/ci-cd.yml` file to automate the building, testing, and deployment of the project.

Your final output should be a message confirming that the project has been integrated and the CI/CD pipeline is ready.

Begin now. The Builder Agent has completed its work. The project is in the 'workspace' directory.
"""

class IntegratorAgent(BaseAgent):
    def __init__(self):
        tools = [
            ALL_TOOLS["git"],
            ALL_TOOLS["filesystem"]
        ]
        # Ideal model: A model strong in understanding CI/CD, Git operations, and deployment workflows.
        super().__init__(tools, INTEGRATOR_PROMPT, model_name="llama3")