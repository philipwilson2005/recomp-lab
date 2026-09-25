"""Daily job: refresh from Garmin, save encrypted history, build site/index.html.

  python run.py                 # last 7 days (default, what the GitHub Action runs)
  python run.py --days 30       # wider refresh
  python run.py --from 2026-07-01   # backfill from a date
  python run.py --no-fetch      # just rebuild the page from saved history
"""
import argparse, os
from datetime import date, timedelta
from recomp import store, build

HIST, TOKENS = "data/history.enc", "data/tokens.enc"

p = argparse.ArgumentParser()
p.add_argument("--days", type=int, default=7)
p.add_argument("--from", dest="start")
p.add_argument("--no-fetch", action="store_true")
a = p.parse_args()

hist = store.load_json(HIST, {"days": {}, "workouts": {}})

if not a.no_fetch:
    from garminconnect import Garmin
    from recomp.fetch import fetch_range
    g = Garmin()
    g.login(store.load_text(TOKENS))  # inline JSON tokenstore; tokens refresh automatically
    end = date.today()
    start = date.fromisoformat(a.start) if a.start else end - timedelta(days=a.days - 1)
    fetch_range(g, hist, start, end)
    store.save_text(TOKENS, g.client.dumps())  # persist refreshed tokens for tomorrow
    store.save_json(HIST, hist)

os.makedirs("site", exist_ok=True)
build.build(hist, "template/index.html", "site/index.html")
print(f"[run] built site/index.html from {len(hist['days'])} days, {len(hist['workouts'])} sessions")
