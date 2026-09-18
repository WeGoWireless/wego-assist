"""Coordinator for WeGo Assist."""

from __future__ import annotations

from datetime import timedelta
import logging
import time

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_LM_STUDIO_URL,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_LM_STUDIO_URL,
    DEFAULT_REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class WeGoAssistCoordinator(DataUpdateCoordinator):
    """Coordinate LM Studio status updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self.entry = entry

        # Runtime diagnostics from AI conversations.
        # These contain metadata only, never prompt content.
        self.ai_diagnostics = {
            "last_request_bytes": None,
            "last_turn_bytes": None,
            "response_time_ms": None,
            "message_count": None,
            "tool_count": None,
            "tool_calls": None,
            "last_tool": None,
        }

        super().__init__(
            hass,
            _LOGGER,
            name="WeGo Assist LM Studio",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Check LM Studio."""

        base_url = self.entry.options.get(
            CONF_LM_STUDIO_URL,
            DEFAULT_LM_STUDIO_URL,
        ).rstrip("/")

        timeout = self.entry.options.get(
            CONF_REQUEST_TIMEOUT,
            DEFAULT_REQUEST_TIMEOUT,
        )

        url = f"{base_url}/models"
        start = time.monotonic()

        try:
            client_timeout = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(
                timeout=client_timeout
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    payload = await response.json()

            latency_ms = round(
                (time.monotonic() - start) * 1000
            )

            return {
                "connected": True,
                "latency_ms": latency_ms,
                "models": [
                    model.get("id")
                    for model in payload.get("data", [])
                    if model.get("id")
                ],
            }

        except Exception as err:
            raise UpdateFailed(
                f"Unable to connect to LM Studio: {err}"
            ) from err
