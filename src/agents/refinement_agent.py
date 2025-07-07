from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS
import json

REFINEMENT_PROMPT = """
You are the Refinement Agent. Your task is to interpret natural language feedback from the human user and translate it into actionable instructions or modifications for other agents or the project plan.

Your workflow:
1.  **Analyze Feedback**: Understand the user's feedback in the context of the current project state (provided in the input).
2.  **Identify Target**: Determine which agent(s) or part of the project needs to be modified or re-executed based on the feedback.
3.  **Formulate Action**: Generate a precise, machine-readable instruction for the system to act upon. This might involve:
    - Modifying a specific part of the `selected_design` (e.g., changing a database type, adding an API endpoint).
    - Requesting a re-run of a previous agent with modified parameters (e.g., re-run Analyzer with a new focus).
    - Updating the `initial_prompt` to restart the idea generation or architect analysis.

Your output must be a JSON object with the following keys:
- `action_type`: A string indicating the type of action (e.g., "modify_context", "rerun_agent", "update_initial_prompt").
- `modifications`: A dictionary of changes to apply to the `job_context`. For `action_type: "modify_context"`, this would be the specific key-value pairs to update in `job_context.context`. For `action_type: "rerun_agent"`, this might specify which agent to rerun and any new parameters.
- `next_state_suggestion`: The suggested next state for the workflow (e.g., "DESIGNING", "BUILDING", "ARCHITECT_ANALYSIS", "IDEA_GENERATION").
- `explanation`: A brief explanation of how you interpreted the feedback and what action you are taking.

Begin now. The user's feedback is: {input_feedback}. The current job context is: {input_context}
"""

class RefinementAgent(BaseAgent):
    def __init__(self):
        tools = [
            ALL_TOOLS["filesystem"]
        ]
        # Ideal model: A model strong in natural language understanding, intent recognition, and mapping high-level requests to system actions.
        super().__init__(tools, REFINEMENT_PROMPT, model_name="llama3")