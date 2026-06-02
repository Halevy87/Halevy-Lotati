def _case_payload(**overrides):
    payload = {
        "deal_type": "purchase",
        "block": "6941",
        "parcel": "120",
        "sub_parcel": "5",
        "property_address": "רוטשילד 5",
        "property_city": "תל אביב",
        "deal_value_ils": 3200000,
        "primary_client": {
            "role": "buyer",
            "full_name": "ישראל ישראלי",
            "israeli_id": "000000018",  # synthetic/fake
            "phone": "050-0000000",
            "email": "buyer@example.test",
        },
    }
    payload.update(overrides)
    return payload


def test_create_case_returns_case_number_and_logs_activity(client):
    resp = client.post("/api/cases", json=_case_payload())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["case_number"].endswith("-0001")
    assert data["status"] == "intake_pending"
    assert data["property_city"] == "תל אביב"
    assert len(data["parties"]) == 1
    assert data["parties"][0]["israeli_id"] == "000000018"

    activity = client.get(f"/api/cases/{data['id']}/activity").json()
    assert any(a["type"] == "case_opened" for a in activity)


def test_case_numbers_are_sequential(client):
    first = client.post("/api/cases", json=_case_payload()).json()
    second = client.post("/api/cases", json=_case_payload()).json()
    assert first["case_number"].endswith("-0001")
    assert second["case_number"].endswith("-0002")


def test_list_cases_with_pagination_and_status_filter(client):
    for _ in range(3):
        client.post("/api/cases", json=_case_payload())
    resp = client.get("/api/cases", params={"page": 1, "page_size": 2})
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    filtered = client.get("/api/cases", params={"status": "intake_pending"}).json()
    assert filtered["total"] == 3
    none = client.get("/api/cases", params={"status": "signed"}).json()
    assert none["total"] == 0


def test_get_update_delete_case(client):
    created = client.post("/api/cases", json=_case_payload()).json()
    cid = created["id"]

    assert client.get(f"/api/cases/{cid}").status_code == 200

    patched = client.patch(f"/api/cases/{cid}", json={"status": "in_progress"}).json()
    assert patched["status"] == "in_progress"

    assert client.delete(f"/api/cases/{cid}").status_code == 204
    assert client.get(f"/api/cases/{cid}").status_code == 404


def test_get_missing_case_returns_404(client):
    import uuid

    assert client.get(f"/api/cases/{uuid.uuid4()}").status_code == 404


def test_create_case_validation_error_returns_422(client):
    resp = client.post("/api/cases", json={"deal_type": "purchase"})  # missing required fields
    assert resp.status_code == 422
