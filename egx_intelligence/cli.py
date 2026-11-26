"""Command-line entry point for scheduled research jobs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from egx_intelligence.data_cedar import DataCedarClient, DataCedarError
from egx_intelligence.market_data import MarketDataError, export_json, load_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EGX Intelligence research runner")
    parser.add_argument("--mode", choices=["daily", "validate-csv", "fetch-datacedar"], default="daily")
    parser.add_argument("--input", help="Source-attributed OHLCV CSV export")
    parser.add_argument("--output", default="data/processed/latest.json")
    parser.add_argument("--symbols", help="Comma-separated provider IDs, e.g. egx:COMI,egx:HRHO")
    parser.add_argument("--timeframe", choices=["1m", "5m", "15m", "1h", "1d"], default="1d")
    parser.add_argument("--from-date", dest="start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", dest="end", help="End date (YYYY-MM-DD)")
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
        print(json.dumps({"status": "VERIFIED_IMPORT", "rows": len(bars), "output": args.output}, indent=2))
        return 0

    if args.mode == "fetch-datacedar":
        if not args.symbols:
            parser.error("--symbols is required with --mode fetch-datacedar")
        try:
            client = DataCedarClient()
            bars = []
            for sid in (item.strip() for item in args.symbols.split(",")):
                if sid:
                    bars.extend(client.fetch_bars(
                        sid, timeframe=args.timeframe, start=args.start, end=args.end,
                    ))
            if not bars:
                print(json.dumps({
                    "status": "NO_DATA",
                    "reason": "Provider returned no bars for the requested symbols and window.",
                }, indent=2))
                return 3
            export_json(bars, args.output)
        except (DataCedarError, MarketDataError) as exc:
            print(json.dumps({"status": "DATA_REJECTED", "reason": str(exc)}, indent=2))
            return 2
        print(json.dumps({
            "status": "HISTORICAL_DATA_IMPORTED",
            "rows": len(bars),
            "symbols": sorted({bar.symbol for bar in bars}),
            "output": args.output,
            "data_type": "historical OHLCV; not real-time quotes",
        }, indent=2))
        return 0

    print(json.dumps({
        "mode": args.mode,
        "status": "NO_TRADE",
        "reason": "No verified daily research pipeline is configured yet.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
