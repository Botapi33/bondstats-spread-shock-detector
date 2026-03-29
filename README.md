# Spread Shock Detector

A real-time bond market divergence detection tool.

## What it does

This tool tracks:

- cross-country yield dispersion
- recent changes in sovereign yields
- spread widening vs US benchmark

## Shock Score

A dynamic score (0–100) based on:

- spread dispersion
- average absolute yield changes

## Levels

- Normal
- Elevated
- Stress
- Shock

## Data Source

https://botapi33.github.io/bondstats-global-yields/global_yields.json

