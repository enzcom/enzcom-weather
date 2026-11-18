"""Separate numeric values for dashboards and user-defined automations."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfSpeed, UnitOfPressure, UnitOfLength, DEGREE
from homeassistant.helpers.entity import EntityCategory
from .api import timestamp
from .entity import WeatherBaseEntity
from .model import value, bearing, hourly, fresh

DESCRIPTIONS = (
    SensorEntityDescription(key="temperature", translation_key="temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="humidity", translation_key="humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="pressure", translation_key="pressure", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE, native_unit_of_measurement=UnitOfPressure.HPA, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="wind_speed", translation_key="wind_speed", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="wind_gust", translation_key="wind_gust", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT),
    SensorEntityDescription(key="wind_direction", translation_key="wind_direction", native_unit_of_measurement=DEGREE, icon="mdi:compass-outline"),
    SensorEntityDescription(key="precipitation", translation_key="precipitation", native_unit_of_measurement="l/m²", icon="mdi:weather-rainy"),
    SensorEntityDescription(key="precipitation_probability", translation_key="precipitation_probability", native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:weather-rainy"),
    SensorEntityDescription(key="visibility", translation_key="visibility", device_class=SensorDeviceClass.DISTANCE, native_unit_of_measurement=UnitOfLength.METERS, state_class=SensorStateClass.MEASUREMENT, entity_registry_enabled_default=False),
    SensorEntityDescription(key="fetched_at", translation_key="fetched_at", device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC),
    SensorEntityDescription(key="status", translation_key="status", device_class=SensorDeviceClass.ENUM, options=["current", "stale", "unavailable"], entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EnzcomSensor(entry.runtime_data, description) for description in DESCRIPTIONS])


class EnzcomSensor(WeatherBaseEntity, SensorEntity):
    def __init__(self, coordinator, description):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self):
        if self.entity_description.key in ("status", "fetched_at"):
            return self.coordinator.data is not None
        return super().available

    @property
    def native_value(self):
        key = self.entity_description.key
        data = self.coordinator.data
        if key == "status":
            if not self.coordinator.last_update_success:
                return "unavailable"
            return "current" if fresh(data) else "stale"
        if key == "fetched_at":
            return timestamp(data.get(key))
        if key == "precipitation_probability":
            forecasts = hourly(data)
            return forecasts[0].get(key) if forecasts else None
        if key == "wind_direction":
            return bearing(data["current"])
        return value(data["current"], key, None if key == "temperature" else 0,
                     100 if key == "humidity" else None)

    @property
    def extra_state_attributes(self):
        data, key = self.coordinator.data, self.entity_description.key
        if key == "precipitation":
            current = data["current"]
            return {"interval_start": current.get("interval_start"), "interval_end": current.get("time"),
                    "interval_minutes": current.get("precipitation_minutes"), "data_kind": current.get("kind")}
        if key == "precipitation_probability":
            forecasts = hourly(data)
            return {"forecast_time": forecasts[0]["datetime"] if forecasts else None}
        if key == "status":
            return {"provider": data.get("provider"), "expires_at": data.get("expires_at"),
                    "data_kind": data["current"].get("kind")}
        return None
