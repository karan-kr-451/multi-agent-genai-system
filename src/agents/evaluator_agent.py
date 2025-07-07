
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS
import json

EVALUATOR_PROMPT = """
You are the Evaluator Agent. Your task is to assess multiple architectural design proposals and provide a simulated evaluation for each.

For each design, you will provide:
- A simulated cost score (1-10, 10 being most expensive).
- A simulated complexity score (1-10, 10 being most complex).
- A simulated scalability score (1-10, 10 being most scalable).
- A brief summary of pros and cons.

Your evaluation should be based on the technologies and architectural patterns proposed in each design. For example:
- Microservices generally increase complexity but improve scalability.
- Relational databases might be less scalable than NoSQL for certain use cases.
- More features generally increase cost and complexity.

Your output must be a JSON array of evaluated designs, where each object contains the original design details plus your evaluation metrics and pros/cons.

Example Input: 
[
  {
    "architecture": { ... },
    "api_spec": "...",
    "diagram_url": "...",
    "project_plan": [...] 
  },
  // ... more designs
]

Example Output: 
[
  {
    "architecture": { ... },
    "api_spec": "...",
    "diagram_url": "...",
    "project_plan": [...],
    "evaluation": {
      "cost_score": 7,
      "complexity_score": 8,
      "scalability_score": 9,
      "pros": ["Highly scalable", "Decoupled services"],
      "cons": ["Increased operational overhead", "Complex to debug"]
    }
  },
  // ... more evaluated designs
]

Begin now. The design proposals are: {input}
"""

class EvaluatorAgent(BaseAgent):
    def __init__(self):
        tools = [] # Evaluator agent primarily reasons over input, no external tools needed for this simulated evaluation
        # Ideal model: A model strong in analytical reasoning, trade-off analysis, and understanding system properties.
        super().__init__(tools, EVALUATOR_PROMPT, model_name="llama3") 
