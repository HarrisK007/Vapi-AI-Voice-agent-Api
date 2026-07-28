from datetime import datetime, date, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Patient
from app.schemas import PatientCreate, PatientUpdate, normalize_phone


def create_patient(db: Session, patient_in: PatientCreate) -> Patient:
    db_patient = Patient(
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        date_of_birth=patient_in.date_of_birth,
        sex=patient_in.sex.value if hasattr(patient_in.sex, 'value') else patient_in.sex,
        phone_number=patient_in.phone_number,
        email=patient_in.email,
        address_line_1=patient_in.address_line_1,
        address_line_2=patient_in.address_line_2,
        city=patient_in.city,
        state=patient_in.state,
        zip_code=patient_in.zip_code,
        insurance_provider=patient_in.insurance_provider,
        insurance_member_id=patient_in.insurance_member_id,
        preferred_language=patient_in.preferred_language or "English",
        emergency_contact_name=patient_in.emergency_contact_name,
        emergency_contact_phone=patient_in.emergency_contact_phone,
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def get_patient(db: Session, patient_id: str, include_deleted: bool = False) -> Optional[Patient]:
    query = db.query(Patient).filter(Patient.patient_id == patient_id)
    if not include_deleted:
        query = query.filter(Patient.deleted_at.is_(None))
    return query.first()


def list_patients(
    db: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    phone_number: Optional[str] = None,
    include_deleted: bool = False
) -> List[Patient]:
    query = db.query(Patient)
    if not include_deleted:
        query = query.filter(Patient.deleted_at.is_(None))

    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name.strip()}%"))

    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)

    if phone_number:
        clean_phone = normalize_phone(phone_number)
        if clean_phone:
            query = query.filter(Patient.phone_number == clean_phone)

    return query.order_by(Patient.created_at.desc()).all()


def get_patient_by_phone(db: Session, phone_number: str) -> Optional[Patient]:
    clean_phone = normalize_phone(phone_number)
    if not clean_phone:
        return None
    return (
        db.query(Patient)
        .filter(Patient.phone_number == clean_phone, Patient.deleted_at.is_(None))
        .first()
    )


def update_patient(db: Session, db_patient: Patient, patient_in: PatientUpdate) -> Patient:
    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "sex" and hasattr(value, 'value'):
                value = value.value
            setattr(db_patient, field, value)

    db_patient.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_patient)
    return db_patient


def soft_delete_patient(db: Session, db_patient: Patient) -> Patient:
    db_patient.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_patient)
    return db_patient
