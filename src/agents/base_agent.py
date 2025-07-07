import logging
from typing import List, Optional
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentCallbackHandler(BaseCallbackHandler):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")

    def on_llm_start(self, *args, **kwargs):
        self.logger.info(f"{self.agent_name} starting LLM call")

    def on_llm_error(self, error: Exception, *args, **kwargs):
        self.logger.error(f"{self.agent_name} LLM error: {str(error)}")

    def on_tool_start(self, tool_name: str, *args, **kwargs):
        self.logger.info(f"{self.agent_name} using tool: {tool_name}")

    def on_tool_error(self, error: Exception, *args, **kwargs):
        self.logger.error(f"{self.agent_name} tool error: {str(error)}")

class BaseAgent:
    def __init__(self, tools: List, system_prompt: str, model_name: str = "llama3", max_retries: int = 3):
        self.logger = logging.getLogger(f"agent.{self.__class__.__name__}")
        self.tools = tools
        self.prompt = PromptTemplate.from_template(system_prompt)
        self.max_retries = max_retries
        self.callback_handler = AgentCallbackHandler(self.__class__.__name__)
        
        # Initialize LLM with retries
        self.llm = self._initialize_llm(model_name)
        
        # Create agent with error handling
        try:
            agent = create_react_agent(self.llm, self.tools, self.prompt)
            self.executor = AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=True,
                callbacks=[self.callback_handler]
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {str(e)}")
            raise

    def _initialize_llm(self, model_name: str) -> Optional[Ollama]:
        for attempt in range(self.max_retries):
            try:
                return Ollama(
                    model=model_name,
                    callbacks=[self.callback_handler]
                )
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} to initialize LLM failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    self.logger.error("All attempts to initialize LLM failed")
                    raise

    def run(self, task: str) -> str:
        """
        Run the agent with error handling and retries.
        
        Args:
            task: The task description or input for the agent
            
        Returns:
            str: The result of the agent's execution
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_retries} to run task")
                result = self.executor.invoke({"input": task})
                self.logger.info("Task completed successfully")
                return result
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
        self.logger.error(f"All {self.max_retries} attempts to run task failed")
        raise last_error
