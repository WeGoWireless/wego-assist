# WeGo Assist

WeGo Assist is a Home Assistant custom conversation integration for local AI
models served by LM Studio.

It connects Home Assistant directly to LM Studio's OpenAI-compatible API and
uses Home Assistant's native Assist LLM API for device control, current state
queries, and other Home Assistant tools.

## Features

- Local AI conversation through LM Studio
- Home Assistant native Assist tool support
- Device control and live Home Assistant state queries
- Configurable LM Studio URL and conversation model
- Automatic model discovery from LM Studio
- LM Studio connection and loaded-model diagnostics
- AI timing, payload, tool-call, and iteration diagnostics
- Configurable request and AI response timeouts
- Optional metadata-only debug logging
- Home Assistant UI configuration

## Requirements

- Home Assistant 2026.9-era LLM APIs
- LM Studio with its local API server enabled
- A model capable of reliable tool/function calling is recommended

WeGo Assist has primarily been developed and tested with Qwen3 8B.

## Installation

Copy the `wego_assist` directory into:

    /config/custom_components/wego_assist/

Restart Home Assistant.

Then go to **Settings -> Devices & services -> Add Integration** and search
for **WeGo Assist**.

No `configuration.yaml` entry is required.

## Configuration

Integration options include:

- LM Studio URL
- Conversation model
- LM Studio request timeout
- AI response timeout
- Debug logging

Example LM Studio API URL:

    http://192.168.1.100:1234/v1

Change the address to match your LM Studio server.

## Voice Assistants

WeGo Assist can be selected as the conversation agent for a Home Assistant
voice assistant pipeline. Speech-to-text and text-to-speech remain handled
by the services selected in the Home Assistant voice pipeline.

## Home Assistant Tools

WeGo Assist uses Home Assistant's native Assist LLM API and exposure rules.
The exact tools available depend on Home Assistant and the entities exposed
to Assist.

Compatible models can use these tools to read live states, control devices
and lights, work with timers, obtain date and time information, and use
other capabilities provided by Home Assistant.

## Diagnostics

WeGo Assist provides diagnostic entities for LM Studio connectivity, latency,
available and loaded models, AI response timing, request and conversation
payload sizes, message and tool counts, tool calls, iterations, and the last
Home Assistant tool used.

## Debug Logging

Optional debug logging records additional metadata including iterations, tool
names, response metadata, and timing. These metadata messages do not
intentionally log Home Assistant tool arguments or entity state values.

## Status

WeGo Assist is currently version **0.1.0** and should be considered
experimental. It is being developed against Home Assistant 2026.9-era LLM
APIs, which may change in future Home Assistant releases.

## License

MIT License
