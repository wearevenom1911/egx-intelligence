# EGX Intelligence

A personal market-research and risk-management dashboard for the Egyptian Exchange (EGX) and selected US-listed companies.

## Project principles

- Research and alerts only: no broker login, order placement, or automatic trading.
- Every recommendation must include its data timestamp, source, thesis, invalidation level, risk/reward, and confidence limitations.
- Never fabricate live prices or imply guaranteed returns.
- Telegram posts are treated as untrusted source material and independently checked against market data.
- Secrets and Telegram session files must never be committed.

## Initial scope

1. Collect and archive Telegram channel posts from channels the account is authorized to view.
2. Normalize and track stock mentions and recommendations.
3. Add independently sourced market data for EGX and US equities.
4. Build technical/fundamental research and position-sizing modules.
5. Publish a dashboard and daily research report.
6. Backtest and paper-trade before considering any real-money decisions.

## Architecture

- Python research/collector jobs run through GitHub Actions initially.
- Static dashboard is hosted with GitHub Pages.
- Persistent storage is not provided by GitHub Pages or ephemeral Actions runners; a durable database/storage provider will be evaluated before relying on long-term history.
- Telegram access will use an authorized Telegram client session stored only as an encrypted GitHub Secret or other secure secret store. Never commit session files or API credentials.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

## Current status

- [x] Public repository and GitHub Pages deployment.
- [x] Initial project scaffold and CI.
- [x] Source-attributed OHLCV CSV ingestion with strict validation.
- [ ] Select and authorize a licensed EGX data provider.
- [ ] Connect a documented EGX/US market-data API.
- [ ] Durable database and scheduled ingestion.
- [ ] Research engine, risk controls and verified reports.
- [ ] Dashboard API integration.
- [ ] Telegram integration (authorized channels only).

## Market data ingestion

See [docs/data-ingestion.md](docs/data-ingestion.md) and the empty [CSV template](data/imports/template.csv).

The importer validates source-attributed CSV exports; it does not fetch live quotes. No live market-data provider is configured yet.

## Important

This project is a research aid, not financial advice. It does not guarantee profit or prevent losses. The user makes all investment decisions and places any trades manually.
