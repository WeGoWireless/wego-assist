"""Sensors for WeGo Assist."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeGoAssistCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WeGo Assist sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            WeGoAssistLatencySensor(coordinator, entry),
            WeGoAssistModelsSensor(coordinator, entry),
        ]
    )


class WeGoAssistLatencySensor(
    CoordinatorEntity,
    SensorEntity,
):
    """LM Studio API latency."""

    _attr_has_entity_name = True
    _attr_name = "LM Studio Latency"
    _attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: WeGoAssistCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize latency sensor."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{entry.entry_id}_lm_studio_latency"
        )

    @property
    def native_value(self):
        """Return LM Studio latency."""

        if not self.coordinator.data:
            return None

        return self.coordinator.data.get("latency_ms")

    @property
    def device_info(self):
        """Return device information."""

        return {
            "identifiers": {(DOMAIN, "wego_assist")},
            "name": "WeGo Assist",
            "manufacturer": "WeGo Wireless",
            "model": "Local AI Assistant",
        }


class WeGoAssistModelsSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """LM Studio available models."""

    _attr_has_entity_name = True
    _attr_name = "LM Studio Models"
    _attr_icon = "mdi:brain"

    def __init__(
        self,
        coordinator: WeGoAssistCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize models sensor."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{entry.entry_id}_lm_studio_models"
        )

    @property
    def native_value(self):
        """Return number of available models."""

        if not self.coordinator.data:
            return None

        return len(
            self.coordinator.data.get("models", [])
        )

    @property
    def extra_state_attributes(self):
        """Return available model names."""

        if not self.coordinator.data:
            return {}

        return {
            "models": self.coordinator.data.get(
                "models",
                [],
            )
        }

    @property
    def device_info(self):
        """Return device information."""

        return {
            "identifiers": {(DOMAIN, "wego_assist")},
            "name": "WeGo Assist",
            "manufacturer": "WeGo Wireless",
            "model": "Local AI Assistant",
        }
