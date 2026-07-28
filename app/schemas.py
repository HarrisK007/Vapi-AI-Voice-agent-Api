import re
from datetime import date, datetime
from enum import Enum
from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "MP", "AS"
}


class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE_TO_ANSWER = "Decline to Answer"


def normalize_name(v: Optional[str]) -> Optional[str]:
    if v is None:
        return v
    v = v.strip()
    if not v:
        raise ValueError("Name cannot be empty")
    if not re.match(r"^[A-Za-z\s\-\']+$", v):
        raise ValueError("Must contain only alphabetic characters, hyphens, or apostrophes")
    if len(v) > 50:
        raise ValueError("Must be 50 characters or fewer")
    return v


def normalize_phone(v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return None
    # Strip non-digit characters
    digits = re.sub(r"\D", "", v)
    # Handle country code +1
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Must be a valid 10-digit U.S. phone number")
    return digits


class PatientBase(BaseModel):
    first_name: str = Field(..., description="First name of the patient")
    last_name: str = Field(..., description="Last name of the patient")
    date_of_birth: date = Field(..., description="Date of birth (YYYY-MM-DD or MM/DD/YYYY)")
    sex: SexEnum = Field(..., description="Sex/Gender identity")
    phone_number: str = Field(..., description="Valid 10-digit US phone number")
    email: Optional[EmailStr] = Field(None, description="Valid email address")
    address_line_1: str = Field(..., description="Street address")
    address_line_2: Optional[str] = Field(None, description="Apt, suite, or unit")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="2-letter US state code")
    zip_code: str = Field(..., description="5-digit or ZIP+4 code")
    insurance_provider: Optional[str] = Field(None, description="Insurance company name")
    insurance_member_id: Optional[str] = Field(None, description="Insurance member ID")
    preferred_language: Optional[str] = Field("English", description="Preferred spoken language")
    emergency_contact_name: Optional[str] = Field(None, description="Emergency contact full name")
    emergency_contact_phone: Optional[str] = Field(None, description="Emergency contact phone number")

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def validate_names(cls, v: str) -> str:
        res = normalize_name(v)
        if res is None:
            raise ValueError("Field is required")
        return res

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_dob(cls, v: Any) -> date:
        if isinstance(v, date):
            parsed_date = v
        elif isinstance(v, str):
            v = v.strip()
            # Try MM/DD/YYYY first, then YYYY-MM-DD
            try:
                parsed_date = datetime.strptime(v, "%m/%d/%Y").date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("Date of birth must be formatted as YYYY-MM-DD or MM/DD/YYYY")
        else:
            raise ValueError("Invalid date format")

        if parsed_date > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return parsed_date

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, v: Any) -> SexEnum:
        if isinstance(v, SexEnum):
            return v
        if isinstance(v, str):
            val_str = v.strip().lower()
            mapping = {
                "male": SexEnum.MALE,
                "m": SexEnum.MALE,
                "female": SexEnum.FEMALE,
                "f": SexEnum.FEMALE,
                "other": SexEnum.OTHER,
                "decline": SexEnum.DECLINE_TO_ANSWER,
                "decline to answer": SexEnum.DECLINE_TO_ANSWER,
                "declined": SexEnum.DECLINE_TO_ANSWER,
            }
            if val_str in mapping:
                return mapping[val_str]
        raise ValueError("Sex must be one of: Male, Female, Other, Decline to Answer")

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        res = normalize_phone(v)
        if res is None:
            raise ValueError("Phone number is required")
        return res

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return normalize_phone(v)

    @field_validator("state", mode="before")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("State is required")
        st = v.strip().upper()
        if st not in US_STATES:
            raise ValueError("State must be a valid 2-letter U.S. state abbreviation")
        return st

    @field_validator("zip_code", mode="before")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("ZIP code is required")
        z = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", z):
            raise ValueError("ZIP code must be 5 digits (e.g. 12345) or ZIP+4 (e.g. 12345-6789)")
        return z

    @field_validator("city", mode="before")
    @classmethod
    def validate_city(cls, v: str) -> str:
        if not v or not isinstance(v, str) or not v.strip():
            raise ValueError("City is required")
        c = v.strip()
        if len(c) > 100:
            raise ValueError("City must be 100 characters or fewer")
        return c


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def validate_names_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_name(v)

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def validate_dob_opt(cls, v: Any) -> Optional[date]:
        if v is None:
            return v
        return PatientBase.validate_dob(v)

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex_opt(cls, v: Any) -> Optional[SexEnum]:
        if v is None:
            return v
        return PatientBase.validate_sex(v)

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_phone(v)

    @field_validator("emergency_contact_phone", mode="before")
    @classmethod
    def validate_emerg_phone_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_phone(v)

    @field_validator("state", mode="before")
    @classmethod
    def validate_state_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return PatientBase.validate_state(v)

    @field_validator("zip_code", mode="before")
    @classmethod
    def validate_zip_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return PatientBase.validate_zip(v)

    @field_validator("city", mode="before")
    @classmethod
    def validate_city_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return PatientBase.validate_city(v)


class PatientResponse(PatientBase):
    patient_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class APIEnvelope(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[Any] = None
