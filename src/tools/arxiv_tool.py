import arxiv
from langchain.tools import BaseTool
import json

class ArxivTool(BaseTool):
    name = "ArxivSearch"
    description = "Searches arXiv for academic papers on a given topic."

    def _run(self, query: str):
        try:
            search = arxiv.Search(
                query=query,
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results = []
            for result in search.results():
                results.append({
                    "title": result.title,
                    "summary": result.summary,
                    "url": result.pdf_url
                })
            return json.dumps(results)
        except Exception as e:
            return f"An error occurred: {e}"

    async def _arun(self, query: str):
        raise NotImplementedError("ArxivTool does not support async")

# Instantiate the tool
arxiv_tool = ArxivTool()