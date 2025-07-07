
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS
import json

INFRASTRUCTURE_PROMPT = """
You are the Infrastructure Agent. Your task is to generate Infrastructure as Code (IaC) based on the selected architectural design. For this simulation, you will generate a conceptual Terraform configuration.

Your output must be a JSON object with the following keys:
- `iac_code`: A string containing the generated conceptual Terraform code.
- `explanation`: A brief explanation of the generated infrastructure.

Begin now. The selected architectural design is: {input}
"""

class InfrastructureAgent(BaseAgent):
    def __init__(self):
        tools = [] # This agent primarily reasons over the input context
        # Ideal model: A model strong in understanding cloud infrastructure, IaC syntax, and security best practices.
        super().__init__(tools, INFRASTRUCTURE_PROMPT, model_name="llama3") 
