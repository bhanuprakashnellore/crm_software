from datetime import date, timedelta

from langchain_core.tools import tool
from sqlalchemy import or_

from app.database import SessionLocal
from app.models import HCP, Interaction, FollowUp, SentimentEnum, ChannelEnum, SourceEnum
from app.agent.llm import get_llm, get_fallback_llm
from app.agent.extraction import invoke_json

EXTRACTION_SYSTEM_PROMPT = """You are a life-science CRM assistant. A pharmaceutical sales representative just \
described an interaction with a healthcare professional (HCP) in free text. Extract a structured record.

Return JSON with EXACTLY these keys:
{
  "hcp_name": string,
  "channel": one of ["in_person", "video_call", "phone_call", "email", "conference"],
  "purpose": short string (e.g. "product_detailing", "sample_drop", "medical_inquiry", "relationship_building"),
  "topics_discussed": [string, ...],
  "products_discussed": [string, ...],
  "materials_shared": [string, ...],
  "samples_distributed": {"ProductName": integer_quantity},
  "sentiment": one of ["positive", "neutral", "negative"],
  "summary": 1-3 sentence professional summary,
  "follow_up_required": boolean,
  "follow_up_notes": string or null
}
If information is not mentioned, use an empty list/object, null, or a sensible default (channel="in_person", \
sentiment="neutral", follow_up_required=false).
"""

COMPLIANCE_SYSTEM_PROMPT = """You are a pharma compliance reviewer. Given notes from an HCP interaction, decide if \
they contain a compliance risk such as: off-label promotion, unsubstantiated efficacy/safety claims, guarantees of \
outcomes, disparaging a named competitor product, or offering something that could be seen as an inducement.

Return JSON: {"flag": boolean, "reason": string or null}
"""

FOLLOWUP_DATE_SYSTEM_PROMPT = """Convert a natural-language follow-up timing description into a concrete ISO date \
(YYYY-MM-DD). Today's date is {today}. Return JSON: {{"due_date": "YYYY-MM-DD"}}
"""

EDIT_SYSTEM_PROMPT = """You are a life-science CRM assistant. A field rep wants to edit an already-logged HCP \
interaction. You are given the CURRENT record as JSON and an EDIT INSTRUCTION in plain English. Return a JSON \
PATCH object containing ONLY the fields that should change, using the same keys/shapes as the current record \
(topics_discussed, products_discussed, materials_shared, samples_distributed, sentiment, purpose, summary, \
raw_notes, follow_up_required, follow_up_date [YYYY-MM-DD], follow_up_notes, channel). Do not include unchanged \
fields.
"""


def _find_or_create_hcp(db, hcp_name: str) -> HCP:
    hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
    if hcp:
        return hcp
    hcp = HCP(name=hcp_name)
    db.add(hcp)
    db.commit()
    db.refresh(hcp)
    return hcp


@tool
def log_interaction(raw_notes: str) -> dict:
    """Log a new HCP interaction from free-text notes (works for both the chat and the form's 'quick notes' path).
    Uses an LLM to extract the HCP name, topics, products, samples distributed, sentiment, and a summary, runs a
    compliance check on the content, creates the HCP if new, and persists the interaction record. Returns the
    created interaction as a dict."""
    db = SessionLocal()
    try:
        llm = get_llm()
        extracted = invoke_json(llm, EXTRACTION_SYSTEM_PROMPT, raw_notes)
        if not extracted:
            fallback_llm = get_fallback_llm()
            extracted = invoke_json(fallback_llm, EXTRACTION_SYSTEM_PROMPT, raw_notes)

        hcp_name = extracted.get("hcp_name") or "Unknown HCP"
        hcp = _find_or_create_hcp(db, hcp_name)

        compliance = invoke_json(llm, COMPLIANCE_SYSTEM_PROMPT, raw_notes)

        channel_value = extracted.get("channel", "in_person")
        if channel_value not in ChannelEnum.__members__:
            channel_value = "in_person"
        sentiment_value = extracted.get("sentiment", "neutral")
        if sentiment_value not in SentimentEnum.__members__:
            sentiment_value = "neutral"

        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_date=date.today(),
            channel=ChannelEnum(channel_value),
            purpose=extracted.get("purpose"),
            topics_discussed=extracted.get("topics_discussed", []),
            products_discussed=extracted.get("products_discussed", []),
            materials_shared=extracted.get("materials_shared", []),
            samples_distributed=extracted.get("samples_distributed", {}),
            sentiment=SentimentEnum(sentiment_value),
            summary=extracted.get("summary"),
            raw_notes=raw_notes,
            follow_up_required=bool(extracted.get("follow_up_required", False)),
            follow_up_notes=extracted.get("follow_up_notes"),
            compliance_flag=bool(compliance.get("flag", False)),
            compliance_notes=compliance.get("reason"),
            source=SourceEnum.chat,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return {
            "id": interaction.id,
            "hcp_id": hcp.id,
            "hcp_name": hcp.name,
            "summary": interaction.summary,
            "sentiment": interaction.sentiment.value,
            "topics_discussed": interaction.topics_discussed,
            "products_discussed": interaction.products_discussed,
            "samples_distributed": interaction.samples_distributed,
            "compliance_flag": interaction.compliance_flag,
            "compliance_notes": interaction.compliance_notes,
            "follow_up_required": interaction.follow_up_required,
        }
    finally:
        db.close()


