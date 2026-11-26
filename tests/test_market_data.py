from datetime import date
from pathlib import Path

import pytest

from egx_intelligence.market_data import MarketDataError, load_csv


def _write(tmp_path: Path, rows: str) -> Path:
    path = tmp_path / "quotes.csv"
    path.write_text(
        "date,symbol,open,high,low,close,volume,source,data_timestamp,currency\n" + rows,
        encoding="utf-8",
    )
    return path


def test_loads_source_attributed_ohlcv(tmp_path):
    path = _write(
        tmp_path,
        "2026-11-25,comi,50,52,49,51,1200,licensed_export,2026-11-25T14:30:00+02:00,EGP\n",
    )
    bars = load_csv(path)
    assert len(bars) == 1
    assert bars[0].symbol == "COMI"
    assert bars[0].date == date(2026, 11, 25)
    assert bars[0].source == "licensed_export"


def test_rejects_timezone_naive_data_timestamp(tmp_path):
    path = _write(
        tmp_path,
        "2026-11-25,COMI,50,52,49,51,1200,provider,2026-11-25T14:30:00,EGP\n",
    )
    with pytest.raises(MarketDataError, match="timezone"):
        load_csv(path)


def test_rejects_invalid_ohlc_relationship(tmp_path):
    path = _write(
        tmp_path,
        "2026-11-25,COMI,50,48,49,51,1200,provider,2026-11-25T14:30:00+02:00,EGP\n",
    )
    with pytest.raises(MarketDataError, match="high"):
        load_csv(path)


def test_rejects_duplicate_symbol_session(tmp_path):
    row = "2026-11-25,COMI,50,52,49,51,1200,provider,2026-11-25T14:30:00+02:00,EGP\n"
    with pytest.raises(MarketDataError, match="duplicate"):
        load_csv(_write(tmp_path, row + row))
