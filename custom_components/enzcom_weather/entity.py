"""Stable place-bound entities."""
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, API_URL
from .model import fresh


class WeatherBaseEntity(CoordinatorEntity):
    _attr_has_entity_name = True
    _attr_attribution = "Weather data: ENZCOM // Weather; DWD / Bright Sky or MET Norway."

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.location}_{key}"
        place = coordinator.data["place"]
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coordinator.location)},
            name=place["name"], manufacturer="ENZCOM", model="ENZCOM // Weather",
            configuration_url=f"{API_URL}/?place={coordinator.location}")

    @property
    def available(self):
        return super().available and fresh(self.coordinator.data)
