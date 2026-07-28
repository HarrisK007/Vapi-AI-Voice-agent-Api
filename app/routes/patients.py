from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=schemas.APIEnvelope[List[schemas.PatientResponse]])
def get_patients(
    last_name: Optional[str] = Query(None, description="Filter by last name (case-insensitive substring)"),
    date_of_birth: Optional[date] = Query(None, description="Filter by date of birth (YYYY-MM-DD)"),
    phone_number: Optional[str] = Query(None, description="Filter by 10-digit phone number"),
    db: Session = Depends(get_db)
):
    patients = crud.list_patients(
        db,
        last_name=last_name,
        date_of_birth=date_of_birth,
        phone_number=phone_number
    )
    return {"data": patients, "error": None}


@router.get("/{id}", response_model=schemas.APIEnvelope[schemas.PatientResponse])
def get_patient_by_id(id: str, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id=id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' was not found"
        )
    return {"data": patient, "error": None}


@router.post("", response_model=schemas.APIEnvelope[schemas.PatientResponse], status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: schemas.PatientCreate, db: Session = Depends(get_db)):
    created_patient = crud.create_patient(db, patient_in)
    return {"data": created_patient, "error": None}


@router.put("/{id}", response_model=schemas.APIEnvelope[schemas.PatientResponse])
def update_patient(id: str, patient_in: schemas.PatientUpdate, db: Session = Depends(get_db)):
    db_patient = crud.get_patient(db, patient_id=id)
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' was not found"
        )
    updated_patient = crud.update_patient(db, db_patient, patient_in)
    return {"data": updated_patient, "error": None}


@router.delete("/{id}", response_model=schemas.APIEnvelope[dict])
def delete_patient(id: str, db: Session = Depends(get_db)):
    db_patient = crud.get_patient(db, patient_id=id)
    if not db_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{id}' was not found"
        )
    crud.soft_delete_patient(db, db_patient)
    return {
        "data": {
            "message": "Patient record soft-deleted successfully",
            "patient_id": id
        },
        "error": None
    }
