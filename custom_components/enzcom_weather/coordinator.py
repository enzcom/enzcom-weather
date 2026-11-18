"""One shared request per configured location, with native retry semantics."""
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import WeatherClient, WeatherError
from .const import CONF_PLACE_ID, UPDATE_INTERVAL

LOGGER = logging.getLogger(__name__)


class WeatherCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, LOGGER, config_entry=entry, name="ENZCOM // Weather",
                         update_interval=UPDATE_INTERVAL)
        self.location = entry.data[CONF_PLACE_ID]
        self.client = WeatherClient(async_get_clientsession(hass))

    async def _async_update_data(self):
        try:
            return await self.client.weather(self.location)
        except WeatherError as err:
            # Do not expose transport URLs or locations through generic errors.
            raise UpdateFailed("Weather data temporarily unavailable") from err
