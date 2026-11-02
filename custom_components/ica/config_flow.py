"""Config flow: paste the thSessionId cookie from ica.se."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IcaApi, IcaApiError, IcaAuthError
from .const import CONF_SESSION_ID, DOMAIN

SCHEMA = vol.Schema({vol.Required(CONF_SESSION_ID): str})


class IcaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, session_id: str) -> tuple[IcaApi | None, str | None]:
        api = IcaApi(async_get_clientsession(self.hass), session_id.strip())
        try:
            await api.validate()
        except IcaAuthError:
            return None, "invalid_auth"
        except IcaApiError:
            return None, "cannot_connect"
        return api, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            api, error = await self._validate(user_input[CONF_SESSION_ID])
            if api:
                await self.async_set_unique_id(str(api.customer_id))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"ICA ({api.first_name})" if api.first_name else "ICA",
                    data={CONF_SESSION_ID: user_input[CONF_SESSION_ID].strip()},
                )
            errors["base"] = error
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            api, error = await self._validate(user_input[CONF_SESSION_ID])
            if api:
                await self.async_set_unique_id(str(api.customer_id))
                self._abort_if_unique_id_mismatch(reason="wrong_account")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_SESSION_ID: user_input[CONF_SESSION_ID].strip()},
                )
            errors["base"] = error
        return self.async_show_form(step_id="reauth_confirm", data_schema=SCHEMA, errors=errors)
