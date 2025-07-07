
from src.agents.base_agent import BaseAgent
from src.tools.tools import ALL_TOOLS

IDEA_GENERATION_PROMPT = """
You are the Idea Generation Agent. Your task is to take a high-level, potentially vague, project concept and expand it into 3-5 distinct, concrete project ideas.

For each idea, provide:
- A concise project title.
- A brief description (1-2 sentences).
- Key features.
- Suggested core technologies (e.g., Python/FastAPI, React, PostgreSQL).

Your output must be a JSON array of these project ideas.

Example Input: "Build a social media app."
Example Output: 
[
  {
    "title": "Microblogging Platform",
    "description": "A platform for short text posts, followers, and likes.",
    "features": ["User authentication", "Post creation", "Following system", "Like/Comment functionality"],
    "technologies": ["Python/FastAPI", "React", "PostgreSQL"]
  },
  // ... more ideas
]

Begin now. The high-level concept is: {input}
"""

class IdeaGenerationAgent(BaseAgent):
    def __init__(self):
        tools = [ALL_TOOLS["search"]]
        # Ideal model: A model strong in creativity, brainstorming, and understanding diverse domains.
        super().__init__(tools, IDEA_GENERATION_PROMPT, model_name="llama3") 
