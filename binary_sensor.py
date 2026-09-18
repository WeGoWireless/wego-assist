"""Binary sensors for WeGo Assist."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    """Set up WeGo Assist binary sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            WeGoAssistLMStudioBinarySensor(
                coordinator,
                entry,
            )
        ]
    )


class WeGoAssistLMStudioBinarySensor(
    CoordinatorEntity,
    BinarySensorEntity,
):
    """LM Studio connection sensor."""

    _attr_has_entity_name = True
    _attr_name = "LM Studio"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator: WeGoAssistCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize sensor."""

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{entry.entry_id}_lm_studio_connection"
        )

    @property
    def device_info(self):
        """Return device information."""

        return {
            "identifiers": {(DOMAIN, "wego_assist")},
            "name": "WeGo Assist",
            "manufacturer": "WeGo Wireless",
            "model": "Local AI Assistant",
        }

    @property
    def is_on(self) -> bool:
        """Return whether LM Studio is connected."""

        return bool(
            self.coordinator.data
            and self.coordinator.data.get("connected")
        )

    @property
    def extra_state_attributes(self):
        """Return LM Studio status information."""

        if not self.coordinator.data:
            return {}

        return {
            "latency_ms": self.coordinator.data.get(
                "latency_ms"
            ),
            "models": self.coordinator.data.get(
                "models",
                [],
            ),
        }
