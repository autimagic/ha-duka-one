"""Sensors: humidity, fan rpm, filter days left, operating time, timer countdown, device clock."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DukaConfigEntry
from .entity import DukaEntity
from .protocol import P


@dataclass(frozen=True, kw_only=True)
class DukaSensorDescription(SensorEntityDescription):
    param: int
    convert: Callable[[Any], Any] = lambda v: v


def _clock(data: dict[int, Any]) -> str | None:
    d, t = data.get(P.RTC_DATE), data.get(P.RTC_TIME)
    return f"{d} {t}" if d and t else None


DESCRIPTIONS: tuple[DukaSensorDescription, ...] = (
    DukaSensorDescription(key="humidity", translation_key="humidity", param=P.HUMIDITY, device_class=SensorDeviceClass.HUMIDITY, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE),
    DukaSensorDescription(key="fan1_rpm", translation_key="fan1_rpm", param=P.FAN1_RPM, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=REVOLUTIONS_PER_MINUTE, icon="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
    DukaSensorDescription(key="fan2_rpm", translation_key="fan2_rpm", param=P.FAN2_RPM, state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=REVOLUTIONS_PER_MINUTE, icon="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
    DukaSensorDescription(key="filter_days_left", translation_key="filter_days_left", param=P.FILTER_COUNTDOWN, native_unit_of_measurement=UnitOfTime.DAYS, icon="mdi:air-filter", convert=lambda m: round(m / 1440, 1)),
    DukaSensorDescription(key="operating_time", translation_key="operating_time", param=P.MACHINE_HOURS, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING, native_unit_of_measurement=UnitOfTime.HOURS, entity_category=EntityCategory.DIAGNOSTIC, convert=lambda m: round(m / 60, 1)),
    DukaSensorDescription(key="timer_countdown", translation_key="timer_countdown", param=P.TIMER_COUNTDOWN, device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.SECONDS, icon="mdi:timer-outline"),
    DukaSensorDescription(key="device_clock", translation_key="device_clock", param=P.RTC_TIME, icon="mdi:clock-outline", entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False),
)


def _has_second_fan(data: dict[int, Any]) -> bool:
    """Single-motor units (e.g. type 27) report 0 rpm on fan 2 while running."""
    running = data.get(P.ON_OFF) == 1 and (data.get(P.FAN1_RPM) or 0) > 0
    return not (running and data.get(P.FAN2_RPM) == 0)


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    second_fan = _has_second_fan(coordinator.data)
    async_add_entities(DukaSensor(coordinator, d) for d in DESCRIPTIONS if d.key != "fan2_rpm" or second_fan)


class DukaSensor(DukaEntity, SensorEntity):
    entity_description: DukaSensorDescription

    @property
    def native_value(self) -> Any:
        if self.entity_description.key == "device_clock":
            return _clock(self.coordinator.data)
        v = self.param(self.entity_description.param)
        return None if v is None else self.entity_description.convert(v)
