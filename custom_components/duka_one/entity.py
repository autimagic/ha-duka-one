"""Base entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import DukaCoordinator


class DukaEntity(CoordinatorEntity[DukaCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DukaCoordinator, description: EntityDescription | None = None) -> None:
        super().__init__(coordinator)
        if description is not None:
            self.entity_description = description
            self._attr_unique_id = f"{coordinator.device_id}_{description.key}"
        else:
            self._attr_unique_id = coordinator.device_id
        unit = coordinator.unit_type
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=coordinator.config_entry.title if coordinator.config_entry else None,
            manufacturer=MANUFACTURER,
            model=f"DUKA One type {unit}" if unit is not None else "DUKA One",
            sw_version=coordinator.firmware,
            serial_number=coordinator.device_id,
            configuration_url=f"http://{coordinator.ip}",
        )

    def param(self, param: int):
        return self.coordinator.data.get(param)
