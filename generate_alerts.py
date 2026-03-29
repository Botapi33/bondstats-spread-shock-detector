import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DATA_URL = "https://botapi33.github.io/bondstats-global-yields/global_yields.json"
BASE_DIR = Path(__file__).resolve().parent
ALERTS_PATH = BASE_DIR / "alerts.json"
HISTORY_PATH = BASE_DIR / "history.json"

def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def level_from_score(score: float) -> str:
    if score < 25:
        return "normal"
    if score < 50:
        return "elevated"
    if score < 75:
        return "stress"
    return "shock"

def mean(values):
    if not values:
      return 0.0
    return sum(values) / len(values)

def stddev(values):
    if not values:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((x - avg) ** 2 for x in values) / len(values))

def build():
    data = fetch_json(DATA_URL)
    countries_raw = data.get("countries", {})

    rows = []
    for _, item in countries_raw.items():
        try:
            value = float(item.get("value"))
        except (TypeError, ValueError):
            continue

        try:
            change = float(item.get("change"))
        except (TypeError, ValueError):
            change = 0.0

        rows.append({
            "country": item.get("label", "Unknown"),
            "yield": value,
            "change": change,
            "date": item.get("date", "—"),
            "frequency": item.get("frequency", "—"),
        })

    us = next((r for r in rows if r["country"] == "United States"), None)
    if not us:
        raise RuntimeError("United States benchmark not found in JSON feed")

    spreads = []
    for row in rows:
        if row["country"] == "United States":
            continue
        spread_vs_us = row["yield"] - us["yield"]
        spreads.append({
            **row,
            "spread_vs_us": spread_vs_us
        })

    spread_std = stddev([r["spread_vs_us"] for r in spreads])
    avg_abs_change = mean([abs(r["change"]) for r in spreads])

    shock_score = min(100.0, (spread_std * 10.0) + (avg_abs_change * 20.0))
    level = level_from_score(shock_score)

    alerts = []

    if shock_score >= 75:
        alerts.append({
            "title": "Global spread shock",
            "message": "Cross-country bond spread dispersion has moved into a shock regime.",
            "country": "Global",
            "value": round(shock_score, 2),
            "unit": "/100",
            "level": "shock"
        })
    elif shock_score >= 50:
        alerts.append({
            "title": "Global spread stress",
            "message": "Cross-country bond spread dispersion is elevated and moving into stress territory.",
            "country": "Global",
            "value": round(shock_score, 2),
            "unit": "/100",
            "level": "stress"
        })
    elif shock_score >= 25:
        alerts.append({
            "title": "Elevated divergence",
            "message": "Bond markets are showing elevated divergence versus the US benchmark.",
            "country": "Global",
            "value": round(shock_score, 2),
            "unit": "/100",
            "level": "elevated"
        })

    by_change = sorted(spreads, key=lambda x: abs(x["change"]), reverse=True)
    top_movers = by_change[:8]

    for mover in top_movers[:3]:
        abs_change = abs(mover["change"])
        if abs_change >= 0.30:
            alerts.append({
                "title": "Large country move",
                "message": f"{mover['country']} is showing an unusually large recent yield move.",
                "country": mover["country"],
                "value": round(mover["change"], 2),
                "unit": " pp",
                "level": "shock" if abs_change >= 0.50 else "stress"
            })

    widest_spread = max(spreads, key=lambda x: x["spread_vs_us"])
    lowest_spread = min(spreads, key=lambda x: x["spread_vs_us"])

    if widest_spread["spread_vs_us"] >= 4.0:
        alerts.append({
            "title": "Wide positive spread",
            "message": f"{widest_spread['country']} is trading far above the US benchmark.",
            "country": widest_spread["country"],
            "value": round(widest_spread["spread_vs_us"], 2),
            "unit": " pp",
            "level": "stress"
        })

    if lowest_spread["spread_vs_us"] <= -2.0:
        alerts.append({
            "title": "Deep negative spread",
            "message": f"{lowest_spread['country']} is trading well below the US benchmark.",
            "country": lowest_spread["country"],
            "value": round(lowest_spread["spread_vs_us"], 2),
            "unit": " pp",
            "level": "elevated"
        })

    description = {
        "normal": "Bond markets are moving within a relatively normal cross-country dispersion range.",
        "elevated": "Bond markets are showing elevated divergence, but not yet a full stress regime.",
        "stress": "Cross-country bond market divergence is high enough to signal stress across sovereign yields.",
        "shock": "Bond markets are no longer moving together. Cross-country divergence has moved into a shock regime."
    }[level]

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    alerts_payload = {
        "updated_at": now,
        "source_updated_at": data.get("meta", {}).get("lastUpdated", "—"),
        "shock_score": round(shock_score, 2),
        "level": level,
        "description": description,
        "top_movers": [
            {
                "country": m["country"],
                "change": round(m["change"], 2),
                "spread_vs_us": round(m["spread_vs_us"], 2)
            }
            for m in top_movers
        ],
        "alerts": alerts
    }

    if HISTORY_PATH.exists():
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    else:
        history = {"entries": []}

    history["entries"].insert(0, {
        "timestamp": now,
        "shock_score": round(shock_score, 2),
        "level": level
    })
    history["entries"] = history["entries"][:100]

    ALERTS_PATH.write_text(json.dumps(alerts_payload, indent=2), encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")

if __name__ == "__main__":
    build()
