import json
import re

from langchain_core.messages import SystemMessage, HumanMessage


def invoke_json(llm, system_prompt: str, user_content: str) -> dict:
    """Call an LLM and coerce its reply into a dict, tolerating markdown code fences."""
    messages = [
        SystemMessage(content=system_prompt + "\nRespond with ONLY valid JSON, no prose, no markdown fences."),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(messages)
    text = response.content.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
