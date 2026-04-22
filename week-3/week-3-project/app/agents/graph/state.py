# app/agents/graph/state.py
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class CriticScore(BaseModel):
    """Individual dimension scores from the critic."""
    accuracy: int = Field(ge=1, le=10, description="Factual accuracy score")
    completeness: int = Field(ge=1, le=10, description="Coverage of the query")
    clarity: int = Field(ge=1, le=10, description="Ease of understanding")
    structure: int = Field(ge=1, le=10, description="Logical organization")
    conciseness: int = Field(ge=1, le=10, description="Brevity without sacrifice")


class AgentState(BaseModel):
    """
    Shared state for the multi‑agent research pipeline.
    All fields are Optional except `user_query` and `messages`.
    """

    user_query: str = Field(..., description="The original user question or task")

    messages: Annotated[List[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Full conversation history across all agents"
    )

    research_findings: Optional[str] = Field(
        default=None,
        description="Raw research notes gathered by the researcher"
    )

    report_draft: Optional[str] = Field(
        default=None,
        description="The current draft of the report"
    )

    critic_score: Optional[CriticScore] = Field(
        default=None,
        description="Scores assigned by the critic"
    )
    
    critic_feedback: List[str] = Field(
        default_factory=list,
        description="Specific actionable feedback from the critic"
    )
    
    is_approved: bool = Field(
        default=False,
        description="True if the report meets quality threshold"
    )
    
    next_agent: str = Field(
        default="",
        description="The agent to invoke next (set by supervisor)"
    )
    
    route_reason: str = Field(
        default="",
        description="Explanation for the supervisor's routing decision"
    )
    
    iteration_count: int = Field(
        default=0,
        description="Number of agent invocations so far"
    )
    
    last_agent: Optional[str] = Field(
        default=None,
        description="The most recently invoked agent"
    )
    
    report_exists: bool = Field(
        default=False,
        description="True once a draft report has been generated"
    )