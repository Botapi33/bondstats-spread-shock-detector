# Spread Shock Detector

A real-time divergence alert system for global sovereign bond markets.

## What this repo includes

- live dashboard (`index.html`)
- automated alert engine (`generate_alerts.py`)
- auto-updating alert feed (`alerts.json`)
- alert history tracking (`history.json`)
- scheduled GitHub Actions workflow

## What it detects

The system tracks:

- cross-country spread dispersion versus the US benchmark
- average absolute yield moves
- largest country movers
- widening or compressing spread extremes

## Shock Regimes

- Normal
- Elevated
- Stress
- Shock

## Data Source

The alert engine reads from:

`https://botapi33.github.io/bondstats-global-yields/global_yields.json`

## Files

- `index.html`
- `generate_alerts.py`
- `alerts.json`
- `history.json`
- `.github/workflows/update-alerts.yml`
- `README.md`
- `.nojekyll`


## Future Extensions

This alert feed can later be used for:

- Twitter / X bot posts
- email alerts
- Telegram / Discord notifications
- embedded BondStats homepage alert blocks
