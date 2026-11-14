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
    scale_255: bool = False  # entity shows 0-100 %, unit stores 0-255
    uint16: bool = False


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
    DukaNumberDescription(
        key="speed1_exhaust", translation_key="speed1_exhaust", param=P.SPEED1_EXHAUST, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-1", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="speed1_supply", translation_key="speed1_supply", param=P.SPEED1_SUPPLY, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-1", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="speed2_exhaust", translation_key="speed2_exhaust", param=P.SPEED2_EXHAUST, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-2", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="speed2_supply", translation_key="speed2_supply", param=P.SPEED2_SUPPLY, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-2", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="speed3_exhaust", translation_key="speed3_exhaust", param=P.SPEED3_EXHAUST, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-3", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="speed3_supply", translation_key="speed3_supply", param=P.SPEED3_SUPPLY, scale_255=True,
        native_min_value=0, native_max_value=100, native_step=1, native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX, icon="mdi:fan-speed-3", entity_category=EntityCategory.CONFIG,
    ),
    DukaNumberDescription(
        key="filter_interval", translation_key="filter_interval", param=P.FILTER_INTERVAL, uint16=True,
        native_min_value=1, native_max_value=365, native_step=1, native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX, icon="mdi:air-filter", entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(DukaNumber(entry.runtime_data, d) for d in DESCRIPTIONS)


class DukaNumber(DukaEntity, NumberEntity):
    entity_description: DukaNumberDescription

    @property
    def native_value(self) -> float | None:
        v = self.param(self.entity_description.param)
        if v is None:
            return None
        return round(v * 100 / 255) if self.entity_description.scale_255 else v

    async def async_set_native_value(self, value: float) -> None:
        d = self.entity_description
        if d.scale_255:
            await self.coordinator.async_write(d.param, round(value * 255 / 100))
        elif d.uint16:
            await self.coordinator.async_write(d.param, int(value).to_bytes(2, "little"))
        else:
            await self.coordinator.async_write(d.param, int(value))
