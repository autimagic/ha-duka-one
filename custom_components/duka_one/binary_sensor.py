"""Binary sensors: filter replacement, alarm, boost active."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .entity import DukaEntity
from .protocol import P


@dataclass(frozen=True, kw_only=True)
class DukaBinaryDescription(BinarySensorEntityDescription):
    param: int


DESCRIPTIONS: tuple[DukaBinaryDescription, ...] = (
    DukaBinaryDescription(key="filter_replacement", translation_key="filter_replacement", param=P.FILTER_INDICATOR, device_class=BinarySensorDeviceClass.PROBLEM, icon="mdi:air-filter"),
    DukaBinaryDescription(key="alarm", translation_key="alarm", param=P.ALARM, device_class=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
    DukaBinaryDescription(key="boost_active", translation_key="boost_active", param=P.BOOST_ACTIVE, device_class=BinarySensorDeviceClass.RUNNING, icon="mdi:fan-plus"),
)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(DukaBinary(entry.runtime_data, d) for d in DESCRIPTIONS)


class DukaBinary(DukaEntity, BinarySensorEntity):
    entity_description: DukaBinaryDescription

    @property
    def is_on(self) -> bool | None:
        v = self.param(self.entity_description.param)
        return None if v is None else bool(v)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        if self.entity_description.key == "alarm":
            return {"level": {0: "none", 1: "alarm", 2: "warning"}.get(self.param(P.ALARM), "unknown")}
        return None
