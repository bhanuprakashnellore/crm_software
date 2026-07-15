from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interaction, FollowUp
from app.schemas import InteractionCreate, InteractionUpdate, InteractionOut, FollowUpOut

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.get("", response_model=list[InteractionOut])
def list_interactions(hcp_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Interaction)
    if hcp_id is not None:
        query = query.filter(Interaction.hcp_id == hcp_id)
    return query.order_by(Interaction.interaction_date.desc()).all()


@router.post("", response_model=InteractionOut, status_code=201)
def create_interaction(payload: InteractionCreate, db: Session = Depends(get_db)):
    """Structured-form submission path (no LLM extraction needed — the rep already filled in the fields)."""
    interaction = Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("/{interaction_id}", response_model=InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.patch("/{interaction_id}", response_model=InteractionOut)
def update_interaction(interaction_id: int, payload: InteractionUpdate, db: Session = Depends(get_db)):
    """Structured-form edit path (direct field update, no LLM involved)."""
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interaction, field, value)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}", status_code=204)
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()


@router.get("/follow-ups/all", response_model=list[FollowUpOut])
def list_follow_ups(db: Session = Depends(get_db)):
    return db.query(FollowUp).order_by(FollowUp.due_date).all()
