from datetime import datetime, timezone

import pytest

from egx_intelligence.data_cedar import DataCedarClient, DataCedarError


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def get(self, url, **kwargs):
        self.kwargs = {"url": url, **kwargs}
        return self.response


def _payload():
    return {
        "data": [{
            "sid": "egx:COMI", "symbol": "COMI", "timeframe": "1Day",
            "ts_ms": "1795608000000", "open": 50, "high": 52,
            "low": 49, "close": 51, "volume": "1200",
        }],
        "pagination": {"count": 1, "has_more": False, "next_cursor": None},
        "meta": {"currency": "EGP", "attribution": "DataCedar source attributed"},
    }


def test_fetches_and_normalizes_historical_bars():
    session = FakeSession(FakeResponse(_payload()))
    client = DataCedarClient("test-key", session=session)
    bars = client.fetch_bars("egx:COMI", start="2026-11-01", end="2026-11-26")
    assert len(bars) == 1
    assert bars[0].symbol == "COMI"
    assert bars[0].currency == "EGP"
    assert bars[0].source == "DataCedar source attributed"
    assert bars[0].data_timestamp.tzinfo == timezone.utc
    assert session.kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert session.kwargs["params"]["timeframe"] == "1d"


def test_requires_api_key():
    with pytest.raises(DataCedarError, match="not configured"):
        DataCedarClient("")


def test_rejects_unqualified_symbol():
    client = DataCedarClient("test-key", session=FakeSession(FakeResponse(_payload())))
    with pytest.raises(DataCedarError, match="exchange-qualified"):
        client.fetch_bars("COMI")


def test_rejects_invalid_timeframe():
    client = DataCedarClient("test-key", session=FakeSession(FakeResponse(_payload())))
    with pytest.raises(DataCedarError, match="Unsupported timeframe"):
        client.fetch_bars("egx:COMI", timeframe="1w")


def test_rejects_missing_currency_metadata():
    payload = _payload()
    payload["meta"].pop("currency")
    client = DataCedarClient("test-key", session=FakeSession(FakeResponse(payload)))
    with pytest.raises(DataCedarError, match="meta.currency"):
        client.fetch_bars("egx:COMI")
