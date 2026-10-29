
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(
        min_length=10,
        max_length=2000,
        description="Question to investigate",
    )


class Evidence(BaseModel):
    title: str
    url: str
    content: str
    source_type: str = "web"


class ResearchResponse(BaseModel):
    run_id: str
    question: str
    plan: list[str]
    sources: list[Evidence]
    verification: str
    report: str
    status: str
    evaluation: dict = Field(default_factory=dict)



class IngestResponse(BaseModel):
    filename: str
    chunks_added: int
    status: str
