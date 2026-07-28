# Voice AI Patient Registration REST API Backend

A high-performance, robust RESTful backend API built using **FastAPI**, **Pydantic (v2)**, **SQLAlchemy**, and **SQLite** designed specifically to integrate with a **Vapi Voice Agent** for U.S. patient demographic registration.

---

## 📞 Live Voice Demo Details

- **Phone Number to Call**: `+1 (978) 838-4920`
- **Live API Base URL**: `https://f212-110-38-240-181.ngrok-free.app`
- **Interactive API Docs (Swagger)**: `https://f212-110-38-240-181.ngrok-free.app/docs`

---

## 🌟 Features

- **Full RESTful Patient CRUD**:
  - `GET /patients`: List patients (with filtering by `last_name`, `date_of_birth`, `phone_number`).
  - `GET /patients/{id}`: Retrieve patient by UUID.
  - `POST /patients`: Create patient record.
  - `PUT /patients/{id}`: Full/Partial update patient record.
  - `DELETE /patients/{id}`: Soft-delete patient record (sets UTC `deleted_at` timestamp).
- **Strict Server-Side Validation**:
  - Full name checks (1–50 chars, alphabetic + hyphens/apostrophes).
  - Date of Birth validation (valid date, strictly prohibits future dates).
  - U.S. Phone Number normalization (10 digits).
  - Sex enum validation (`Male`, `Female`, `Other`, `Decline to Answer`).
  - U.S. State abbreviation validation (2-letter state codes).
  - ZIP Code validation (5-digit or ZIP+4 format).
- **Consistent Response Envelope**: All endpoints return responses formatted as `{ "data": ..., "error": ... }`.
- **Vapi Integration Routes**:
  - `POST /vapi/check-caller`: Fast duplicate caller lookup by phone number for returning callers.
  - `POST /vapi/tool-call`: Universal Vapi function calling webhook handler.
- **SQLite Persistence & Seeding**: Includes seed script for sample data and table creation handlers.
- **Automated Test Suite**: 100% passing test coverage using Pytest and HTTPX.

---

## 🏗️ Architecture & Data Flow

```
[ Caller (Phone) ]
       │ (Voice Audio)
       ▼
[ Vapi Assistant (STT / LLM / Speech) ]
       │ (HTTP Tool Calls / Webhooks)
       ▼
[ FastAPI REST Service ]
       │ (SQLAlchemy ORM)
       ▼
[ SQLite Database (patients.db) ]
```

---

## 🛠️ Technology Stack & Justification

| Technology | Purpose | Justification |
| :--- | :--- | :--- |
| **FastAPI** | Web Framework | Extremely fast, native async support, automatic OpenAPI (`/docs`) generation, seamless Pydantic integration. |
| **Pydantic v2** | Data Validation | High-performance Rust-backed data validation ensuring strict input sanitization server-side. |
| **SQLite** | Database | Zero-config, lightweight relational DB stored in `patients.db` surviving server restarts. |
| **SQLAlchemy 2.0** | ORM | Expressive database access layer enabling clear model definitions, migrations, and indexing. |
| **Pytest + TestClient** | Testing | Fast unit and integration testing suite verifying endpoint behavior and validation edge cases. |

---

## 🚀 Setup & Execution Instructions

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)

### 2. Virtual Environment & Dependencies
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration:
```env
PORT=8000
DATABASE_URL=sqlite:///./patients.db
APP_ENV=development
```

### 4. Seed Database (Optional)
Populate the SQLite database with 1-2 initial sample patient records:
```bash
python seed.py
```

### 5. Run the Server
Start the local FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`
- ReDoc API Documentation: `http://127.0.0.1:8000/redoc`

---

## 🧪 Running Automated Tests

Run the full Pytest test suite:
```bash
pytest -v
```

---

## 📖 API Documentation & Standards

### Standard JSON Envelope Format

#### Success Response (HTTP 200 / 201)
```json
{
  "data": {
    "patient_id": "a0e28cc1-d180-4b30-9cf8-689bd55339dc",
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "sex": "Female",
    "phone_number": "5551234567",
    "email": "jane.doe@example.com",
    "address_line_1": "123 Main St",
    "address_line_2": "Apt 4B",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94105",
    "insurance_provider": "Blue Cross Blue Shield",
    "insurance_member_id": "BC123456789",
    "preferred_language": "English",
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "5559876543",
    "created_at": "2026-07-28T14:29:44.499885",
    "updated_at": "2026-07-28T14:29:44.499890",
    "deleted_at": null
  },
  "error": null
}
```

#### Validation Error Response (HTTP 422)
```json
{
  "data": null,
  "error": {
    "message": "Validation failed for request body or parameters.",
    "code": 422,
    "details": [
      {
        "field": "date_of_birth",
        "message": "Value error, Date of birth cannot be in the future"
      }
    ]
  }
}
```

---

## 🎙️ Vapi Voice Agent Integration Guide

To connect your Vapi Voice Assistant to this API backend:

### 0. System Prompt / LLM Instruction
A complete, production-ready system prompt adhering to all assessment requirements (natural conversational tone, validation, readback confirmation, optional field opt-in, and duplicate checking) is included in [**VAPI_SYSTEM_PROMPT.md**](file:///home/harris/Desktop/WorkSpace/Vapi%20Voice%20Agent%20Api/VAPI_SYSTEM_PROMPT.md). Copy and paste its contents into your Vapi Assistant System Prompt box.

### 1. Function Tool Definition in Vapi (`create_patient`)
Add a Custom Function Tool in your Vapi Assistant configuration with:
- **Server URL**: `https://your-api-domain.com/patients` (or use `/vapi/tool-call`)
- **Method**: `POST`
- **Parameters**:
```json
{
  "type": "object",
  "properties": {
    "first_name": { "type": "string", "description": "First name of the patient" },
    "last_name": { "type": "string", "description": "Last name of the patient" },
    "date_of_birth": { "type": "string", "description": "Date of birth (YYYY-MM-DD or MM/DD/YYYY)" },
    "sex": { "type": "string", "enum": ["Male", "Female", "Other", "Decline to Answer"] },
    "phone_number": { "type": "string", "description": "10-digit U.S. phone number" },
    "address_line_1": { "type": "string", "description": "Street address" },
    "city": { "type": "string", "description": "City name" },
    "state": { "type": "string", "description": "2-letter U.S. state code (e.g. CA, NY)" },
    "zip_code": { "type": "string", "description": "5-digit U.S. ZIP code" },
    "email": { "type": "string", "description": "Optional email address" },
    "insurance_provider": { "type": "string", "description": "Optional insurance company name" },
    "insurance_member_id": { "type": "string", "description": "Optional insurance member ID" },
    "preferred_language": { "type": "string", "description": "Optional preferred language" }
  },
  "required": ["first_name", "last_name", "date_of_birth", "sex", "phone_number", "address_line_1", "city", "state", "zip_code"]
}
```

### 2. Duplicate Detection Tool (`POST /vapi/check-caller`)
At the beginning of a call, Vapi can send the caller's phone number to `POST /vapi/check-caller`. If `exists: true`, Vapi can prompt:
> *"It looks like we already have a record for Jane Doe. Would you like to update your information instead?"*

---

## ⚖️ Trade-offs & Future Enhancements

- **SQLite vs. PostgreSQL**: SQLite was chosen for zero-config portability within the 3-hour constraint. For high-concurrency production deployments, PostgreSQL with connection pooling (AsyncPG) is recommended.
- **Authentication**: Authentication (JWT / API Key headers) is disabled for local demonstration testing, but can easily be added via FastAPI `HTTPBearer` dependencies.
