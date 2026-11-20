"""Current weather and on-demand cached hourly/daily forecasts."""
from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfPressure, UnitOfLength
from homeassistant.core import callback
from homeassistant.util import dt as dt_util
from .entity import WeatherBaseEntity
from .model import value, bearing, condition, hourly, daily


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EnzcomWeather(entry.runtime_data)])


class EnzcomWeather(WeatherBaseEntity, WeatherEntity):
    _attr_name = None
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_visibility_unit = UnitOfLength.METERS
    _attr_native_precipitation_unit = UnitOfLength.MILLIMETERS
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator):
        super().__init__(coordinator, "weather")

    @property
    def current(self):
        return self.coordinator.data["current"]

    @property
    def condition(self): return condition(self.current.get("icon"))
    @property
    def native_temperature(self): return value(self.current, "temperature")
    @property
    def native_dew_point(self): return value(self.current, "dew_point")
    @property
    def humidity(self): return value(self.current, "humidity", 0, 100)
    @property
    def native_pressure(self): return value(self.current, "pressure", 0)
    @property
    def native_wind_speed(self): return value(self.current, "wind_speed", 0)
    @property
    def native_wind_gust_speed(self): return value(self.current, "wind_gust", 0)
    @property
    def wind_bearing(self): return bearing(self.current)
    @property
    def native_visibility(self): return value(self.current, "visibility", 0)
    @property
    def cloud_coverage(self): return value(self.current, "cloud_cover", 0, 100)

    async def async_forecast_hourly(self):
        return hourly(self.coordinator.data) if self.available else None

    async def async_forecast_daily(self):
        if not self.available:
            return None
        data = self.coordinator.data
        name = data["place"].get("timezone")
        if not isinstance(name, str) or not name:
            return []
        zone = await dt_util.async_get_time_zone(name)
        return daily(data, zone) if self.available else None

    @callback
    def _handle_coordinator_update(self):
        super()._handle_coordinator_update()
        self.hass.async_create_task(self.async_update_listeners(None))
