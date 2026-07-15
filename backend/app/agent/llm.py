from langchain_groq import ChatGroq

from app.config import settings


def get_llm(temperature: float = 0.2):
    """Primary Groq-hosted model for tool-calling and conversation (gemma2-9b-it)."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
    )


def get_fallback_llm(temperature: float = 0.2):
    """Larger Groq model (llama-3.3-70b-versatile) used for tougher summarization/extraction calls."""
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_fallback_model,
        temperature=temperature,
    )
