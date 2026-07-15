from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agent.graph import agent_graph
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    config = {"configurable": {"thread_id": payload.thread_id}}

    prior_state = agent_graph.get_state(config)
    prior_count = len(prior_state.values.get("messages", [])) if prior_state.values else 0

    result = agent_graph.invoke({"messages": [HumanMessage(content=payload.message)]}, config=config)
    new_messages = result["messages"][prior_count:]

    tool_calls = [
        {"tool": m.name, "result": m.content}
        for m in new_messages
        if isinstance(m, ToolMessage)
    ]

    reply = ""
    for m in reversed(result["messages"]):
        if isinstance(m, AIMessage) and m.content:
            reply = m.content
            break

    return ChatResponse(reply=reply, tool_calls=tool_calls, thread_id=payload.thread_id)
