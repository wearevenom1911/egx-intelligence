"""Validated, source-attributed market data ingestion.

This first adapter deliberately accepts explicit CSV exports only. It never
scrapes an undocumented endpoint or invents a quote when a provider is absent.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_COLUMNS = {
    "date", "symbol", "open", "high", "low", "close", "volume",
    "source", "data_timestamp",
}


class MarketDataError(ValueError):
    """Raised when market data is missing, malformed, or unsafe to use."""


@dataclass(frozen=True, slots=True)
class MarketBar:
    date: date
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    source: str
    data_timestamp: datetime
    currency: str = "EGP"

    def to_dict(self) -> dict[str, object]:
        row = asdict(self)
        row["date"] = self.date.isoformat()
        row["data_timestamp"] = self.data_timestamp.isoformat()
        for key in ("open", "high", "low", "close"):
            row[key] = str(row[key])
        return row


def _decimal(value: str, field: str, line: int) -> Decimal:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise MarketDataError(f"Line {line}: invalid {field}") from None
    if not number.is_finite() or number <= 0:
        raise MarketDataError(f"Line {line}: {field} must be a positive finite number")
    return number


def _parse_row(row: dict[str, str], line: int) -> MarketBar:
    try:
        session_date = date.fromisoformat(row["date"].strip())
        timestamp = datetime.fromisoformat(row["data_timestamp"].strip().replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise MarketDataError(f"Line {line}: date/data_timestamp must be ISO-8601") from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise MarketDataError(f"Line {line}: data_timestamp must include a timezone")
    symbol = row["symbol"].strip().upper()
    source = row["source"].strip()
    currency = (row.get("currency") or "EGP").strip().upper()
    if not symbol or not source:
        raise MarketDataError(f"Line {line}: symbol and source are required")
    if not currency:
        raise MarketDataError(f"Line {line}: currency is required")

    values = {name: _decimal(row[name], name, line) for name in ("open", "high", "low", "close")}
    if values["high"] < max(values["open"], values["close"], values["low"]):
        raise MarketDataError(f"Line {line}: high is below another OHLC value")
    if values["low"] > min(values["open"], values["close"], values["high"]):
        raise MarketDataError(f"Line {line}: low is above another OHLC value")
    try:
        volume = int(row["volume"].strip())
    except (ValueError, AttributeError):
        raise MarketDataError(f"Line {line}: volume must be a non-negative integer") from None
    if volume < 0:
        raise MarketDataError(f"Line {line}: volume must be a non-negative integer")

    return MarketBar(
        date=session_date, symbol=symbol, **values, volume=volume,
        source=source, data_timestamp=timestamp, currency=currency,
    )


def load_csv(path: str | Path) -> list[MarketBar]:
    """Load and validate OHLCV CSV rows, rejecting duplicate symbol/session pairs."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise MarketDataError(f"CSV file not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise MarketDataError("Missing CSV columns: " + ", ".join(sorted(missing)))
        bars: list[MarketBar] = []
        seen: set[tuple[str, date]] = set()
        for line, row in enumerate(reader, start=2):
            bar = _parse_row(row, line)
            key = (bar.symbol, bar.date)
            if key in seen:
                raise MarketDataError(f"Line {line}: duplicate symbol/session {bar.symbol} {bar.date}")
            seen.add(key)
            bars.append(bar)
    if not bars:
        raise MarketDataError("CSV contains no market data rows")
    return bars


def export_json(bars: list[MarketBar], path: str | Path) -> None:
    import json

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "VERIFIED_IMPORT",
        "row_count": len(bars),
        "data_sources": sorted({bar.source for bar in bars}),
        "data_timestamp": max(bar.data_timestamp for bar in bars).isoformat(),
        "bars": [bar.to_dict() for bar in bars],
        "disclaimer": "Imported data; freshness and licensing remain the operator's responsibility.",
    }
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
