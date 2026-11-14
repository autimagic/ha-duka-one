"""DUKA One (Blauberg Vento Expert) local integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import DukaCoordinator
from .protocol import DukaClient

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

type DukaConfigEntry = ConfigEntry[DukaCoordinator]


def _client(hass: HomeAssistant) -> DukaClient:
    data = hass.data.setdefault(DOMAIN, {})
    if "client" not in data:
        data["client"] = DukaClient()
    return data["client"]


async def async_setup_entry(hass: HomeAssistant, entry: DukaConfigEntry) -> bool:
    coordinator = DukaCoordinator(hass, entry, _client(hass))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DukaConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok and not [e for e in hass.config_entries.async_loaded_entries(DOMAIN) if e.entry_id != entry.entry_id]:
        client: DukaClient | None = hass.data.get(DOMAIN, {}).pop("client", None)
        if client:
            client.close()
    return ok
