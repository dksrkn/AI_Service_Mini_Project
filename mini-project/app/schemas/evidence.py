from typing import Literal, Optional
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    technology: str
    competitor: Optional[str] = None
    title: str
    snippet: str
    url: str
    source_type: Literal["web", "rag"]
    stance: Literal["positive", "negative", "neutral"]
    trl_label: str = "판단 불가"
    trl_confidence: Literal["direct", "estimated", "unknown"] = "unknown"
    trl_reason: str = ""