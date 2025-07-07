
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS
import json

PROMPT_OPTIMIZER_PROMPT = """
You are the Prompt Optimizer Agent. Your task is to analyze the retrospection report of a completed job and suggest specific, actionable improvements to the system prompts of the agents involved.

Your analysis should focus on:
- Identifying agents that struggled or contributed to errors (from `retrospection_result.agent_specific_feedback`).
- Suggesting concrete modifications to their system prompts to improve their future performance.

Your output must be a JSON object with the following keys:
- `optimized_prompts`: A dictionary where keys are agent names (e.g., "builder", "designer") and values are the *new, optimized system prompts* for those agents.
- `explanation`: A brief explanation of why these prompt changes are suggested.

Begin now. The retrospection report is: {input}
"""

class PromptOptimizerAgent(BaseAgent):
    def __init__(self):
        tools = [] # This agent primarily reasons over the input context
        # Ideal model: A model strong in meta-learning, understanding prompt engineering, and identifying reasoning failures.
        super().__init__(tools, PROMPT_OPTIMIZER_PROMPT, model_name="llama3") 
