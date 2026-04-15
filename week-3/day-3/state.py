from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing import Annotated

class supervisoer_state(BaseModel):
    agent_id: str
    query: str
    messages: Annotated[list[str], add_messages]
    next_agent: str

class coder_state(BaseModel):
    query: str
    answer: str

class researcher_state(BaseModel):
    query: str
    answer: str

class general_state(BaseModel):
    query: str
    answer: str