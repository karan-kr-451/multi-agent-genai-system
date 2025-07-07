from langchain.tools import BaseTool
from PyPDF2 import PdfReader
import os

class PDFReaderTool(BaseTool):
    name = "PDFReaderTool"
    description = "Reads a PDF file from the specified path and extracts its text content. Input is the absolute file path to the PDF."

    def _run(self, file_path: str):
        try:
            # Ensure path is within the allowed workspace for security
            workspace_root = os.path.abspath("workspace")
            abs_file_path = os.path.abspath(file_path)
            if not abs_file_path.startswith(workspace_root):
                return "Error: File path is outside the allowed workspace."

            reader = PdfReader(abs_file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"An error occurred while reading PDF: {e}"

    async def _arun(self, file_path: str):
        raise NotImplementedError("PDFReaderTool does not support async")

# Instantiate the tool
pdf_reader_tool = PDFReaderTool()