@tool
def edit_interaction(interaction_id: int, edit_instruction: str) -> dict:
    """Edit an already-logged interaction using a plain-English instruction, e.g. 'change the sentiment to
    positive' or 'add that 20 samples of ProductX were dropped off'. Loads the current record, asks the LLM to
    produce a JSON patch of only the changed fields, applies it, and returns the updated interaction."""
    db = SessionLocal()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return {"error": f"No interaction found with id {interaction_id}"}

        current = {
            "channel": interaction.channel.value,
            "purpose": interaction.purpose,
            "topics_discussed": interaction.topics_discussed,
            "products_discussed": interaction.products_discussed,
            "materials_shared": interaction.materials_shared,
            "samples_distributed": interaction.samples_distributed,
            "sentiment": interaction.sentiment.value,
            "summary": interaction.summary,
            "raw_notes": interaction.raw_notes,
            "follow_up_required": interaction.follow_up_required,
            "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
            "follow_up_notes": interaction.follow_up_notes,
        }

        llm = get_llm()
        user_content = f"CURRENT RECORD:\n{current}\n\nEDIT INSTRUCTION:\n{edit_instruction}"
        patch = invoke_json(llm, EDIT_SYSTEM_PROMPT, user_content)

        if "channel" in patch and patch["channel"] in ChannelEnum.__members__:
            interaction.channel = ChannelEnum(patch["channel"])
        if "sentiment" in patch and patch["sentiment"] in SentimentEnum.__members__:
            interaction.sentiment = SentimentEnum(patch["sentiment"])
        for field in ["purpose", "topics_discussed", "products_discussed", "materials_shared",
                      "samples_distributed", "summary", "raw_notes", "follow_up_required", "follow_up_notes"]:
            if field in patch and patch[field] is not None:
                setattr(interaction, field, patch[field])
        if patch.get("follow_up_date"):
            try:
                interaction.follow_up_date = date.fromisoformat(patch["follow_up_date"])
            except ValueError:
                pass

        db.commit()
        db.refresh(interaction)

        return {
            "id": interaction.id,
            "updated_fields": list(patch.keys()),
            "summary": interaction.summary,
            "sentiment": interaction.sentiment.value,
            "topics_discussed": interaction.topics_discussed,
            "products_discussed": interaction.products_discussed,
            "samples_distributed": interaction.samples_distributed,
            "follow_up_required": interaction.follow_up_required,
            "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else None,
        }
    finally:
        db.close()


@tool
def search_hcp(query: str) -> dict:
    """Search for healthcare professionals by name, specialty, or institution. Returns matching HCP profiles so
    the rep (or the agent) can confirm which HCP a conversation is about before logging or editing anything."""
    db = SessionLocal()
    try:
        like = f"%{query}%"
        results = db.query(HCP).filter(
            or_(HCP.name.ilike(like), HCP.specialty.ilike(like), HCP.institution.ilike(like))
        ).limit(10).all()
        return {
            "matches": [
                {
                    "id": h.id,
                    "name": h.name,
                    "specialty": h.specialty,
                    "institution": h.institution,
                    "engagement_tier": h.engagement_tier,
                }
                for h in results
            ]
        }
    finally:
        db.close()


@tool
def get_interaction_history(hcp_name: str, limit: int = 5) -> dict:
    """Retrieve the most recent logged interactions for a given HCP (by name), so the rep or agent has context
    (e.g. 'what did we discuss with Dr. Rao last time?') before logging a new interaction or planning a visit."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return {"error": f"No HCP found matching '{hcp_name}'"}

        interactions = (
            db.query(Interaction)
            .filter(Interaction.hcp_id == hcp.id)
            .order_by(Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )
        return {
            "hcp_name": hcp.name,
            "history": [
                {
                    "id": i.id,
                    "date": i.interaction_date.isoformat(),
                    "channel": i.channel.value,
                    "purpose": i.purpose,
                    "summary": i.summary,
                    "sentiment": i.sentiment.value,
                    "products_discussed": i.products_discussed,
                }
                for i in interactions
            ],
        }
    finally:
        db.close()


@tool
def schedule_followup(hcp_name: str, timing_description: str, notes: str = "") -> dict:
    """Schedule a follow-up task for an HCP given a natural-language timing description (e.g. 'in 2 weeks',
    'next Monday', '2026-08-01'). Uses the LLM to resolve the date relative to today, then creates a follow-up
    record linked to the HCP."""
    db = SessionLocal()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return {"error": f"No HCP found matching '{hcp_name}'"}

        llm = get_llm()
        today = date.today().isoformat()
        result = invoke_json(
            llm,
            FOLLOWUP_DATE_SYSTEM_PROMPT.format(today=today),
            f"Timing description: {timing_description}",
        )
        due_date_str = result.get("due_date")
        try:
            due_date = date.fromisoformat(due_date_str) if due_date_str else date.today() + timedelta(days=14)
        except ValueError:
            due_date = date.today() + timedelta(days=14)

        follow_up = FollowUp(hcp_id=hcp.id, due_date=due_date, notes=notes)
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)

        return {
            "id": follow_up.id,
            "hcp_name": hcp.name,
            "due_date": follow_up.due_date.isoformat(),
            "notes": follow_up.notes,
        }
    finally:
        db.close()


@tool
def flag_compliance_review(raw_notes: str) -> dict:
    """Run a standalone compliance check on interaction notes to flag potential off-label promotion,
    unsubstantiated claims, competitor disparagement, or inducements — useful for reviewing text before it is
    logged, independent of the log_interaction tool."""
    llm = get_llm()
    result = invoke_json(llm, COMPLIANCE_SYSTEM_PROMPT, raw_notes)
    return {
        "flag": bool(result.get("flag", False)),
        "reason": result.get("reason"),
    }


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    search_hcp,
    get_interaction_history,
    schedule_followup,
    flag_compliance_review,
]
