"""Einrichtungsdialog für Too Good To Go Mail."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback

from .const import (
    CONF_DAYS, CONF_FOLDER, CONF_SENDER, DEFAULT_DAYS, DEFAULT_FOLDER,
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_SENDER, DOMAIN,
)
from .coordinator import ImapLoginError, imap_verbinden


def _test(host: str, port: int, user: str, pw: str) -> None:
    conn = imap_verbinden(host, port, user, pw)
    conn.logout()


class TgtgConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()
            try:
                await self.hass.async_add_executor_job(
                    _test, user_input[CONF_HOST], user_input[CONF_PORT],
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD],
                )
            except ImapLoginError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Too Good To Go ({user_input[CONF_USERNAME]})", data=user_input
                )
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_FOLDER, default=DEFAULT_FOLDER): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            d = entry.data
            try:
                await self.hass.async_add_executor_job(
                    _test, d[CONF_HOST], d[CONF_PORT], d[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
            except ImapLoginError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return TgtgOptionsFlow()


class TgtgOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        o = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema({
            vol.Optional(CONF_FOLDER, default=o.get(CONF_FOLDER, DEFAULT_FOLDER)): str,
            vol.Optional(CONF_SENDER, default=o.get(CONF_SENDER, DEFAULT_SENDER)): str,
            vol.Optional(CONF_DAYS, default=o.get(CONF_DAYS, DEFAULT_DAYS)): vol.All(int, vol.Range(min=1, max=90)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
