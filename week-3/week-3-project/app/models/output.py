from pydantic import BaseModel, Field
from typing import Literal, List, Optional


#--------------------------------------
#  Supporting Models
#--------------------------------------

class ConfidenceScore(BaseModel):
    """Separate model for confidence assessment."""
    level: Literal["High", "Medium", "Low"] = Field(
        default="Medium",
        description="Level of confidence in the research findings"
    )
    reason: str = Field(
        default="",
        description="One sentence explaining the confidence level"
    )
    
class CriticScores(BaseModel):
    accuracy: int = Field(ge=1, le=10)
    completeness: int = Field(ge=1, le=10)
    clarity: int = Field(ge=1, le=10)
    structure: int = Field(ge=1, le=10)
    conciseness: int = Field(ge=1, le=10)

#-------------------------------------------
# Ouput Models
#-------------------------------------------

class SupervisorOutput(BaseModel):
    next_agent: str = Field(
        default_factory=str, 
        description="Next route from researcher, writer, critic, end"
        )
    reason: str = Field(
        default_factory=str, 
        description="one sentence explaining this routing decision"
        )

class ResearcherOutput(BaseModel):
    key_findings: List[str] = Field(
        default_factory=list,
        description="Bullet points — one fact per bullet, attributed to source"
    )
    supporting_details: str = Field(
        default="",
        description="Expanded context for each key finding where necessary"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of all sources used with URLs where available"
    )
    confidence: ConfidenceScore = Field(
        default_factory=ConfidenceScore,
        description="Confidence assessment for the research"
    )

class WriterOutput(BaseModel):
    summary: str = Field(
        default = "", 
        description="2-3 sentences maximum — the single most important takeaway"
        )
    conclusion: str = Field(
        default = "", 
        description="synthesis — what the findings mean, not a repetition of what they said"
        )
    limitations: str = Field(
        default = "", 
        description="what is unknown, uncertain, or outside the scope of available research"
        )
    revison_list: Optional[List[str]] = Field(
        default_factory=list, 
        description="bullet list of what was changed based on critic feedback"
        )

class CriticOutput(BaseModel):
    scores: CriticScores = Field(
        default_factory=CriticScores,
        description="Score of the drafted report out of 10"
    )
    approved: bool = Field(
        default_factory=bool,
        description="Approved the report draft, True/False"
        )
    feedback: List[str] = Field(
        default_factory=list,
        description="feedback for the drafted report"
    )