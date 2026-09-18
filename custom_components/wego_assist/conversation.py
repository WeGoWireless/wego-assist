"""Conversation support for WeGo Assist."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import aiohttp
import probatio

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_AI_TIMEOUT,
    CONF_DEBUG_LOGGING,
    CONF_LM_STUDIO_URL,
    CONF_MODEL,
    DEFAULT_AI_TIMEOUT,
    DEFAULT_DEBUG_LOGGING,
    DEFAULT_LM_STUDIO_URL,
    DEFAULT_MODEL,
    DOMAIN,
)
from .coordinator import WeGoAssistCoordinator

_LOGGER = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 10


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


def _format_tool(
    tool: llm.Tool,
    custom_serializer,
) -> dict[str, Any]:
    """Convert a Home Assistant tool to OpenAI format."""

    function = {
        "name": tool.name,
        "parameters": probatio.to_openapi(
            tool.parameters,
            custom_serializer=custom_serializer,
        ),
    }

    if tool.description:
        function["description"] = tool.description

    return {
        "type": "function",
        "function": function,
    }


def _convert_content(content) -> dict[str, Any]:
    """Convert Home Assistant chat content to OpenAI format."""

    if isinstance(content, conversation.SystemContent):
        return {
            "role": "system",
            "content": content.content,
        }

    if isinstance(content, conversation.UserContent):
        return {
            "role": "user",
            "content": content.content,
        }

    if isinstance(content, conversation.ToolResultContent):
        return {
            "role": "tool",
            "tool_call_id": content.tool_call_id,
            "content": json.dumps(content.tool_result),
        }

    if isinstance(content, conversation.AssistantContent):
        message: dict[str, Any] = {
            "role": "assistant",
            "content": content.content,
        }

        if content.tool_calls:
            message["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.tool_name,
                        "arguments": json.dumps(
                            tool_call.tool_args
                        ),
                    },
                }
                for tool_call in content.tool_calls
            ]

        return message

    raise TypeError(
        f"Unsupported chat content: {type(content)}"
    )


class WeGoAssistConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """WeGo Assist conversation agent."""

    _attr_has_entity_name = True
    _attr_name = "WeGo Assist"
    _attr_supports_streaming = False
    _attr_supported_features = (
        conversation.ConversationEntityFeature.CONTROL
    )

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

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                llm.LLM_API_ASSIST,
                (
                    "You are WeGo Assist, a voice assistant "
                    "for Home Assistant. Answer simply and "
                    "to the point in plain text. "
                    "For requests involving Home Assistant "
                    "devices, entities, areas, current states, "
                    "or controls, use the available Home "
                    "Assistant tools whenever needed. Do not "
                    "decide from memory or conversation context "
                    "that a device or entity does not exist. "
                    "Do not say a device or entity cannot be "
                    "found until you have attempted the "
                    "appropriate Home Assistant tool. Do not "
                    "ask permission to check Home Assistant "
                    "when checking is necessary to answer the "
                    "request. Never invent an entity state, "
                    "temperature, sensor value, or device. "
                    "If Home Assistant cannot provide the "
                    "requested information after checking, say "
                    "that you cannot find it. Preserve the "
                    "measurement units returned by Home "
                    "Assistant."
                ),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

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
            response = conversation.intent.IntentResponse(
                language=user_input.language
            )
            response.async_set_speech(
                "LM Studio is connected but no model is available."
            )

            return conversation.ConversationResult(
                response=response,
                conversation_id=user_input.conversation_id,
            )

        selected_model = self.entry.options.get(
            CONF_MODEL,
            DEFAULT_MODEL,
        )

        model = (
            selected_model
            if selected_model in models
            else models[0]
        )

        tools = None

        if chat_log.llm_api:
            tools = [
                _format_tool(
                    tool,
                    chat_log.llm_api.custom_serializer,
                )
                for tool in chat_log.llm_api.tools
            ]

        url = f"{base_url}/chat/completions"

        session = async_get_clientsession(self.hass)

        ai_timeout = self.entry.options.get(
            CONF_AI_TIMEOUT,
            DEFAULT_AI_TIMEOUT,
        )
        debug_logging = self.entry.options.get(
            CONF_DEBUG_LOGGING,
            DEFAULT_DEBUG_LOGGING,
        )
        timeout = aiohttp.ClientTimeout(total=ai_timeout)

        agent_id = self.entity_id or DOMAIN

        turn_bytes = 0
        turn_tool_calls = 0
        last_tool = None
        turn_start = time.monotonic()

        try:
            for iteration in range(MAX_TOOL_ITERATIONS):
                payload: dict[str, Any] = {
                    "model": model,
                    "messages": [
                        _convert_content(content)
                        for content in chat_log.content
                    ],
                    "stream": False,
                }

                if tools:
                    payload["tools"] = tools
                    payload["tool_choice"] = "auto"

                # Measure exactly what we send to LM Studio.
                request_bytes = len(
                    json.dumps(
                        payload,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                )

                tool_data_bytes = len(
                    json.dumps(
                        payload.get("tools", []),
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                )

                message_data_bytes = len(
                    json.dumps(
                        payload.get("messages", []),
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                )

                system_context_bytes = sum(
                    len(
                        json.dumps(
                            message,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    )
                    for message in payload.get("messages", [])
                    if message.get("role") == "system"
                )

                conversation_data_bytes = max(
                    0,
                    message_data_bytes - system_context_bytes,
                )

                turn_bytes += request_bytes

                self.coordinator.ai_diagnostics.update(
                    {
                        "last_request_bytes": request_bytes,
                        "last_turn_bytes": turn_bytes,
                        "tool_data_bytes": tool_data_bytes,
                        "message_data_bytes": message_data_bytes,
                        "system_context_bytes": system_context_bytes,
                        "conversation_data_bytes": conversation_data_bytes,
                        "response_time_ms": None,
                        "message_count": len(
                            payload["messages"]
                        ),
                        "tool_count": len(tools or []),
                        "tool_calls": turn_tool_calls,
                        "iterations": iteration + 1,
                        "last_tool": last_tool,
                    }
                )

                async with session.post(
                    url,
                    json=payload,
                    timeout=timeout,
                ) as http_response:
                    http_response.raise_for_status()
                    result = await http_response.json()

                message = result["choices"][0]["message"]

                if debug_logging:
                    response_content = message.get("content")
                    response_tool_calls = message.get(
                        "tool_calls",
                        [],
                    )

                    _LOGGER.info(
                        "AI response metadata: iteration=%s "
                        "finish_reason=%s content_none=%s "
                        "content_blank=%s content_chars=%s "
                        "returned_tool_calls=%s",
                        iteration + 1,
                        result["choices"][0].get(
                            "finish_reason"
                        ),
                        response_content is None,
                        (
                            isinstance(response_content, str)
                            and not response_content.strip()
                        ),
                        (
                            len(response_content)
                            if isinstance(response_content, str)
                            else 0
                        ),
                        len(response_tool_calls),
                    )

                tool_inputs = []

                for tool_call in message.get(
                    "tool_calls",
                    [],
                ):
                    function = tool_call["function"]
                    arguments = function.get(
                        "arguments",
                        {},
                    )

                    if isinstance(arguments, str):
                        arguments = json.loads(
                            arguments or "{}"
                        )

                    turn_tool_calls += 1
                    last_tool = function["name"]

                    if debug_logging:
                        _LOGGER.info(
                            "AI tool call: iteration=%s tool=%s",
                            iteration + 1,
                            function["name"],
                        )

                    tool_inputs.append(
                        llm.ToolInput(
                            id=tool_call.get("id"),
                            tool_name=function["name"],
                            tool_args=arguments,
                        )
                    )

                assistant_content = (
                    conversation.AssistantContent(
                        agent_id=agent_id,
                        content=message.get("content"),
                        tool_calls=tool_inputs or None,
                    )
                )

                async for _tool_result in (
                    chat_log.async_add_assistant_content(
                        assistant_content
                    )
                ):
                    pass

                if not tool_inputs:
                    break

            else:
                _LOGGER.error(
                    "WeGo Assist exceeded %d tool iterations",
                    MAX_TOOL_ITERATIONS,
                )

                final_content = conversation.AssistantContent(
                    agent_id=agent_id,
                    content=(
                        "I was unable to complete that request."
                    ),
                )

                chat_log.async_add_assistant_content_without_tools(
                    final_content
                )

        except Exception:
            _LOGGER.exception(
                "WeGo Assist conversation request failed"
            )

            final_content = conversation.AssistantContent(
                agent_id=agent_id,
                content=(
                    "I had a problem communicating with "
                    "LM Studio or Home Assistant."
                ),
            )

            chat_log.async_add_assistant_content_without_tools(
                final_content
            )

        response_time_ms = round(
            (time.monotonic() - turn_start) * 1000
        )

        self.coordinator.ai_diagnostics.update(
            {
                "last_turn_bytes": turn_bytes,
                "response_time_ms": response_time_ms,
                "tool_calls": turn_tool_calls,
                "last_tool": last_tool,
            }
        )

        if debug_logging:
            _LOGGER.info(
                "AI turn complete: model=%s iterations=%s "
                "tool_calls=%s last_tool=%s turn_bytes=%s "
                "response_time_ms=%s",
                model,
                iteration + 1,
                turn_tool_calls,
                last_tool or "none",
                turn_bytes,
                response_time_ms,
            )

        return conversation.async_get_result_from_chat_log(
            user_input,
            chat_log,
        )
