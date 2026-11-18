"""Read-only public client; never accepts arbitrary servers or follows redirects."""
import asyncio
import re
from datetime import datetime, timezone
from math import isfinite

import aiohttp

from .const import API_URL


class WeatherError(Exception):
    """The public service could not provide usable data."""


class RateLimited(WeatherError):
    """The service asked us to wait."""


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) else None


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (TypeError, ValueError, AttributeError):
        return None


def place_id(value):
    return isinstance(value, str) and re.fullmatch(r"geonames:[1-9]\d{0,9}", value) is not None


class WeatherClient:
    def __init__(self, session):
        self.session = session

    async def _get(self, path, params=None):
        try:
            async with asyncio.timeout(20):
                async with self.session.get(API_URL + path, params=params, allow_redirects=False,
                        headers={"Accept": "application/json", "User-Agent": "ENZCOM-Weather-HomeAssistant/1.0.0"}) as response:
                    if response.status == 429:
                        raise RateLimited("rate_limited")
                    if response.status != 200:
                        raise WeatherError("cannot_connect")
                    # Bound public responses before decoding, including chunked responses.
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(65536):
                        content.extend(chunk)
                        if len(content) > 2_000_000:
                            raise WeatherError("invalid_response")
                    import json
                    result = json.loads(content)
                    if not isinstance(result, dict):
                        raise WeatherError("invalid_response")
                    return result
        except (aiohttp.ClientError, TimeoutError, ValueError, UnicodeError) as err:
            raise WeatherError("cannot_connect") from err

    async def search(self, query):
        query = query.strip()
        if not 2 <= len(query) <= 100:
            return []
        data = await self._get("/api/v1/places", {"q": query})
        return [p for p in data.get("places", []) if isinstance(p, dict)
                and place_id(p.get("id")) and isinstance(p.get("name"), str)][:30]

    async def weather(self, location):
        if not place_id(location):
            raise WeatherError("invalid_place")
        data = await self._get("/api/v1/weather/" + location)
        if (data.get("schema_version") != 1 or not isinstance(data.get("place"), dict)
                or data["place"].get("id") != location
                or not isinstance(data.get("current"), dict)
                or not isinstance(data.get("hourly"), list)
                or not isinstance(data.get("daily"), list)
                or not isinstance(data.get("units"), dict)
                or timestamp(data.get("fetched_at")) is None
                or timestamp(data.get("expires_at")) is None):
            raise WeatherError("invalid_response")
        for key, unit in {"temperature": "°C", "wind_speed": "km/h", "wind_gust": "km/h",
                          "precipitation": "mm", "pressure": "hPa", "humidity": "%", "visibility": "m"}.items():
            if data["units"].get(key) != unit:
                raise WeatherError("invalid_units")
        return data
