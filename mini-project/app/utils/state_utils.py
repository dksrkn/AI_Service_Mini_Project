from langchain_core.messages import AIMessage


def append_agent_message(state: dict, agent_name: str, summary: str) -> None:
    global_info = state.setdefault("global_info", {})
    messages = global_info.setdefault("messages", [])
    messages.append(
        AIMessage(
            content=f"[{agent_name}] {summary}",
            name=agent_name,
        )
    )
