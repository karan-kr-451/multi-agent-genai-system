
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS
import json

DEPLOYMENT_PROMPT = """
You are the Deployment Agent. Your task is to simulate the deployment of the application to a production-like environment.

Your tasks are:
1.  **Simulate Deployment**: Acknowledge the deployment request.
2.  **Report Status**: Indicate whether the deployment was successful or encountered simulated issues.

Your output must be a JSON object with the following keys:
- `status`: "success" or "failure".
- `message`: A brief message about the deployment outcome.
- `deployment_url`: (Optional) A simulated URL where the application is accessible.

Begin now. The project is ready for deployment. {input}
"""

class DeploymentAgent(BaseAgent):
    def __init__(self):
        tools = [
            # In a real scenario, this would interact with cloud APIs
            ALL_TOOLS["shell"]
        ]
        # Ideal model: A model strong in understanding deployment configurations and cloud platforms.
        super().__init__(tools, DEPLOYMENT_PROMPT, model_name="llama3") 
