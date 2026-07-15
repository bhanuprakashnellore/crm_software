from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from app.agent.llm import get_llm
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are Field Copilot, an AI assistant embedded in a pharmaceutical CRM used by field sales \
representatives to manage relationships with healthcare professionals (HCPs).

You help reps log interactions, edit past interactions, look up HCPs, review interaction history, and schedule \
follow-ups — entirely through conversation, using the tools available to you. Prefer calling a tool over asking \
the rep to use the form. When a rep describes an interaction in free text, call log_interaction with their raw \
text. When they want to change something already logged, call edit_interaction. Always confirm back to the rep, \
briefly and professionally, what you did (e.g. which HCP, what was logged, any compliance flag raised).

Be concise. You are a professional tool for busy field reps, not a chatty assistant.
"""

llm_with_tools = get_llm().bind_tools(ALL_TOOLS)


def agent_node(state: MessagesState):
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def build_graph():
    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=MemorySaver())


agent_graph = build_graph()
