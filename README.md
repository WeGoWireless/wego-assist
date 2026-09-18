# WeGo Assist 0.1.0

A small Home Assistant custom integration that registers a filtered LLM API.

It reuses Home Assistant's normal Assist tool providers and exposure rules, then
keeps only these tool families:

- GetLiveContext
- GetDateTime
- HassTurnOn
- HassTurnOff
- HassToggle
- HassLightSet
- HassClimateSetTemperature
- HassSetPosition

It intentionally omits media-player, timer, todo, and shopping-list tools.

## Install

Copy the `wego_assist` folder into:

    /config/custom_components/wego_assist/

Then add this to `configuration.yaml`:

    wego_assist:

Restart Home Assistant.

After restart, edit the llama.cpp conversation agent. Under "Control Home
Assistant", select "WeGo Assist" and deselect "Assist".

This is an experimental first version intended for Home Assistant 2026.9-era
LLM APIs.
