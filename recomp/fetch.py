"""Pull daily data from Garmin Connect via python-garminconnect (MIT,
github.com/cyberjunky/python-garminconnect) and upsert it into the history.

Nothing here prints health values: Actions logs on public repos are public.
"""
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.getenv("TZ_NAME", "America/Chicago"))
G_PER_LB = 453.59237


def log(msg):
    print(f"[fetch] {msg}", flush=True)


def safe(fn, *args):
    try:
        return fn(*args)
    except Exception as e:  # one failed endpoint shouldn't kill the run
        log(f"{getattr(fn, '__name__', 'call')} failed: {type(e).__name__}")
        return None


def _local(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone(TZ)


def _hours_rel_midnight(dt):
    h = dt.hour + dt.minute / 60
    return round(h - 24 if h >= 12 else h, 2)


def _find_calories(obj, depth=0):
    """The nutrition payload isn't documented; look for a daily calorie total."""
    if depth > 3 or obj is None:
        return None
    if isinstance(obj, dict):
        for k in ("totalCalories", "consumedCalories", "caloriesConsumed", "calories", "calorie"):
            v = obj.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return round(v)
        for v in obj.values():
            r = _find_calories(v, depth + 1)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = _find_calories(v, depth + 1)
            if r:
                return r
    return None


def _kind(type_key, name):
    t, n = (type_key or "").lower(), (name or "").lower()
    if "strength" in t or any(k in n for k in ("lift", "push", "pull", "legs", "strength")):
        return "lift"
    if "walk" in t:
        return "walk"
    return "cardio"


def _sets(payload):
    out = []
    for s in (payload or {}).get("exerciseSets", []) or []:
        if s.get("setType") != "ACTIVE" or not s.get("repetitionCount"):
            continue
        ex = (s.get("exercises") or [{}])[0]
        name = (ex.get("name") or ex.get("category") or "UNKNOWN").replace("_", " ").title()
        w = s.get("weight")
        lbs = None
        if w:
            lbs = round(w / G_PER_LB, 1) if w > 1000 else round(w * 2.20462, 1)  # grams vs kg
        out.append({"ex": name, "reps": s["repetitionCount"], "lb": lbs})
    return out


def fetch_range(g, hist, start: date, end: date):
    days, workouts = hist.setdefault("days", {}), hist.setdefault("workouts", {})

    # Scale readings: keep the first weigh-in of each day
    bc = safe(g.get_body_composition, start.isoformat(), end.isoformat()) or {}
    firsts = {}
    for e in bc.get("dateWeightList", []) or []:
        ts = e.get("date") or e.get("timestampGMT")
        if not ts or not e.get("weight"):
            continue
        dt = _local(ts)
        d = e.get("calendarDate") or dt.date().isoformat()
        if d not in firsts or dt < firsts[d][0]:
            firsts[d] = (dt, e)
    for d, (dt, e) in firsts.items():
        rec = days.setdefault(d, {})
        rec["w"] = round(e["weight"] / G_PER_LB, 1)
        if e.get("bodyFat"):
            rec["bf"] = round(e["bodyFat"], 1)
        if e.get("muscleMass"):
            rec["muscle"] = round(e["muscleMass"] / G_PER_LB, 1)
        rec["pm"] = dt.hour >= 17
    log(f"weigh-ins found: {len(firsts)}")

    d = start
    nut_logged = False
    while d <= end:
        k = d.isoformat()
        rec = days.setdefault(k, {})
        s = safe(g.get_user_summary, k) or {}
        if s.get("totalSteps") is not None:
            rec["steps"] = s["totalSteps"]
        if s.get("totalDistanceMeters"):
            rec["dist"] = round(s["totalDistanceMeters"] / 1609.34, 2)
        if s.get("totalKilocalories") and d < date.today():  # today's total is partial
            rec["burn"] = round(s["totalKilocalories"])
        if s.get("restingHeartRate"):
            rec["rhr"] = s["restingHeartRate"]

        sl = (safe(g.get_sleep_data, k) or {}).get("dailySleepDTO") or {}
        if sl.get("sleepStartTimestampGMT") and sl.get("sleepEndTimestampGMT"):
            rec["bed"] = _hours_rel_midnight(_local(sl["sleepStartTimestampGMT"]))
            rec["wake"] = _hours_rel_midnight(_local(sl["sleepEndTimestampGMT"]))
            rec["deep"] = round((sl.get("deepSleepSeconds") or 0) / 60)
            rec["rem"] = round((sl.get("remSleepSeconds") or 0) / 60)
            score = ((sl.get("sleepScores") or {}).get("overall") or {}).get("value")
            if score:
                rec["sleepScore"] = score

        h = ((safe(g.get_hrv_data, k) or {}).get("hrvSummary") or {}).get("lastNightAvg")
        if h:
            rec["hrv"] = h

        n = safe(g.get_nutrition_daily_food_log, k)
        cal = _find_calories(n)
        if cal and cal > 300 and d < date.today():
            rec["intake"] = cal
        elif n and not nut_logged:
            keys = sorted(n.keys()) if isinstance(n, dict) else type(n).__name__
            log(f"nutrition payload keys (no values): {keys}")
            nut_logged = True
        d += timedelta(days=1)

    acts = safe(g.get_activities_by_date, start.isoformat(), end.isoformat()) or []
    for a in acts:
        aid = str(a.get("activityId"))
        type_key = (a.get("activityType") or {}).get("typeKey", "")
        w = {
            "date": (a.get("startTimeLocal") or "")[:10],
            "type": a.get("activityName") or type_key.replace("_", " ").title(),
            "duration": round((a.get("duration") or 0) / 60),
            "cal": round(a["calories"]) if a.get("calories") else None,
            "avgHR": round(a["averageHR"]) if a.get("averageHR") else None,
            "maxHR": round(a["maxHR"]) if a.get("maxHR") else None,
            "kind": _kind(type_key, a.get("activityName")),
        }
        if "strength" in type_key:
            w["sets"] = _sets(safe(g.get_activity_exercise_sets, aid))
        workouts[aid] = w
    log(f"activities found: {len(acts)}")
    return hist
