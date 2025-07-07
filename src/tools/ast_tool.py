import ast
from langchain.tools import BaseTool

class ASTAnalysisTool(BaseTool):
    name = "ASTAnalysisTool"
    description = "Analyzes a Python code string using Abstract Syntax Trees (AST) to find functions, classes, and imports. Input is a JSON object with 'action' and 'code'. Actions: 'find_functions', 'find_classes', 'find_imports'."

    def _run(self, tool_input: str):
        import json
        try:
            params = json.loads(tool_input)
            action = params.get("action")
            code = params.get("code", "")

            tree = ast.parse(code)
            
            if action == "find_functions":
                functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                return json.dumps(functions)
            
            elif action == "find_classes":
                classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                return json.dumps(classes)

            elif action == "find_imports":
                imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
                return json.dumps(imports)

            else:
                return "Error: Invalid action specified for ASTAnalysisTool."

        except Exception as e:
            return f"An error occurred during AST analysis: {e}"

    async def _arun(self, tool_input: str):
        raise NotImplementedError("ASTAnalysisTool does not support async")

# Instantiate the tool
ast_tool = ASTAnalysisTool()