"""Coordinator for WeGo Assist."""

from __future__ import annotations

from datetime import timedelta
import logging
import time

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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
            "tool_data_bytes": None,
            "message_data_bytes": None,
            "system_context_bytes": None,
            "conversation_data_bytes": None,
            "response_time_ms": None,
            "message_count": None,
            "tool_count": None,
            "tool_calls": None,
            "iterations": None,
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

            session = async_get_clientsession(self.hass)

            async with session.get(
                url,
                timeout=client_timeout,
            ) as response:
                response.raise_for_status()
                payload = await response.json()

            latency_ms = round(
                (time.monotonic() - start) * 1000
            )

            models = [
                model.get("id")
                for model in payload.get("data", [])
                if model.get("id")
            ]

            # LM Studio's native API reports which models are
            # currently loaded. This is optional diagnostic data;
            # failure here must not affect the normal health check.
            loaded_models = []

            if base_url.endswith("/v1"):
                server_root = base_url[:-3]
            else:
                server_root = base_url

            native_models_url = (
                f"{server_root}/api/v1/models"
            )

            try:
                async with session.get(
                    native_models_url,
                    timeout=client_timeout,
                ) as response:
                    response.raise_for_status()
                    native_payload = await response.json()

                loaded_models = [
                    model.get("key")
                    for model in native_payload.get(
                        "models",
                        [],
                    )
                    if model.get("type") == "llm"
                    and model.get("key")
                    and model.get("loaded_instances")
                ]
            except Exception as err:
                _LOGGER.debug(
                    "Unable to retrieve LM Studio loaded models: %s",
                    err,
                )

            return {
                "connected": True,
                "latency_ms": latency_ms,
                "models": models,
                "loaded_models": loaded_models,
            }

        except Exception as err:
            raise UpdateFailed(
                f"Unable to connect to LM Studio: {err}"
            ) from err
