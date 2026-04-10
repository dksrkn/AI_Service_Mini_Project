from app.utils.state_utils import append_agent_message


def supervisor_node(state):
    print("\n[Supervisor] entered")

    if state["global_info"].get("workflow_status") in {"", None}:
        state["global_info"]["workflow_status"] = "STARTED"

    if not state["retrieval_data"]["rag_raw_chunks"]:
        print("[Supervisor] next -> rag_agent")
        state["supervisor_ctrl"]["next_agent"] = "rag_agent"
        append_agent_message(
            state,
            "supervisor",
            "routing to rag_agent because document evidence has not been collected yet",
        )
        return state

    if not state["retrieval_data"]["web_raw_results"]:
        print("[Supervisor] next -> web_search_agent")
        state["supervisor_ctrl"]["next_agent"] = "web_search_agent"
        append_agent_message(
            state,
            "supervisor",
            "routing to web_search_agent because competitor and market signals are still missing",
        )
        return state

    if not state["draft_work"]["current_draft"]:
        print("[Supervisor] next -> draft_agent")
        state["supervisor_ctrl"]["next_agent"] = "draft_agent"
        append_agent_message(
            state,
            "supervisor",
            "routing to draft_agent to generate the first report draft",
        )
        return state

    feedback = state["supervisor_ctrl"].get("review_feedback", [])
    print(f"[Supervisor] feedback = {feedback}")

    if not feedback:
        print("[Supervisor] next -> formatter")
        state["supervisor_ctrl"]["next_agent"] = "formatter"
        append_agent_message(
            state,
            "supervisor",
            "all review checks passed, sending draft to formatter",
        )
        return state

    evidence_problem = any(
        "교차 근거 부족" in f
        or "웹 검색 근거 부족" in f
        or "RAG 기술 배경 부족" in f
        for f in feedback
    )
    policy_problem = any(
        "TRL" in f
        or "섹션" in f
        or "한계" in f
        or "근거 없는 주장" in f
        or "출처 없음" in f
        or "R&D 전문가" in f
        or "질문과 관련된" in f
        or "과도한 단정" in f
        or "근거 점프" in f
        or "내부 모순" in f
        or "정보 부족" in f
        or "판단 불가" in f
        for f in feedback
    )

    if evidence_problem and state["supervisor_ctrl"]["loop_a_count"] < 2:
        state["supervisor_ctrl"]["loop_a_count"] += 1
        # 편향 정보를 missing_info_log에 저장해서 보완 쿼리 생성에 활용
        for f in feedback:
            if "교차 근거 부족" in f:
                state["supervisor_ctrl"]["missing_info_log"].append(f)
        print(f"[Supervisor] evidence retry -> web_search_agent "
              f"(loop_a_count={state['supervisor_ctrl']['loop_a_count']})")
        state["supervisor_ctrl"]["next_agent"] = "web_search_agent"
        state["global_info"]["workflow_status"] = "IN_REVISION"
        # draft 초기화해서 보완된 web 결과로 재작성하도록
        state["draft_work"]["current_draft"] = ""
        state["supervisor_ctrl"]["review_feedback"] = []
        state["global_info"]["final_report_markdown"] = ""
        state["global_info"]["final_report_pdf_path"] = ""
        append_agent_message(
            state,
            "supervisor",
            f"Loop A retry requested due to evidence quality issues: {feedback}",
        )
        return state

    if policy_problem and state["supervisor_ctrl"]["loop_b_count"] < 2:
        state["supervisor_ctrl"]["loop_b_count"] += 1
        print(f"[Supervisor] policy retry -> draft_agent "
              f"(loop_b_count={state['supervisor_ctrl']['loop_b_count']})")
        state["supervisor_ctrl"]["next_agent"] = "draft_agent"
        state["global_info"]["workflow_status"] = "IN_REVISION"
        state["supervisor_ctrl"]["review_feedback"] = []
        state["global_info"]["final_report_markdown"] = ""
        state["global_info"]["final_report_pdf_path"] = ""
        append_agent_message(
            state,
            "supervisor",
            f"Loop B retry requested due to policy or structure issues: {feedback}",
        )
        return state

    # 최대 재시도 초과 — fallback 처리
    for item in feedback:
        if "정보 부족" in item or "교차 근거 부족" in item:
            state["supervisor_ctrl"]["missing_info_log"].append(item)

    print("[Supervisor] fallback -> formatter")
    state["supervisor_ctrl"]["termination_reason"] = "MAX_RETRY_REACHED_WITH_FALLBACK"
    state["supervisor_ctrl"]["next_agent"] = "formatter"
    state["global_info"]["workflow_status"] = "FALLBACK"
    append_agent_message(
        state,
        "supervisor",
        f"max retries reached, proceeding with fallback formatting. unresolved issues: {feedback}",
    )
    return state
