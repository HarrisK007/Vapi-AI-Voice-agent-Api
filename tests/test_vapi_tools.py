def test_vapi_check_caller_duplicate(client):
    # Insert existing patient
    p = {
        "first_name": "Sarah",
        "last_name": "Connor",
        "date_of_birth": "1965-05-12",
        "sex": "Female",
        "phone_number": "5558889999",
        "address_line_1": "100 Resistance Way",
        "city": "Los Angeles",
        "state": "CA",
        "zip_code": "90001"
    }
    client.post("/patients", json=p)

    # Check caller with direct JSON
    res = client.post("/vapi/check-caller", json={"phone_number": "(555) 888-9999"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["exists"] is True
    assert data["patient"]["first_name"] == "Sarah"

    # Check non-existent caller
    res_no = client.post("/vapi/check-caller", json={"phone_number": "5550000000"})
    assert res_no.status_code == 200
    assert res_no.json()["data"]["exists"] is False


def test_vapi_tool_call_create_patient(client):
    tool_call_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "create_patient",
                        "arguments": {
                            "first_name": "Grace",
                            "last_name": "Hopper",
                            "date_of_birth": "1906-12-09",
                            "sex": "Female",
                            "phone_number": "5551239876",
                            "address_line_1": "500 Navy Yard",
                            "city": "Arlington",
                            "state": "VA",
                            "zip_code": "22201"
                        }
                    }
                }
            ]
        }
    }

    res = client.post("/vapi/tool-call", json=tool_call_payload)
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) == 1
    assert results[0]["toolCallId"] == "call_abc123"
    assert "saved successfully" in results[0]["result"]
