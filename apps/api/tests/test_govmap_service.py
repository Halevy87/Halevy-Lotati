import httpx

from app.services import govmap


def _mock(handler):
    return httpx.MockTransport(handler)


# A square parcel polygon (EPSG:3857-ish) that contains the point (100, 100).
_SQUARE = [[[[0, 0], [200, 0], [200, 200], [0, 200], [0, 0]]]]
# A square far away that does NOT contain (100, 100).
_FAR_SQUARE = [[[[1000, 1000], [1200, 1000], [1200, 1200], [1000, 1200], [1000, 1000]]]]


def _parcel_feature(gush, chelka, coords=_SQUARE):
    return {
        "type": "Feature",
        "geometry": {"type": "MultiPolygon", "coordinates": coords},
        "properties": {"gush_num": gush, "parcel": chelka, "locality_name": "בת ים"},
    }


def _address_response(x=100.0, y=100.0):
    return {"results": [{"type": "address", "shape": f"POINT({x} {y})"}]}


def test_auto_resolved():
    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json=_address_response())
        # WMS GetFeatureInfo
        return httpx.Response(200, json={"type": "FeatureCollection",
                                         "features": [_parcel_feature(7137, 157)]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "auto_resolved"
    assert res.gush == "7137"
    assert res.chelka == "157"
    assert res.coordinates == {"x": 100.0, "y": 100.0}
    assert res.method == "rest"


def test_picks_containing_parcel_when_multiple_returned():
    # WMS returns the target parcel (contains the point) plus a neighbour that does not.
    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json=_address_response())
        return httpx.Response(200, json={"type": "FeatureCollection", "features": [
            _parcel_feature(7137, 157, _SQUARE),        # contains (100,100)
            _parcel_feature(7137, 158, _FAR_SQUARE),    # does not
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "auto_resolved"
    assert (res.gush, res.chelka) == ("7137", "157")


def test_address_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    res = govmap.resolve("עיר", "רחוב", "1", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "not_found"


def test_no_parcel_at_point():
    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json=_address_response())
        return httpx.Response(200, json={"type": "FeatureCollection", "features": []})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "not_found"


def test_multi_candidate_when_none_contain_point():
    # Point on a boundary: two distinct parcels returned, neither containing the point.
    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json=_address_response())
        return httpx.Response(200, json={"type": "FeatureCollection", "features": [
            _parcel_feature(7137, 157, _FAR_SQUARE),
            _parcel_feature(7137, 158, _FAR_SQUARE),
        ]})

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "multi_candidate"
    assert len(res.candidates) == 2
    assert {"gush": "7137", "chelka": "157"} in res.candidates


def test_govmap_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if "autocomplete" in str(request.url):
            return httpx.Response(200, json=_address_response())
        return httpx.Response(500, text="boom")

    res = govmap.resolve("בת ים", "בר יהודה", "33", transport=_mock(handler))
    assert res.status == "failed"
    assert res.reason == "govmap_error"
    assert res.error
