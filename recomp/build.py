"""Turn the history into the dashboard page."""
import json

STATIC_DEFAULTS = {
    "season": {
        "2022": [202.6, 203.9, 202.2, 202.6, 202.6, 200.9, 199.1],
        "2023": [193.3, 192.1, 198.4, 206.9, 208.5, 205.4, 205.6],
        "2024": [191.4, 189.8, 187.9, 189.6, 193.2, 195.4, 196.5],
        "2025": [190.9, 192.3, 196.2, 197.8, 202.9, 205.4, 205.7],
    },
    "phases": [{"name": "Cut", "from": "2026-04-14", "to": "2026-08-15"},
               {"name": "Bulk", "from": "2026-08-17", "to": None}],
    "liftPlan": [["Barbell bench press", 135, 8], ["Incline DB press (pair)", 110, 10],
                 ["Seated DB shoulder press", 45, 10], ["Lat pull-down", 100, 10],
                 ["Seated cable row", 100, 12], ["Dumbbell row", 65, 10],
                 ["Triceps extension", 40, 12], ["Hammer curl", 35, 12]],
}


def to_page_data(hist):
    days = hist.get("days", {})
    static = {**STATIC_DEFAULTS, **hist.get("static", {})}
    daily, muscle, hrv, sleep, intake = [], [], [], [], {}
    for d in sorted(days):
        r = days[d]
        row = {k: r[k] for k in ("w", "bf", "rhr", "steps", "dist", "deep", "rem", "burn") if r.get(k) is not None}
        if r.get("pm"):
            row["pm"] = True
        if row:
            daily.append({"d": d, **row})
        if r.get("muscle"):
            muscle.append({"d": d, "muscle": r["muscle"]})
        if r.get("hrv"):
            hrv.append({"d": d, "v": r["hrv"]})
        if r.get("bed") is not None and r.get("wake") is not None:
            sleep.append({"d": d, "bed": r["bed"], "wake": r["wake"], "score": r.get("sleepScore")})
        if "intake" in r:
            intake[d] = r["intake"]
    workouts = sorted(hist.get("workouts", {}).values(), key=lambda w: w["date"])
    return {"daily": daily, "muscle": muscle, "hrv": hrv, "sleep": sleep, "intake": intake,
            "workouts": workouts, **static}


def build(hist, template_path, out_path):
    html = open(template_path, encoding="utf-8").read()
    data = json.dumps(to_page_data(hist), separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html.replace("__DATA__", data))
