"""Shared constants for ENZCOM // Weather."""
from datetime import timedelta
DOMAIN = "enzcom_weather"
API_URL = "https://weather.enzcom.cloud"
UPDATE_INTERVAL = timedelta(minutes=10)
CONF_PLACE_ID = "place_id"
PLATFORMS = ["weather", "sensor"]
