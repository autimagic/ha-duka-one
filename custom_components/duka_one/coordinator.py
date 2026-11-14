"""Polling coordinator for one DUKA One unit."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_DEVICE_ID, DOMAIN, SCAN_INTERVAL
from .protocol import INFO_PARAMS, STATUS_PARAMS, DukaClient, P

_LOGGER = logging.getLogger(__name__)


class DukaCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Reads all status parameters every SCAN_INTERVAL; writes refresh immediately."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: DukaClient) -> None:
        super().__init__(hass, _LOGGER, name=f"{DOMAIN} {entry.title}", update_interval=SCAN_INTERVAL, config_entry=entry)
        self.client = client
        self.ip: str = entry.data[CONF_IP_ADDRESS]
        self.device_id: str = entry.data[CONF_DEVICE_ID]
        self.password: str = entry.data[CONF_PASSWORD]
        self.info: dict[int, Any] = {}
        self.unsupported: set[int] = set()

    async def async_read_info(self) -> None:
        resp = await self.client.read(self.ip, self.device_id, self.password, INFO_PARAMS)
        self.info = resp.values

    async def _async_update_data(self) -> dict[int, Any]:
        # The units occasionally drop a UDP datagram; one retry avoids a spurious "unavailable".
        for attempt in range(2):
            try:
                if not self.info:
                    await self.async_read_info()
                resp = await self.client.read(self.ip, self.device_id, self.password, STATUS_PARAMS)
                break
            except asyncio.TimeoutError as err:
                if attempt == 0:
                    _LOGGER.debug("No answer from %s, retrying once", self.ip)
                    continue
                raise UpdateFailed(f"No answer from {self.ip}") from err
            except OSError as err:
                raise UpdateFailed(f"UDP error to {self.ip}: {err}") from err
        if resp.unsupported:
            self.unsupported |= resp.unsupported
        data = dict(self.data or {})
        data.update(resp.values)
        return data

    async def async_write(self, param: int, value: int | bytes) -> None:
        raw = bytes([value]) if isinstance(value, int) else value
        try:
            resp = await self.client.write(self.ip, self.device_id, self.password, param, raw)
        except asyncio.TimeoutError:
            try:
                resp = await self.client.write(self.ip, self.device_id, self.password, param, raw)
            except asyncio.TimeoutError as err:
                raise HomeAssistantError(f"{self.ip} did not confirm the change") from err
        data = dict(self.data or {})
        data.update(resp.values)
        self.async_set_updated_data(data)

    async def async_reset_filter(self) -> None:
        await self.client.write_noval(self.ip, self.device_id, self.password, P.FILTER_RESET)
        await self.async_request_refresh()

    @property
    def firmware(self) -> str | None:
        return self.info.get(P.FIRMWARE)

    @property
    def unit_type(self) -> int | None:
        return self.info.get(P.UNIT_TYPE)
