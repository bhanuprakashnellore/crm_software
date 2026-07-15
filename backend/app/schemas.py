from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models import ChannelEnum, SentimentEnum, SourceEnum, FollowUpStatus


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    npi_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    engagement_tier: Optional[str] = None
    notes: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class InteractionBase(BaseModel):
    hcp_id: int
    rep_name: str = "Demo Rep"
    interaction_date: date = date.today()
    channel: ChannelEnum = ChannelEnum.in_person
    purpose: Optional[str] = None
    topics_discussed: list[str] = []
    products_discussed: list[str] = []
    materials_shared: list[str] = []
    samples_distributed: dict[str, int] = {}
    sentiment: SentimentEnum = SentimentEnum.neutral
    summary: Optional[str] = None
    raw_notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None
    source: SourceEnum = SourceEnum.form


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_date: Optional[date] = None
    channel: Optional[ChannelEnum] = None
    purpose: Optional[str] = None
    topics_discussed: Optional[list[str]] = None
    products_discussed: Optional[list[str]] = None
    materials_shared: Optional[list[str]] = None
    samples_distributed: Optional[dict[str, int]] = None
    sentiment: Optional[SentimentEnum] = None
    summary: Optional[str] = None
    raw_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    follow_up_notes: Optional[str] = None


class InteractionOut(InteractionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    compliance_flag: bool
    compliance_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hcp_id: int
    interaction_id: Optional[int]
    due_date: date
    notes: Optional[str]
    status: FollowUpStatus
    created_at: datetime


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[dict] = []
    thread_id: str
