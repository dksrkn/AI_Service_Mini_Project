def supervisor_node(state):
    print("\n[Supervisor] entered")

    state["global_info"]["workflow_status"] = "STARTED"

    if not state["retrieval_data"]["rag_raw_chunks"]:
        print("[Supervisor] next -> rag_agent")
        state["supervisor_ctrl"]["next_agent"] = "rag_agent"
        return state

    if not state["retrieval_data"]["web_raw_results"]:
        print("[Supervisor] next -> web_search_agent")
        state["supervisor_ctrl"]["next_agent"] = "web_search_agent"
        return state

    if not state["draft_work"]["current_draft"]:
        print("[Supervisor] next -> draft_agent")
        state["supervisor_ctrl"]["next_agent"] = "draft_agent"
        return state

    feedback = state["supervisor_ctrl"].get("review_feedback", [])
    print(f"[Supervisor] feedback = {feedback}")

    if not feedback:
        print("[Supervisor] next -> formatter")
        state["supervisor_ctrl"]["next_agent"] = "formatter"
        return state

    evidence_problem = any("교차 근거 부족" in f or "정보 부족" in f for f in feedback)
    policy_problem = any(
        "TRL" in f or "섹션" in f or "간접 지표" in f or "한계" in f
        for f in feedback
    )

    if evidence_problem and state["supervisor_ctrl"]["loop_a_count"] < 2:
        state["supervisor_ctrl"]["loop_a_count"] += 1
        print("[Supervisor] evidence retry -> web_search_agent")
        state["supervisor_ctrl"]["next_agent"] = "web_search_agent"
        state["global_info"]["workflow_status"] = "IN_REVISION"
        return state

    if policy_problem and state["supervisor_ctrl"]["loop_b_count"] < 2:
        state["supervisor_ctrl"]["loop_b_count"] += 1
        print("[Supervisor] policy retry -> draft_agent")
        state["supervisor_ctrl"]["next_agent"] = "draft_agent"
        state["global_info"]["workflow_status"] = "IN_REVISION"
        return state

    for item in feedback:
        if "정보 부족" in item or "교차 근거 부족" in item:
            state["supervisor_ctrl"]["missing_info_log"].append(item)

    print("[Supervisor] fallback -> formatter")
    state["supervisor_ctrl"]["termination_reason"] = "MAX_RETRY_REACHED_WITH_FALLBACK"
    state["supervisor_ctrl"]["next_agent"] = "formatter"
    state["global_info"]["workflow_status"] = "FALLBACK"
    return state