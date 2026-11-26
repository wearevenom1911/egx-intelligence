"""DataCedar historical market-data API adapter.

DataCedar is a historical OHLCV source, not a real-time consolidated feed.
API keys are read only from the environment and must never reach the browser.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from egx_intelligence.market_data import MarketBar, MarketDataError

BASE_URL = "https://api.datacedar.com/v3"
ALLOWED_TIMEFRAMES = {"1m", "5m", "15m", "1h", "1d"}


class DataCedarError(RuntimeError):
    """Provider, authentication, or response-contract failure."""


class DataCedarClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = (api_key or os.getenv("DATACEDAR_API_KEY", "")).strip()
        if not self.api_key:
            raise DataCedarError("DATACEDAR_API_KEY is not configured")
        self.session = session or requests.Session()

    def fetch_bars(
        self,
        sid: str,
        *,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
        limit: int = 50000,
        adjustment: str = "raw",
    ) -> list[MarketBar]:
        sid = sid.strip()
        if ":" not in sid or not all(sid.split(":", 1)):
            raise DataCedarError("Symbol must use exchange-qualified form, e.g. egx:COMI")
        if timeframe not in ALLOWED_TIMEFRAMES:
            raise DataCedarError(f"Unsupported timeframe: {timeframe}")
        if not 1 <= limit <= (50000 if timeframe == "1d" else 5000):
            raise DataCedarError("Limit is outside the documented API range")
        if adjustment not in {"raw", "split", "dividend", "all"}:
            raise DataCedarError("Invalid adjustment")

        params: dict[str, Any] = {
            "timeframe": timeframe,
            "order": "asc",
            "limit": limit,
        }
        if start:
            params["from"] = start
        if end:
            params["to"] = end
        if timeframe == "1d":
            params["adjustment"] = adjustment

        try:
            response = self.session.get(
                f"{BASE_URL}/stocks/{sid}/bars",
                params=params,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                },
                timeout=(5, 30),
            )
        except requests.RequestException as exc:
            raise DataCedarError(f"DataCedar network error: {exc.__class__.__name__}") from None

        if response.status_code >= 400:
            try:
                payload = response.json()
                error = payload.get("error", {})
                code = error.get("code", "HTTP_ERROR")
                message = error.get("message", "Provider request failed")
            except (ValueError, AttributeError):
                code, message = "HTTP_ERROR", "Provider request failed"
            raise DataCedarError(f"DataCedar {response.status_code} {code}: {message}")

        try:
            payload = response.json()
        except ValueError:
            raise DataCedarError("DataCedar returned invalid JSON") from None

        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise DataCedarError("Unexpected DataCedar response: data must be an array")
        meta = payload.get("meta") or {}
        attribution = str(meta.get("attribution") or "DataCedar").strip()
        currency = str(meta.get("currency") or "").strip().upper()
        if not currency:
            raise DataCedarError("Provider response is missing meta.currency")

        bars: list[MarketBar] = []
        try:
            for row in payload["data"]:
                timestamp = datetime.fromtimestamp(int(row["ts_ms"]) / 1000, tz=timezone.utc)
                session_date = timestamp.date()
                values = {
                    field: Decimal(str(row[field]))
                    for field in ("open", "high", "low", "close")
                }
                volume = int(row["volume"])
                if any(not value.is_finite() or value <= 0 for value in values.values()):
                    raise MarketDataError("Provider returned non-positive or non-finite OHLC")
                if values["high"] < max(values["open"], values["close"], values["low"]):
                    raise MarketDataError("Provider returned invalid high/low relationship")
                if values["low"] > min(values["open"], values["close"], values["high"]):
                    raise MarketDataError("Provider returned invalid high/low relationship")
                if volume < 0:
                    raise MarketDataError("Provider returned negative volume")
                bars.append(MarketBar(
                    date=session_date,
                    symbol=str(row.get("symbol") or sid.split(":", 1)[1]).upper(),
                    **values,
                    volume=volume,
                    source=attribution,
                    data_timestamp=timestamp,
                    currency=currency,
                ))
        except (KeyError, TypeError, ValueError, InvalidOperation, OverflowError, OSError) as exc:
            raise DataCedarError(
                f"Malformed DataCedar bar payload ({exc.__class__.__name__})"
            ) from None
        except MarketDataError as exc:
            raise DataCedarError(f"Rejected provider data: {exc}") from None
        return bars
