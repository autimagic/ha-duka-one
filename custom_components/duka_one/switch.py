"""Switches: humidity sensor, relay sensor, 0-10 V sensor, weekly schedule, cloud."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .entity import DukaEntity
from .protocol import P


@dataclass(frozen=True, kw_only=True)
class DukaSwitchDescription(SwitchEntityDescription):
    param: int


DESCRIPTIONS: tuple[DukaSwitchDescription, ...] = (
    DukaSwitchDescription(key="humidity_sensor", translation_key="humidity_sensor", param=P.HUMIDITY_SENSOR, icon="mdi:water-percent-alert", entity_category=EntityCategory.CONFIG),
    DukaSwitchDescription(key="relay_sensor", translation_key="relay_sensor", param=P.RELAY_SENSOR, icon="mdi:electric-switch", entity_category=EntityCategory.CONFIG),
    DukaSwitchDescription(key="analog_sensor", translation_key="analog_sensor", param=P.ANALOG_SENSOR, icon="mdi:sine-wave", entity_category=EntityCategory.CONFIG),
    DukaSwitchDescription(key="weekly_schedule", translation_key="weekly_schedule", param=P.WEEKLY_SCHEDULE, icon="mdi:calendar-clock", entity_category=EntityCategory.CONFIG),
    DukaSwitchDescription(key="cloud", translation_key="cloud", param=P.CLOUD, icon="mdi:cloud-outline", entity_category=EntityCategory.CONFIG, entity_registry_enabled_default=False),
)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(DukaSwitch(entry.runtime_data, d) for d in DESCRIPTIONS)


class DukaSwitch(DukaEntity, SwitchEntity):
    entity_description: DukaSwitchDescription

    @property
    def is_on(self) -> bool | None:
        v = self.param(self.entity_description.param)
        return None if v is None else bool(v)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self.entity_description.param, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_write(self.entity_description.param, 0)
