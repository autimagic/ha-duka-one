"""Numbers: humidity threshold, boost delay, manual speed."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .entity import DukaEntity
from .protocol import P


@dataclass(frozen=True, kw_only=True)
class DukaNumberDescription(NumberEntityDescription):
    param: int


DESCRIPTIONS: tuple[DukaNumberDescription, ...] = (
    DukaNumberDescription(
        key="humidity_threshold", translation_key="humidity_threshold", param=P.HUMIDITY_THRESHOLD,
        native_min_value=40, native_max_value=80, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER, icon="mdi:water-percent", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="boost_delay", translation_key="boost_delay", param=P.BOOST_DELAY,
        native_min_value=0, native_max_value=60, native_step=1, native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX, icon="mdi:timer-sand", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="manual_speed", translation_key="manual_speed", param=P.MANUAL_SPEED,
        native_min_value=0, native_max_value=255, native_step=1,
        mode=NumberMode.SLIDER, icon="mdi:fan", entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(DukaNumber(entry.runtime_data, d) for d in DESCRIPTIONS)


class DukaNumber(DukaEntity, NumberEntity):
    entity_description: DukaNumberDescription

    @property
    def native_value(self) -> float | None:
        return self.param(self.entity_description.param)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write(self.entity_description.param, int(value))
