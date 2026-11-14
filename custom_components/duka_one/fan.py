"""Fan entity: on/off, preset speed 1-3/manual, percentage = manual speed."""
from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .const import PRESET_MANUAL, PRESET_TO_SPEED, SPEED_TO_PRESET
from .entity import DukaEntity
from .protocol import P


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DukaFan(entry.runtime_data)])


class DukaFan(DukaEntity, FanEntity):
    _attr_name = None
    _attr_translation_key = "fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = list(PRESET_TO_SPEED)
    _attr_speed_count = 100

    @property
    def is_on(self) -> bool | None:
        v = self.param(P.ON_OFF)
        return None if v is None else bool(v)

    @property
    def preset_mode(self) -> str | None:
        return SPEED_TO_PRESET.get(self.param(P.SPEED))

    @property
    def percentage(self) -> int | None:
        """Speed 1/2/3 show the step's configured value (supply value in supply mode); manual shows the manual speed."""
        if not self.is_on:
            return 0
        speed = self.param(P.SPEED)
        if speed in (1, 2, 3):
            supply = self.param(P.VENT_MODE) == 2
            key = {1: (P.SPEED1_EXHAUST, P.SPEED1_SUPPLY), 2: (P.SPEED2_EXHAUST, P.SPEED2_SUPPLY), 3: (P.SPEED3_EXHAUST, P.SPEED3_SUPPLY)}[speed][1 if supply else 0]
            raw = self.param(key)
        else:
            raw = self.param(P.MANUAL_SPEED)
        return None if raw is None else round(raw * 100 / 255)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if not self.is_on:
            await self.coordinator.async_write(P.ON_OFF, 1)
            await asyncio.sleep(0.2)
        await self.coordinator.async_write(P.SPEED, PRESET_TO_SPEED[preset_mode])

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
            return
        if not self.is_on:
            await self.coordinator.async_write(P.ON_OFF, 1)
            await asyncio.sleep(0.2)
        if self.preset_mode != PRESET_MANUAL:
            await self.coordinator.async_write(P.SPEED, PRESET_TO_SPEED[PRESET_MANUAL])
            await asyncio.sleep(0.2)
        await self.coordinator.async_write(P.MANUAL_SPEED, max(1, round(percentage * 255 / 100)))

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        await self.coordinator.async_write(P.ON_OFF, 1)
        if preset_mode is not None:
            await asyncio.sleep(0.2)
            await self.coordinator.async_write(P.SPEED, PRESET_TO_SPEED[preset_mode])
        elif percentage is not None:
            await asyncio.sleep(0.2)
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(P.ON_OFF, 0)
