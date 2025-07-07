import os
import logging
import json
import importlib
import ast
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ModificationPlan:
    new_tools: Dict[str, str]
    new_agents: Dict[str, str]
    mcp_modifications: list[str]

class SystemModifier:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.tools_dir = os.path.join(base_path, "src", "tools")
        self.agents_dir = os.path.join(base_path, "src", "agents")
        
        # Ensure directories exist
        for dir_path in [self.tools_dir, self.agents_dir]:
            if not os.path.exists(dir_path):
                raise ValueError(f"Required directory not found: {dir_path}")

    def validate_python_code(self, code: str) -> bool:
        """
        Validate that the provided code is syntactically correct Python code.
        
        Args:
            code: The Python code to validate
            
        Returns:
            bool: True if code is valid, False otherwise
            
        Raises:
            SyntaxError: If the code has syntax errors
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error("Syntax error in generated code: %s", str(e))
            raise

    def validate_class_structure(self, code: str, expected_base_class: str) -> bool:
        """
        Validate that the code contains a class inheriting from the expected base class.
        
        Args:
            code: The Python code to validate
            expected_base_class: The name of the expected parent class
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == expected_base_class:
                            return True
            logger.error("Code does not contain a class inheriting from %s", expected_base_class)
            return False
        except Exception as e:
            logger.error("Error validating class structure: %s", str(e))
            raise

    def safe_write_file(self, file_path: str, content: str) -> None:
        """
        Safely write content to a file with proper error handling.
        
        Args:
            file_path: The path to write to
            content: The content to write
            
        Raises:
            IOError: If writing fails
        """
        try:
            # Create a backup if file exists
            if os.path.exists(file_path):
                backup_path = f"{file_path}.bak"
                os.rename(file_path, backup_path)
                logger.info("Created backup at %s", backup_path)

            # Write new content
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info("Successfully wrote to %s", file_path)

        except Exception as e:
            # Restore backup if available
            if os.path.exists(f"{file_path}.bak"):
                os.rename(f"{file_path}.bak", file_path)
                logger.info("Restored backup for %s", file_path)
            logger.error("Failed to write file %s: %s", file_path, str(e))
            raise

    def validate_tool_code(self, code: str) -> bool:
        """Validate that the tool code follows required patterns."""
        try:
            # Check basic syntax
            if not self.validate_python_code(code):
                return False

            # Check inheritance
            if not self.validate_class_structure(code, "BaseTool"):
                return False

            # Check for required methods
            tree = ast.parse(code)
            required_methods = {"_run", "name", "description"}
            found_methods = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    found_methods.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            found_methods.add(item.name)

            missing_methods = required_methods - found_methods
            if missing_methods:
                logger.error("Tool code missing required methods: %s", missing_methods)
                return False

            return True

        except Exception as e:
            logger.error("Error validating tool code: %s", str(e))
            raise

    def validate_agent_code(self, code: str) -> bool:
        """Validate that the agent code follows required patterns."""
        try:
            # Check basic syntax
            if not self.validate_python_code(code):
                return False

            # Check inheritance
            if not self.validate_class_structure(code, "BaseAgent"):
                return False

            # Check for required attributes/structure
            tree = ast.parse(code)
            has_prompt = False
            has_init = False

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.endswith("_PROMPT"):
                            has_prompt = True
                elif isinstance(node, ast.FunctionDef) and node.name == "__init__":
                    has_init = True

            if not (has_prompt and has_init):
                logger.error("Agent code missing required components (prompt or __init__)")
                return False

            return True

        except Exception as e:
            logger.error("Error validating agent code: %s", str(e))
            raise

    def apply_modifications(self, plan: Dict) -> str:
        """
        Apply the system modifications specified in the plan.
        
        Args:
            plan: A dictionary containing new_tools, new_agents, and mcp_modifications
            
        Returns:
            str: A report of the modifications made
            
        Raises:
            ValueError: If the plan is invalid
            IOError: If file operations fail
        """
        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")

        modification_report = []

        try:
            # Handle new tools
            for filename, code in plan.get("new_tools", {}).items():
                if not filename.endswith(".py"):
                    filename = f"{filename}.py"
                file_path = os.path.join(self.tools_dir, filename)
                
                if self.validate_tool_code(code):
                    self.safe_write_file(file_path, code)
                    modification_report.append(f"Added new tool: {filename}")
                else:
                    raise ValueError(f"Invalid tool code in {filename}")

            # Handle new agents
            for filename, code in plan.get("new_agents", {}).items():
                if not filename.endswith(".py"):
                    filename = f"{filename}.py"
                file_path = os.path.join(self.agents_dir, filename)
                
                if self.validate_agent_code(code):
                    self.safe_write_file(file_path, code)
                    modification_report.append(f"Added new agent: {filename}")
                else:
                    raise ValueError(f"Invalid agent code in {filename}")

            # Record MCP modifications (these are applied by the MCP server)
            for mod in plan.get("mcp_modifications", []):
                modification_report.append(f"MCP Modification: {mod}")

            logger.info("Successfully applied all modifications")
            return "\n".join(modification_report)

        except Exception as e:
            error_msg = f"Failed to apply modifications: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def test_new_component(self, file_path: str) -> Optional[str]:
        """
        Test a newly added component by attempting to import it.
        
        Args:
            file_path: Path to the new component
            
        Returns:
            Optional[str]: Error message if import fails, None if successful
        """
        try:
            # Get module name from file path
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Try importing the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.info("Successfully imported new component: %s", module_name)
            return None

        except Exception as e:
            error_msg = f"Failed to import {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg