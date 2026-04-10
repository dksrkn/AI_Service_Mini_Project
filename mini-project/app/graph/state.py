from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GlobalState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    final_report_markdown: str
    final_report_pdf_path: str
    workflow_status: str


class SupervisorState(TypedDict):
    next_agent: str
    loop_a_count: int
    loop_b_count: int
    missing_info_log: List[str]
    review_feedback: List[str]
    termination_reason: Optional[str]


class RetrievalState(TypedDict):
    rag_raw_chunks: List[Dict[str, Any]]
    rag_by_topic: Dict[str, List[Dict[str, Any]]]
    web_raw_results: List[Dict[str, Any]]
    normalized_evidence: List[Dict[str, Any]]


class DraftState(TypedDict):
    current_draft: str
    trl_justification: str
    policy_passed: bool
    structure_passed: bool
    evidence_balance_passed: bool


class AgenticWorkflowState(TypedDict):
    global_info: GlobalState
    supervisor_ctrl: SupervisorState
    retrieval_data: RetrievalState
    draft_work: DraftState