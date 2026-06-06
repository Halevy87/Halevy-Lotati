import httpx

from app.core.config import settings
from app.services import govmap


def _mock(handler):
    return httpx.MockTransport(handler)


def test_auto_resolved_with_token(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json={"results": [
                {"type": "address", "shape": "POINT(3867584.08 3764952.86)"}
            ]})
        return httpx.Response(200, json={"results": [{"text": "גוש 7136 חלקה 142"}]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "auto_resolved"
    assert res.gush == "7136"
    assert res.chelka == "142"
    assert res.coordinates == {"x": 3867584.08, "y": 3764952.86}
    assert res.method == "rest"


def test_token_not_configured_short_circuits(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [
            {"type": "address", "shape": "POINT(1.0 2.0)"}
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "token_not_configured"
    assert res.coordinates == {"x": 1.0, "y": 2.0}
    assert res.gush is None


def test_address_not_found(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    res = govmap.resolve("עיר", "רחוב", "1", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "not_found"


def test_multi_candidate(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json={"results": [
                {"type": "address", "shape": "POINT(1.0 2.0)"}
            ]})
        return httpx.Response(200, json={"results": [
            {"text": "גוש 7136 חלקה 142"}, {"text": "גוש 7136 חלקה 143"}
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "multi_candidate"
    assert len(res.candidates) == 2


def test_govmap_http_error(monkeypatch):
    monkeypatch.setattr(settings, "govmap_api_token", "test-token")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "govmap_error"
