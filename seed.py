import datetime
from app.database import SessionLocal, init_db
from app import crud, schemas


def seed_database():
    init_db()
    db = SessionLocal()
    try:
        existing = crud.list_patients(db)
        if existing:
            print(f"Database already contains {len(existing)} patient(s). Skipping seed.")
            return

        sample_patients = [
            schemas.PatientCreate(
                first_name="Jane",
                last_name="Doe",
                date_of_birth=datetime.date(1990, 5, 15),
                sex=schemas.SexEnum.FEMALE,
                phone_number="5551234567",
                email="jane.doe@example.com",
                address_line_1="123 Main St",
                address_line_2="Apt 4B",
                city="San Francisco",
                state="CA",
                zip_code="94105",
                insurance_provider="Blue Cross Blue Shield",
                insurance_member_id="BC123456789",
                preferred_language="English",
                emergency_contact_name="John Doe",
                emergency_contact_phone="5559876543"
            ),
            schemas.PatientCreate(
                first_name="Robert",
                last_name="Smith",
                date_of_birth=datetime.date(1985, 11, 20),
                sex=schemas.SexEnum.MALE,
                phone_number="5559876543",
                email="robert.smith@example.com",
                address_line_1="456 Market St",
                city="Austin",
                state="TX",
                zip_code="78701",
                preferred_language="English"
            )
        ]

        for patient_in in sample_patients:
            created = crud.create_patient(db, patient_in)
            print(f"Seeded patient: {created.first_name} {created.last_name} (ID: {created.patient_id})")

        print("Database seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
