# Architecture

## Initial deployment constraints

The first version is designed for GitHub Pages (static frontend) and GitHub Actions (scheduled batch jobs). GitHub Actions is not a persistent server and scheduled runs can be delayed. Do not treat it as a real-time trading system.

## Data flow

1. Telegram collector reads messages only from channels the authorized account can access.
2. Market-data adapters retrieve permitted public/authorized quotes and historical data.
3. Parsers normalize messages into candidate signals with source, timestamp, and confidence metadata.
4. Analysis computes indicators and risk levels from timestamped market data.
5. Reports are generated as static JSON/Markdown artifacts for the dashboard.

## Security

- Never commit Telegram session files, API credentials, broker credentials, or tokens.
- Store secrets in GitHub Actions Secrets; use least privilege.
- A Telegram user session grants account access. Create it locally and never upload or expose it in logs/artifacts.
- No automated order placement in the initial release.

## Financial safety

Recommendations are research outputs, not guarantees. Every signal must show data timestamp, source, entry zone, invalidation/stop level, targets, estimated costs, and risk/reward. If data is stale, missing, or insufficient, output NO_TRADE.

## Planned modules

- egx_intelligence/telegram: authorized Telegram ingestion
- egx_intelligence/market_data: EGX and US market data adapters
- egx_intelligence/analysis: indicators and signal evaluation
- egx_intelligence/risk: position sizing and trade constraints
- egx_intelligence/reports: daily report generation
- frontend/: static dashboard (planned)
