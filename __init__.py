"""WeGo Assist integration."""

import logging
import time

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    CONF_LM_STUDIO_URL,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_LM_STUDIO_URL,
    DEFAULT_REQUEST_TIMEOUT,
    DOMAIN,
)
from .coordinator import WeGoAssistCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

SERVICE_TEST_PROMPT = "test_prompt"
ATTR_PROMPT = "prompt"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up WeGo Assist from a config entry."""

    coordinator = WeGoAssistCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    async def async_test_prompt(call: ServiceCall) -> None:
        """Send a test prompt to LM Studio."""

        prompt = call.data[ATTR_PROMPT]

        base_url = entry.options.get(
            CONF_LM_STUDIO_URL,
            DEFAULT_LM_STUDIO_URL,
        ).rstrip("/")

        timeout = entry.options.get(
            CONF_REQUEST_TIMEOUT,
            DEFAULT_REQUEST_TIMEOUT,
        )

        models = (
            coordinator.data.get("models", [])
            if coordinator.data
            else []
        )

        if not models:
            _LOGGER.error(
                "WeGo Assist test prompt failed: "
                "LM Studio returned no models"
            )
            return

        # Prefer the same model currently used by HA if available.
        preferred_model = "qwen/qwen3-8b"
        model = (
            preferred_model
            if preferred_model in models
            else models[0]
        )

        url = f"{base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
        }

        start = time.monotonic()

        try:
            client_timeout = aiohttp.ClientTimeout(
                total=180
            )

            async with aiohttp.ClientSession(
                timeout=client_timeout
            ) as session:
                async with session.post(
                    url,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

            elapsed_ms = round(
                (time.monotonic() - start) * 1000
            )

            answer = result["choices"][0]["message"]["content"]

            _LOGGER.warning(
                "WeGo Assist AI response "
                "(model=%s, %d ms): %s",
                model,
                elapsed_ms,
                answer,
            )

        except Exception:
            _LOGGER.exception(
                "WeGo Assist test prompt failed"
            )

    if not hass.services.has_service(
        DOMAIN,
        SERVICE_TEST_PROMPT,
    ):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TEST_PROMPT,
            async_test_prompt,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_PROMPT): str,
                }
            ),
        )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload WeGo Assist config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        if not hass.data[DOMAIN]:
            hass.services.async_remove(
                DOMAIN,
                SERVICE_TEST_PROMPT,
            )

    return unload_ok
