"""Selects: ventilation mode, timer mode."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .const import TIMER_MODES, TIMER_MODES_REV, VENT_MODES, VENT_MODES_REV
from .entity import DukaEntity
from .protocol import P


@dataclass(frozen=True, kw_only=True)
class DukaSelectDescription(SelectEntityDescription):
    param: int
    to_option: dict[int, str]
    from_option: dict[str, int]


DESCRIPTIONS: tuple[DukaSelectDescription, ...] = (
    DukaSelectDescription(
        key="ventilation_mode", translation_key="ventilation_mode", icon="mdi:swap-horizontal",
        param=P.VENT_MODE, to_option=VENT_MODES, from_option=VENT_MODES_REV, options=list(VENT_MODES.values()),
    ),
    DukaSelectDescription(
        key="timer_mode", translation_key="timer_mode", icon="mdi:timer-outline",
        param=P.TIMER_MODE, to_option=TIMER_MODES, from_option=TIMER_MODES_REV, options=list(TIMER_MODES.values()),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(DukaSelect(entry.runtime_data, d) for d in DESCRIPTIONS)


class DukaSelect(DukaEntity, SelectEntity):
    entity_description: DukaSelectDescription

    @property
    def current_option(self) -> str | None:
        return self.entity_description.to_option.get(self.param(self.entity_description.param))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_write(self.entity_description.param, self.entity_description.from_option[option])
