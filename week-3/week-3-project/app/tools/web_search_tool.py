from langchain_tavily import TavilySearch
from langchain.tools import tool

from app.core.prompt_loader import PromptManager

prompt_mng = PromptManager()
tool_description = prompt_mng.load_tool_description("web_search")

@tool(description=tool_description)
async def web_search_tool(user_query: str) -> str:
    """Search the web and return formatted results with sources and favicons."""
    tavily = TavilySearch(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
        include_images=False,          
        include_favicon=False,       
    )
    
    return await tavily.ainvoke({"query": user_query})
    
