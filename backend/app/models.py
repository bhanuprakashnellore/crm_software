import enum
from datetime import datetime, date

from sqlalchemy import String, Text, Integer, Date, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChannelEnum(str, enum.Enum):
    in_person = "in_person"
    video_call = "video_call"
    phone_call = "phone_call"
    email = "email"
    conference = "conference"


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SourceEnum(str, enum.Enum):
    form = "form"
    chat = "chat"


class FollowUpStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class HCP(Base):
    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialty: Mapped[str] = mapped_column(String(150), nullable=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=True)
    npi_number: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    engagement_tier: Mapped[str] = mapped_column(String(20), nullable=True)  # KOL, High, Medium, Low
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="hcp", cascade="all, delete-orphan")
    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), nullable=False)
    rep_name: Mapped[str] = mapped_column(String(150), default="Demo Rep")

    interaction_date: Mapped[date] = mapped_column(Date, default=date.today)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum), default=ChannelEnum.in_person)
    purpose: Mapped[str] = mapped_column(String(150), nullable=True)  # e.g. product_detailing, sample_drop

    topics_discussed: Mapped[list] = mapped_column(JSON, default=list)
    products_discussed: Mapped[list] = mapped_column(JSON, default=list)
    materials_shared: Mapped[list] = mapped_column(JSON, default=list)
    samples_distributed: Mapped[dict] = mapped_column(JSON, default=dict)  # {"ProductX": 10}

    sentiment: Mapped[SentimentEnum] = mapped_column(Enum(SentimentEnum), default=SentimentEnum.neutral)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    raw_notes: Mapped[str] = mapped_column(Text, nullable=True)

    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_date: Mapped[date] = mapped_column(Date, nullable=True)
    follow_up_notes: Mapped[str] = mapped_column(Text, nullable=True)

    compliance_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_notes: Mapped[str] = mapped_column(Text, nullable=True)

    source: Mapped[SourceEnum] = mapped_column(Enum(SourceEnum), default=SourceEnum.form)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp: Mapped["HCP"] = relationship(back_populates="interactions")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcp_id: Mapped[int] = mapped_column(ForeignKey("hcps.id"), nullable=False)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[FollowUpStatus] = mapped_column(Enum(FollowUpStatus), default=FollowUpStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hcp: Mapped["HCP"] = relationship(back_populates="follow_ups")
