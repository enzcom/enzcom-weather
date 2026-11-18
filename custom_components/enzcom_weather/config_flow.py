"""Search and select a location without YAML or API credentials."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector
from .api import WeatherClient, WeatherError, RateLimited
from .const import DOMAIN, CONF_PLACE_ID


class EnzcomWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._places = {}

    @property
    def client(self):
        return WeatherClient(async_get_clientsession(self.hass))

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                places = await self.client.search(user_input["query"])
                self._places = {p["id"]: p for p in places}
                if places:
                    return await self.async_step_place()
                errors["base"] = "no_places"
            except RateLimited:
                errors["base"] = "rate_limited"
            except WeatherError:
                errors["base"] = "cannot_connect"
        return self.async_show_form(step_id="user", description_placeholders={"privacy_url": "https://weather.enzcom.cloud/datenschutz"}, data_schema=vol.Schema({
            vol.Required("query"): selector.TextSelector(selector.TextSelectorConfig())}), errors=errors)

    async def async_step_place(self, user_input=None):
        errors = {}
        if user_input is not None:
            location = user_input.get(CONF_PLACE_ID)
            if location not in self._places:
                errors["base"] = "invalid_place"
            else:
                await self.async_set_unique_id(location)
                self._abort_if_unique_id_configured()
                try:
                    data = await self.client.weather(location)
                except RateLimited:
                    errors["base"] = "rate_limited"
                except WeatherError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(title=data["place"]["name"], data={CONF_PLACE_ID: location})
        if not self._places:
            return await self.async_step_user()
        options = [{"value": k, "label": " · ".join(str(v) for v in [p["name"], p.get("region"), p.get("country")] if v)}
                   for k, p in self._places.items()]
        return self.async_show_form(step_id="place", data_schema=vol.Schema({
            vol.Required(CONF_PLACE_ID): selector.SelectSelector(selector.SelectSelectorConfig(options=options))}), errors=errors)
