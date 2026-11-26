"""Command-line entry point for scheduled research jobs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EGX Intelligence research runner")
    parser.add_argument("--mode", choices=["daily"], default="daily")
    args = parser.parse_args(argv)
    result = {
        "mode": args.mode,
        "status": "NO_TRADE",
        "reason": "Market data adapters and validation are not configured yet.",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
