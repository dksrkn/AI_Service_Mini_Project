from pydantic import BaseModel
from typing import List


class Section(BaseModel):
    title: str
    content: str


class Report(BaseModel):
    summary: str
    background: str
    tech_analysis: List[Section]
    competitor_analysis: List[Section]
    strategy: List[Section]
    limitation: str
    references: List[str]