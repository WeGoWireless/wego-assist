"""Conversation support for WeGo Assist."""

from __future__ import annotations

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.intent import IntentResponse

from .const import (
    CONF_LM_STUDIO_URL,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_LM_STUDIO_URL,
    DEFAULT_REQUEST_TIMEOUT,
    DOMAIN,
)
from .coordinator import WeGoAssistCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the WeGo Assist conversation entity."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            WeGoAssistConversationEntity(
                coordinator,
                entry,
            )
        ]
    )


class WeGoAssistConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """WeGo Assist conversation agent."""

    _attr_has_entity_name = True
    _attr_name = "WeGo Assist"
    _attr_supports_streaming = False

    def __init__(
        self,
        coordinator: WeGoAssistCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize WeGo Assist."""

        self.coordinator = coordinator
        self.entry = entry

        self._attr_unique_id = (
            f"{entry.entry_id}_conversation"
        )

    @property
    def supported_languages(self):
        """Return supported languages."""

        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """Register conversation agent."""

        await super().async_added_to_hass()

        conversation.async_set_agent(
            self.hass,
            self.entry,
            self,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unregister conversation agent."""

        conversation.async_unset_agent(
            self.hass,
            self.entry,
        )

        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a conversation message."""

        base_url = self.entry.options.get(
            CONF_LM_STUDIO_URL,
            DEFAULT_LM_STUDIO_URL,
        ).rstrip("/")

        models = (
            self.coordinator.data.get("models", [])
            if self.coordinator.data
            else []
        )

        if not models:
            response = IntentResponse(
                language=user_input.language
            )
            response.async_set_speech(
                "LM Studio is connected but no model is available."
            )

            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id,
            )

        preferred_model = "qwen/qwen3-8b"

        model = (
            preferred_model
            if preferred_model in models
            else models[0]
        )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are WeGo Assist, a voice assistant "
                        "for Home Assistant. Answer simply and "
                        "to the point in plain text."
                    ),
                },
                {
                    "role": "user",
                    "content": user_input.text,
                },
            ],
            "stream": False,
        }

        url = f"{base_url}/chat/completions"

        # AI inference can take substantially longer than
        # the LM Studio health check.
        timeout = aiohttp.ClientTimeout(total=180)

        try:
            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:
                async with session.post(
                    url,
                    json=payload,
                ) as http_response:
                    http_response.raise_for_status()
                    result = await http_response.json()

            answer = result["choices"][0]["message"]["content"]

        except Exception:
            response = IntentResponse(
                language=user_input.language
            )
            response.async_set_speech(
                "I had a problem communicating with LM Studio."
            )

            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id,
            )

        response = IntentResponse(
            language=user_input.language
        )

        response.async_set_speech(answer)

        return conversation.ConversationResult(
            response=response,
            conversation_id=user_input.conversation_id,
        )
