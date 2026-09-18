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
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "last_request_bytes",
                "AI Request Size",
                "B",
                "mdi:database-arrow-up",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "last_turn_bytes",
                "AI Turn Data",
                "B",
                "mdi:database-sync",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "tool_data_bytes",
                "AI Tool Data",
                "B",
                "mdi:tools",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "message_data_bytes",
                "AI Message Data",
                "B",
                "mdi:message-text-outline",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "system_context_bytes",
                "AI System Context",
                "B",
                "mdi:text-box-outline",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "conversation_data_bytes",
                "AI Conversation Data",
                "B",
                "mdi:forum-outline",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "response_time_ms",
                "AI Response Time",
                "ms",
                "mdi:timer-outline",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "message_count",
                "AI Messages",
                None,
                "mdi:message-text-outline",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "tool_count",
                "HA Tools Available",
                None,
                "mdi:tools",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "tool_calls",
                "AI Tool Calls",
                None,
                "mdi:hammer-wrench",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "iterations",
                "AI Iterations",
                None,
                "mdi:repeat",
            ),
            WeGoAssistDiagnosticSensor(
                coordinator,
                entry,
                "last_tool",
                "Last Tool Used",
                None,
                "mdi:function-variant",
            ),
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


class WeGoAssistDiagnosticSensor(SensorEntity):
    """Runtime AI diagnostic sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeGoAssistCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        icon: str,
    ) -> None:
        """Initialize diagnostic sensor."""

        self.coordinator = coordinator
        self._diagnostic_key = key

        self._attr_name = name
        self._attr_unique_id = (
            f"{entry.entry_id}_ai_{key}"
        )
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self):
        """Return diagnostic value."""

        return self.coordinator.ai_diagnostics.get(
            self._diagnostic_key
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
