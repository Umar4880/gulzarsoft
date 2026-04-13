from models import ArticleInput, ArticleSummary
from custome_reducer import add_summary

from pydantic import Field
from typing import Dict, Annotated, Optional

class ParentState:
    topic: list[str] = Field(default_factory=list, description="topics to process")
    articles: Dict[str, ArticleInput] = Field(default_factory=dict)
    summaries: Annotated[Dict[str, ArticleSummary], add_summary] = Field(default_factory=dict)

class SubgraphState:
    topic: str = Field(default_factory=str)
    title: str = Field(default_factory=str)
    content: Optional[str] = Field(default_factory=str)
    summary: Optional[ArticleSummary] = Field(default_factory=str)