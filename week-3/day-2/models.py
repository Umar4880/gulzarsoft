from pydantic import BaseModel, dataclasses
from enum import Enum
from typing import Optional

class ProcessingState(str, Enum):
    success = "success"
    failed = "failed"
    pending = "pending"

class ArticleInput(BaseModel):
    url: str
    title: str
    content: str

class ArticleSummary(BaseModel):
    url: str
    title: str
    summary: str
    key_points: list[str]
    status: ProcessingState = ProcessingState.pending
    error:  Optional[str]
    processing_time: Optional[float] = None