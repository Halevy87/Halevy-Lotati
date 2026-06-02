def _make_case(client):
    payload = {
        "block": "6941",
        "parcel": "120",
        "property_address": "רוטשילד 5",
        "property_city": "תל אביב",
    }
    return client.post("/api/cases", json=payload).json()


def test_add_and_list_parties(client):
    case = _make_case(client)
    cid = case["id"]

    resp = client.post(
        f"/api/cases/{cid}/parties",
        json={"role": "seller", "full_name": "משה כהן", "israeli_id": "000000026"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["identity_check_status"] == "pending"

    parties = client.get(f"/api/cases/{cid}/parties").json()
    assert len(parties) == 1
    assert parties[0]["full_name"] == "משה כהן"


def test_update_party_status(client):
    case = _make_case(client)
    cid = case["id"]
    party = client.post(
        f"/api/cases/{cid}/parties",
        json={"role": "buyer", "full_name": "דנה לוי", "israeli_id": "000000034"},
    ).json()

    updated = client.patch(
        f"/api/cases/{cid}/parties/{party['id']}",
        json={"identity_check_status": "clean"},
    ).json()
    assert updated["identity_check_status"] == "clean"


def test_parties_on_missing_case_404(client):
    import uuid

    assert client.get(f"/api/cases/{uuid.uuid4()}/parties").status_code == 404
