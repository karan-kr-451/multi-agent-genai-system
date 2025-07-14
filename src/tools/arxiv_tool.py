import arxiv
from typing import ClassVar
from langchain_community.tools import BaseTool

class ArxivTool(BaseTool):
    name: ClassVar[str] = "ArxivTool"
    description: ClassVar[str] = "Search arxiv papers. Input should be a search query string."

    def _run(self, query: str) -> str:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=5)

        try:
            results = list(client.results(search))
            if not results:
                return "No papers found matching the query."

            output = []
            for paper in results:
                output.append(f"Title: {paper.title}")
                output.append(f"Authors: {', '.join(author.name for author in paper.authors)}")
                output.append(f"Summary: {paper.summary[:300]}...")
                output.append(f"URL: {paper.pdf_url}")
                output.append("-" * 80)

            return "\n".join(output)
        except Exception as e:
            return f"Error searching arxiv: {str(e)}"

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("ArxivTool does not support async")