def route_after_supervisor(state):
    return state["supervisor_ctrl"]["next_agent"]


def route_after_policy_check(state):
    feedback = state["supervisor_ctrl"].get("review_feedback", [])
    if feedback:
        return "supervisor"
    return "formatter"