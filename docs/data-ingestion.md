# Market data ingestion

## Current implementation

The first ingestion path is a strict CSV import. It is intentionally provider-neutral so the project can accept a licensed EGX export without coupling the research engine to an undocumented endpoint.

Run:

```bash
python -m egx_intelligence.cli --mode validate-csv --input data/imports/quotes.csv --output data/processed/latest.json
```

Required columns:

| Column | Meaning |
|---|---|
| date | Trading session date, ISO `YYYY-MM-DD` |
| symbol | Exchange ticker, e.g. COMI |
| open/high/low/close | Positive OHLC prices |
| volume | Non-negative integer volume |
| source | Provider or export name; never leave blank |
| data_timestamp | ISO-8601 timestamp including UTC offset |
| currency | Optional; defaults to EGP |

The importer rejects malformed timestamps, timezone-naive timestamps, invalid OHLC relationships, negative volume, empty files and duplicate symbol/session rows. It preserves the source and data timestamp in the normalized output.

## Provider selection — not yet configured

- **Official / licensed route:** request EGX market-data access and redistribution terms directly from EGX or an authorized vendor. The official EGX app describes delayed market data; third-party redistribution terms must be confirmed separately.
- **DirectFN:** its public delayed-feed page describes delayed quote fields, top symbols and announcements, and says delivery can be via web service or iframe. Obtain written access, API documentation, credentials and licensing before integrating.
- **Unofficial aggregators:** may be useful for research validation only after due diligence. Do not treat an unofficial service as an exchange-authorized feed or redistribute its data without permission.
- **DataCedar / other paid APIs:** evaluate coverage, symbol mapping, adjustment methodology, freshness, limits and licensing before choosing.

No provider is currently wired to production. Do not publish imported data unless its source, timestamp, delay and usage rights are known.

## Next engineering steps

1. Obtain a sample export and written data-use terms from the selected provider.
2. Implement a provider adapter against its documented schema and authentication method.
3. Add scheduled ingestion, freshness checks, retry/backoff and monitoring.
4. Persist raw source payloads and normalized bars in durable storage.
5. Expose read-only API endpoints and connect the dashboard.
6. Add technical indicators only after the underlying bars pass quality checks.

GitHub Pages is static hosting; it cannot run a persistent Python API or database.
