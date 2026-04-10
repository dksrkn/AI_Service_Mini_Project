from langchain_core.messages import HumanMessage
from app.graph.workflow import build_workflow


def create_initial_state(query: str):
    return {
        "global_info": {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "final_report_markdown": "",
            "final_report_pdf_path": "",
            "workflow_status": "STARTED",
        },
        "supervisor_ctrl": {
            "next_agent": "supervisor",
            "loop_a_count": 0,
            "loop_b_count": 0,
            "missing_info_log": [],
            "review_feedback": [],
            "termination_reason": None,
        },
        "retrieval_data": {
            "rag_raw_chunks": [],
            "rag_by_topic": {},
            "web_raw_results": [],
            "normalized_evidence": [],
        },
        "draft_work": {
            "current_draft": "",
            "trl_justification": "",
            "policy_passed": False,
            "structure_passed": False,
            "evidence_balance_passed": False,
        },
    }


if __name__ == "__main__":
    query = """
    HBM4, PIM, CXL 등의 관련 최신 반도체 R&D 정보를 수집하고,
    Samsung과 Micron의 기술 성숙도 및 위협 수준을 비교 분석한 뒤,
    R&D 담당자가 바로 참고할 수 있는 기술 전략 분석 보고서를 생성하라.
    """

    app = build_workflow()
    result = app.invoke(create_initial_state(query))

    print("\n===== FINAL STATUS =====")
    print(result["global_info"]["workflow_status"])

    print("\n===== FINAL REPORT (MARKDOWN PREVIEW) =====")
    print(result["global_info"]["final_report_markdown"][:3000])

    print("\n===== FINAL PDF PATH =====")
    print(result["global_info"]["final_report_pdf_path"])