"""Conversion to native HA values without inventing unavailable forecasts."""
from datetime import datetime, timedelta, timezone

from .api import number, timestamp


def value(row, key, minimum=None, maximum=None):
    result = number(row.get(key))
    if result is None or (minimum is not None and result < minimum) or (maximum is not None and result > maximum):
        return None
    return result


def bearing(row):
    angle = value(row, "wind_direction", 0, 360)
    return angle % 360 if angle is not None and row.get("wind_speed") != 0 else None


def condition(icon):
    icon = str(icon or "").lower()
    if "thunder" in icon:
        return "lightning-rainy" if "rain" in icon or "shower" in icon else "lightning"
    if "sleet" in icon:
        return "snowy-rainy"
    if "snow" in icon:
        return "snowy"
    if "rain" in icon or "shower" in icon:
        return "rainy"
    if "fog" in icon:
        return "fog"
    if "partly" in icon or "fair" in icon:
        return "partlycloudy"
    if "cloud" in icon:
        return "cloudy"
    if "clear" in icon:
        return "clear-night" if "night" in icon else "sunny"
    if icon == "wind":
        return "windy"
    return None


def hourly(data, now=None):
    now = now or datetime.now(timezone.utc)
    start = now.replace(minute=0, second=0, microsecond=0)
    rain, instants = {}, {}
    for row in data.get("hourly", []):
        if not isinstance(row, dict) or row.get("kind") != "forecast":
            continue
        instant = timestamp(row.get("instant_time", row.get("time")))
        if instant:
            instants[instant] = row if instant not in instants else None
        a, b = timestamp(row.get("interval_start")), timestamp(row.get("time"))
        if a and b and b-a == timedelta(hours=1) and row.get("precipitation_minutes") == 60:
            rain[a] = row if a not in rain else None
    output = []
    for time, row in sorted(instants.items()):
        if row is None or not start <= time < start + timedelta(hours=72):
            continue
        # Wind/temperature are instantaneous; rain belongs to the following hour.
        interval = rain.get(time) or {}
        output.append({"datetime": time.isoformat(), "condition": condition(row.get("icon")),
            "native_temperature": value(row, "temperature"),
            "native_wind_speed": value(row, "wind_speed", 0),
            "native_wind_gust_speed": value(row, "wind_gust", 0), "wind_bearing": bearing(row),
            "humidity": value(row, "humidity", 0, 100), "native_pressure": value(row, "pressure", 0),
            "cloud_coverage": value(row, "cloud_cover", 0, 100),
            "native_precipitation": value(interval, "precipitation", 0),
            "precipitation_probability": value(interval, "precipitation_probability", 0, 100)})
    return output


def daily(data, zone):
    """Convert with an already resolved zone; never load timezone files here."""
    if zone is None:
        return []
    temperatures = {r.get("date"): r for r in data.get("temperature_daily", []) if isinstance(r, dict)}
    output = []
    for row in data.get("daily", [])[:8]:
        if not isinstance(row, dict):
            continue
        try:
            time = datetime.fromisoformat(row["date"]).replace(tzinfo=zone).astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError):
            continue
        temp = temperatures.get(row["date"], {})
        # Do not present remaining-day amounts or incomplete extrema as whole days.
        complete = temp.get("complete") is True
        output.append({"datetime": time.isoformat(), "condition": condition(temp.get("icon")),
            "native_temperature": value(temp, "temperature_max") if complete else None,
            "native_templow": value(temp, "temperature_min") if complete else None,
            "native_precipitation": value(row, "precipitation", 0) if row.get("partial") is False else None})
    return output


def fresh(data, now=None):
    now = now or datetime.now(timezone.utc)
    expires = timestamp(data.get("expires_at"))
    return data.get("stale") is not True and expires is not None and now < expires
