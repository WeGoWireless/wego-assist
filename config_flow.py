"""Config flow for WeGo Assist."""

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_AI_TIMEOUT,
    CONF_DEBUG_LOGGING,
    CONF_LM_STUDIO_URL,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_AI_TIMEOUT,
    DEFAULT_DEBUG_LOGGING,
    DEFAULT_LM_STUDIO_URL,
    DEFAULT_REQUEST_TIMEOUT,
    DOMAIN,
)


class WeGoAssistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WeGo Assist."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title="WeGo Assist",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=None,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return WeGoAssistOptionsFlow()


class WeGoAssistOptionsFlow(config_entries.OptionsFlow):
    """Handle WeGo Assist options."""

    async def async_step_init(self, user_input=None):
        """Manage WeGo Assist options."""

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LM_STUDIO_URL,
                    default=self.config_entry.options.get(
                        CONF_LM_STUDIO_URL,
                        DEFAULT_LM_STUDIO_URL,
                    ),
                ): str,
                vol.Required(
                    CONF_REQUEST_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_REQUEST_TIMEOUT,
                        DEFAULT_REQUEST_TIMEOUT,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                vol.Required(
                    CONF_AI_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_AI_TIMEOUT,
                        DEFAULT_AI_TIMEOUT,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=600)),
                vol.Required(
                    CONF_DEBUG_LOGGING,
                    default=self.config_entry.options.get(
                        CONF_DEBUG_LOGGING,
                        DEFAULT_DEBUG_LOGGING,
                    ),
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
