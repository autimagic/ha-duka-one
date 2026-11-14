"""Buttons: reset filter timer, sync device clock."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import DukaConfigEntry
from .entity import DukaEntity
from .protocol import P

RESET_FILTER = ButtonEntityDescription(key="reset_filter", translation_key="reset_filter", icon="mdi:air-filter", entity_category=EntityCategory.CONFIG)
SYNC_CLOCK = ButtonEntityDescription(key="sync_clock", translation_key="sync_clock", icon="mdi:clock-check-outline", entity_category=EntityCategory.CONFIG)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DukaResetFilter(entry.runtime_data, RESET_FILTER), DukaSyncClock(entry.runtime_data, SYNC_CLOCK)])


class DukaResetFilter(DukaEntity, ButtonEntity):
    async def async_press(self) -> None:
        await self.coordinator.async_reset_filter()


class DukaSyncClock(DukaEntity, ButtonEntity):
    async def async_press(self) -> None:
        now: datetime = dt_util.now()
        await self.coordinator.async_write(P.RTC_TIME, bytes([now.second, now.minute, now.hour]))
        await self.coordinator.async_write(P.RTC_DATE, bytes([now.day, now.isoweekday(), now.month, now.year % 100]))
