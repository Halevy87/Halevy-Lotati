import uuid

from app.services import govmap


def _case_payload(**overrides):
    payload = {
        "deal_type": "purchase",
        "property_address": "בר יהודה 33",
        "property_city": "בת ים",
        "primary_client": {
            "role": "buyer",
            "full_name": "ישראל ישראלי",
            "israeli_id": "000000018",
        },
    }
    payload.update(overrides)
    return payload


def _make_case(client) -> str:
    return client.post("/api/cases", json=_case_payload()).json()["id"]


def test_create_case_without_block_parcel(client):
    resp = client.post("/api/cases", json=_case_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["block"] is None
    assert body["parcel"] is None


def test_resolve_auto_resolved(client, monkeypatch):
    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(
            status="auto_resolved", gush="7136", chelka="142",
            coordinates={"x": 1.0, "y": 2.0}, resolution_time_ms=12,
        )

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    cid = _make_case(client)

    resp = client.post(f"/api/cases/{cid}/resolve-address", json={})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "auto_resolved"
    assert body["resolved_gush"] == "7136"

    case = client.get(f"/api/cases/{cid}").json()
    assert case["resolved_gush"] == "7136"
    assert case["resolved_chelka"] == "142"
    assert case["block"] == "7136"  # mirrored into empty block
    assert case["property_coordinates"] == {"x": 1.0, "y": 2.0}

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "scraping_completed" for a in activity)


def test_resolve_failed_token_not_configured(client, monkeypatch):
    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(
            status="failed", reason="token_not_configured", coordinates={"x": 1.0, "y": 2.0}
        )

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    cid = _make_case(client)

    resp = client.post(f"/api/cases/{cid}/resolve-address", json={})
    assert resp.status_code == 200  # expected outcome, not a server error
    assert resp.json()["status"] == "failed"

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "scraping_failed" for a in activity)


def test_get_address_resolution_404_then_latest(client, monkeypatch):
    cid = _make_case(client)
    assert client.get(f"/api/cases/{cid}/address-resolution").status_code == 404

    def fake_resolve(city, street, number, **kwargs):
        return govmap.AddressResolutionResult(status="failed", reason="not_found")

    monkeypatch.setattr(govmap, "resolve", fake_resolve)
    client.post(f"/api/cases/{cid}/resolve-address", json={})
    got = client.get(f"/api/cases/{cid}/address-resolution")
    assert got.status_code == 200
    assert got.json()["status"] == "failed"


def test_manual_resolution(client):
    cid = _make_case(client)
    resp = client.patch(
        f"/api/cases/{cid}/address-resolution/manual",
        json={"gush": "7136", "chelka": "142", "tat_chelka": "13"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "manual_entry"
    assert body["method"] == "manual"
    assert body["resolved_tat_chelka"] == "13"

    case = client.get(f"/api/cases/{cid}").json()
    assert case["resolved_gush"] == "7136"
    assert case["block"] == "7136"
    assert case["sub_parcel"] == "13"

    activity = client.get(f"/api/cases/{cid}/activity").json()
    assert any(a["type"] == "note_added" for a in activity)


def test_resolve_missing_case_404(client):
    assert client.post(f"/api/cases/{uuid.uuid4()}/resolve-address", json={}).status_code == 404
