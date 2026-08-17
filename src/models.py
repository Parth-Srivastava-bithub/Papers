from pydantic import BaseModel, Field
from typing import Optional, List


class Paper(BaseModel):
    """Canonical representation of an academic research paper."""
    id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    published_date: str = ""
    source: str
    paper_url: str
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: int = 0
    categories: List[str] = Field(default_factory=list)
    score: float = 0.0
    matched_topics: List[str] = Field(default_factory=list)

    @property
    def formatted_authors(self) -> str:
        if not self.authors:
            return "Unknown Authors"
        if len(self.authors) <= 3:
            return ", ".join(self.authors)
        return f"{', '.join(self.authors[:3])} et al."


class PipelineStats(BaseModel):
    """Metrics tracking for a single daily run."""
    total_fetched: int = 0
    after_dedup: int = 0
    after_filter: int = 0
    final_selected: int = 0
    sources_used: List[str] = Field(default_factory=list)
    sources_failed: List[str] = Field(default_factory=list)
