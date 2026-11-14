"""Config flow: broadcast discovery first, manual entry as fallback."""
from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, DOMAIN
from .protocol import DEFAULT_PASSWORD, INFO_PARAMS, DukaClient, P

MANUAL = "manual"


async def _validate(hass: HomeAssistant, ip: str, device_id: str, password: str) -> dict[str, Any]:
    client = DukaClient()
    try:
        resp = await client.read(ip, device_id, password, INFO_PARAMS)
    finally:
        client.close()
    return resp.values


class DukaConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._found: dict[str, str] = {}
        self._picked: tuple[str, str] | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            if user_input["device"] == MANUAL:
                return await self.async_step_manual()
            dev = user_input["device"]
            self._picked = (dev, self._found[dev])
            return await self.async_step_credentials()

        client = DukaClient()
        try:
            found = await client.search()
        except OSError:
            found = []
        finally:
            client.close()
        configured = self._async_current_ids()
        self._found = {dev: ip for dev, ip in found if dev not in configured}
        if not self._found:
            return await self.async_step_manual()
        options = {dev: f"{dev} ({ip})" for dev, ip in self._found.items()}
        options[MANUAL] = "Enter manually"
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required("device"): vol.In(options)}))

    async def async_step_credentials(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        assert self._picked is not None
        dev, ip = self._picked
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self._finish(ip, dev, user_input[CONF_PASSWORD], user_input[CONF_NAME], errors) or self.async_show_form(
                step_id="credentials", data_schema=self._cred_schema(user_input), errors=errors, description_placeholders={"device_id": dev, "ip": ip}
            )
        return self.async_show_form(step_id="credentials", data_schema=self._cred_schema({}), description_placeholders={"device_id": dev, "ip": ip})

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._finish(
                user_input[CONF_IP_ADDRESS], user_input[CONF_DEVICE_ID].strip().upper(), user_input[CONF_PASSWORD], user_input[CONF_NAME], errors
            )
            if result:
                return result
        schema = vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS, default=(user_input or {}).get(CONF_IP_ADDRESS, "")): str,
                vol.Required(CONF_DEVICE_ID, default=(user_input or {}).get(CONF_DEVICE_ID, "")): str,
                vol.Required(CONF_PASSWORD, default=(user_input or {}).get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
                vol.Required(CONF_NAME, default=(user_input or {}).get(CONF_NAME, "DUKA One")): str,
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    @staticmethod
    def _cred_schema(prev: dict[str, Any]) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_PASSWORD, default=prev.get(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
                vol.Required(CONF_NAME, default=prev.get(CONF_NAME, "DUKA One")): str,
            }
        )

    async def _finish(self, ip: str, dev: str, password: str, name: str, errors: dict[str, str]) -> ConfigFlowResult | None:
        if len(dev) != 16:
            errors[CONF_DEVICE_ID] = "invalid_device_id"
            return None
        await self.async_set_unique_id(dev)
        self._abort_if_unique_id_configured(updates={CONF_IP_ADDRESS: ip})
        try:
            info = await _validate(self.hass, ip, dev, password)
        except asyncio.TimeoutError:
            errors["base"] = "cannot_connect"
            return None
        except OSError:
            errors["base"] = "cannot_connect"
            return None
        if P.FIRMWARE not in info:
            errors["base"] = "invalid_auth"
            return None
        return self.async_create_entry(
            title=name,
            data={CONF_IP_ADDRESS: ip, CONF_DEVICE_ID: dev, CONF_PASSWORD: password, CONF_NAME: name},
        )
