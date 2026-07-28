import json
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/vapi", tags=["Vapi Voice Integration"])


@router.get("/check-caller", response_model=schemas.APIEnvelope[dict])
def get_check_caller_info():
    return {
        "data": {
            "endpoint": "/vapi/check-caller",
            "status": "online",
            "method_required": "POST",
            "message": "Vapi Duplicate Caller Checker endpoint is active. Send POST requests with phone_number parameter."
        },
        "error": None
    }


@router.post("/check-caller", response_model=schemas.APIEnvelope[dict])
def check_caller(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Check if an incoming caller's phone number exists in the patient database.
    Supports either direct JSON `{"phone_number": "..."}` or Vapi call event object.
    """
    phone_number = payload.get("phone_number")
    if not phone_number and "message" in payload:
        call_obj = payload.get("message", {}).get("call", {})
        customer_obj = call_obj.get("customer", {})
        phone_number = customer_obj.get("number")

    if not phone_number:
        return {
            "data": {"exists": False, "patient": None, "message": "No phone number provided"},
            "error": None
        }

    patient = crud.get_patient_by_phone(db, phone_number)
    if patient:
        return {
            "data": {
                "exists": True,
                "patient": {
                    "patient_id": patient.patient_id,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "phone_number": patient.phone_number,
                    "date_of_birth": str(patient.date_of_birth),
                    "city": patient.city,
                    "state": patient.state
                },
                "prompt_suggestion": f"Existing record found for {patient.first_name} {patient.last_name}."
            },
            "error": None
        }

    return {
        "data": {"exists": False, "patient": None, "message": "No existing record found for this number"},
        "error": None
    }


@router.get("/tool-call", response_model=schemas.APIEnvelope[dict])
def get_tool_call_info():
    return {
        "data": {
            "endpoint": "/vapi/tool-call",
            "status": "online",
            "method_required": "POST",
            "message": "Vapi Universal Tool Webhook endpoint is active. Vapi Voice Agent sends POST tool calls to this endpoint."
        },
        "error": None
    }


@router.post("/tool-call")
def handle_vapi_tool_call(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Generic tool call webhook receiver for Vapi custom functions.
    Handles function tool calls sent from Vapi Voice Assistant.
    """
    # Extract tool calls from various Vapi payload formats
    message = payload.get("message", {}) if isinstance(payload.get("message"), dict) else {}
    tool_calls = message.get("toolCalls", []) or message.get("toolCallList", [])

    if not tool_calls and "toolWithToolCallList" in message:
        tool_calls = [t.get("toolCall") for t in message.get("toolWithToolCallList", []) if t.get("toolCall")]

    if not tool_calls and "toolCall" in payload:
        tool_calls = [payload["toolCall"]]

    if not tool_calls and ("function" in payload or "name" in payload or "first_name" in payload):
        func_name = payload.get("name") or (payload.get("function", {}).get("name") if isinstance(payload.get("function"), dict) else None) or "create_patient"
        args = payload.get("arguments") or (payload.get("function", {}).get("arguments") if isinstance(payload.get("function"), dict) else None) or payload
        tool_calls = [{
            "id": payload.get("id", "tool_call_1"),
            "function": {
                "name": func_name,
                "arguments": args
            }
        }]

    results = []
    last_result_data: Optional[Dict[str, Any]] = None

    for tool in tool_calls:
        tool_id = tool.get("id")
        function_obj = tool.get("function", {})
        func_name = function_obj.get("name")
        args = function_obj.get("arguments", {})

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        result_data: Dict[str, Any] = {}

        try:
            if func_name == "create_patient":
                patient_in = schemas.PatientCreate(**args)
                created = crud.create_patient(db, patient_in)
                result_data = {
                    "status": "success",
                    "patient_id": created.patient_id,
                    "first_name": created.first_name,
                    "last_name": created.last_name,
                    "date_of_birth": str(created.date_of_birth),
                    "sex": created.sex,
                    "phone_number": created.phone_number,
                    "address_line_1": created.address_line_1,
                    "address_line_2": created.address_line_2,
                    "city": created.city,
                    "state": created.state,
                    "zip_code": created.zip_code,
                    "email": created.email,
                    "insurance_provider": created.insurance_provider,
                    "insurance_member_id": created.insurance_member_id,
                    "preferred_language": created.preferred_language,
                    "emergency_contact_name": created.emergency_contact_name,
                    "emergency_contact_phone": created.emergency_contact_phone,
                    "message": f"Patient registration saved successfully for {created.first_name} {created.last_name}."
                }
            elif func_name == "check_caller_duplicate":
                phone = args.get("phone_number")
                existing = crud.get_patient_by_phone(db, phone) if phone else None
                if existing:
                    result_data = {
                        "exists": True,
                        "patient_id": existing.patient_id,
                        "first_name": existing.first_name,
                        "last_name": existing.last_name
                    }
                else:
                    result_data = {"exists": False}
            elif func_name == "update_patient":
                patient_id = args.get("patient_id")
                if not patient_id or not isinstance(patient_id, str):
                    result_data = {"status": "error", "message": "Patient ID is required"}
                else:
                    db_patient = crud.get_patient(db, patient_id)
                    if not db_patient:
                        result_data = {"status": "error", "message": "Patient not found"}
                    else:
                        update_schema = schemas.PatientUpdate(**args)
                        updated = crud.update_patient(db, db_patient, update_schema)
                        result_data = {
                            "status": "success",
                            "patient_id": updated.patient_id,
                            "message": "Patient record updated successfully."
                        }
            else:
                result_data = {"status": "error", "message": f"Unknown function '{func_name}'"}

            last_result_data = result_data
            results.append({
                "toolCallId": tool_id,
                "result": json.dumps(result_data) if isinstance(result_data, dict) else str(result_data)
            })
        except Exception as e:
            results.append({
                "toolCallId": tool_id,
                "result": f"Error processing tool call: {str(e)}"
            })

    response_dict: Dict[str, Any] = {"results": results}
    if len(tool_calls) == 1 and last_result_data:
        response_dict.update(last_result_data)

    return response_dict
