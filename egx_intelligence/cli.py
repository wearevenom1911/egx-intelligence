"""Command-line entry point for scheduled research jobs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from egx_intelligence.market_data import MarketDataError, export_json, load_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EGX Intelligence research runner")
    parser.add_argument("--mode", choices=["daily", "validate-csv"], default="daily")
    parser.add_argument("--input", help="Source-attributed OHLCV CSV export")
    parser.add_argument("--output", default="data/processed/latest.json")
    args = parser.parse_args(argv)

    if args.mode == "validate-csv":
        if not args.input:
            parser.error("--input is required with --mode validate-csv")
        try:
            bars = load_csv(args.input)
            export_json(bars, args.output)
        except MarketDataError as exc:
            print(json.dumps({"status": "DATA_REJECTED", "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps({
            "status": "VERIFIED_IMPORT",
            "rows": len(bars),
            "symbols": sorted({bar.symbol for bar in bars}),
            "output": args.output,
        }, indent=2))
        return 0

    result = {
        "mode": args.mode,
        "status": "NO_TRADE",
        "reason": "No verified live market-data provider is configured.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
