def test_root_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["data"]["status"] == "online"
    assert json_data["error"] is None


def test_create_patient_success(client):
    payload = {
        "first_name": "Alice",
        "last_name": "Johnson",
        "date_of_birth": "1995-08-25",
        "sex": "Female",
        "phone_number": "(555) 234-5678",
        "email": "alice.johnson@example.com",
        "address_line_1": "789 Pine St",
        "city": "Seattle",
        "state": "WA",
        "zip_code": "98101",
        "preferred_language": "English"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["error"] is None
    data = json_data["data"]
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Johnson"
    assert data["phone_number"] == "5552345678"  # Normalized
    assert data["state"] == "WA"
    assert "patient_id" in data


def test_validation_error_future_dob(client):
    payload = {
        "first_name": "Bob",
        "last_name": "Marley",
        "date_of_birth": "2099-01-01",  # Future date!
        "sex": "Male",
        "phone_number": "5551234567",
        "address_line_1": "101 Beach Rd",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == 422
    assert "Validation failed" in json_data["error"]["message"]


def test_validation_error_invalid_phone(client):
    payload = {
        "first_name": "Bob",
        "last_name": "Marley",
        "date_of_birth": "1980-01-01",
        "sex": "Male",
        "phone_number": "123",  # Invalid short phone!
        "address_line_1": "101 Beach Rd",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["data"] is None
    assert json_data["error"]["code"] == 422


def test_get_patients_and_filtering(client):
    # Insert two patients
    p1 = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "date_of_birth": "1990-03-12",
        "sex": "Male",
        "phone_number": "5551112222",
        "address_line_1": "12 Elm St",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201"
    }
    p2 = {
        "first_name": "Lucy",
        "last_name": "VanPelt",
        "date_of_birth": "1992-06-15",
        "sex": "Female",
        "phone_number": "5553334444",
        "address_line_1": "34 Elm St",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201"
    }
    client.post("/patients", json=p1)
    client.post("/patients", json=p2)

    # List all
    res = client.get("/patients")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2

    # Filter by last name
    res_filter = client.get("/patients?last_name=Brown")
    assert res_filter.status_code == 200
    data = res_filter.json()["data"]
    assert len(data) == 1
    assert data[0]["last_name"] == "Brown"

    # Filter by phone
    res_phone = client.get("/patients?phone_number=5553334444")
    assert res_phone.status_code == 200
    data_phone = res_phone.json()["data"]
    assert len(data_phone) == 1
    assert data_phone[0]["first_name"] == "Lucy"


def test_get_patient_by_id(client):
    p = {
        "first_name": "David",
        "last_name": "Miller",
        "date_of_birth": "1988-12-05",
        "sex": "Male",
        "phone_number": "5559998888",
        "address_line_1": "55 Oak Ave",
        "city": "Denver",
        "state": "CO",
        "zip_code": "80202"
    }
    created = client.post("/patients", json=p).json()["data"]
    patient_id = created["patient_id"]

    # Get existing
    res = client.get(f"/patients/{patient_id}")
    assert res.status_code == 200
    assert res.json()["data"]["patient_id"] == patient_id

    # Get non-existent
    res_404 = client.get("/patients/non-existent-uuid")
    assert res_404.status_code == 404
    assert res_404.json()["data"] is None
    assert res_404.json()["error"]["code"] == 404


def test_update_patient(client):
    p = {
        "first_name": "Eve",
        "last_name": "Davis",
        "date_of_birth": "1991-04-10",
        "sex": "Female",
        "phone_number": "5557776666",
        "address_line_1": "99 Maple Rd",
        "city": "Portland",
        "state": "OR",
        "zip_code": "97201"
    }
    created = client.post("/patients", json=p).json()["data"]
    patient_id = created["patient_id"]

    # Update insurance and phone number
    update_payload = {
        "insurance_provider": "Aetna",
        "insurance_member_id": "AET-998877",
        "phone_number": "5550001111"
    }
    res = client.put(f"/patients/{patient_id}", json=update_payload)
    assert res.status_code == 200
    updated_data = res.json()["data"]
    assert updated_data["insurance_provider"] == "Aetna"
    assert updated_data["phone_number"] == "5550001111"
    assert updated_data["first_name"] == "Eve"  # Preserved original field


def test_soft_delete_patient(client):
    p = {
        "first_name": "Frank",
        "last_name": "Castle",
        "date_of_birth": "1975-02-14",
        "sex": "Male",
        "phone_number": "5554443333",
        "address_line_1": "1 Wall St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10005"
    }
    created = client.post("/patients", json=p).json()["data"]
    patient_id = created["patient_id"]

    # Delete patient
    del_res = client.delete(f"/patients/{patient_id}")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["patient_id"] == patient_id

    # Verify patient is no longer found via GET by ID
    get_res = client.get(f"/patients/{patient_id}")
    assert get_res.status_code == 404

    # Verify patient is excluded from GET list
    list_res = client.get("/patients")
    ids = [item["patient_id"] for item in list_res.json()["data"]]
    assert patient_id not in ids
