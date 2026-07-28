import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, Date, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def current_utc_time():
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(50), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    insurance_member_id: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(50), default="English")
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=current_utc_time)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=current_utc_time, onupdate=current_utc_time)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None, index=True)

    __table_args__ = (
        Index("idx_patient_search", "last_name", "date_of_birth"),
    )

