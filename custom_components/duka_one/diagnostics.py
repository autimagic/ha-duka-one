"""Diagnostics: raw parameter map, redacting the password."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from . import DukaConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: DukaConfigEntry) -> dict[str, Any]:
    c = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), {CONF_PASSWORD}),
        "info": {f"0x{k:04X}": v for k, v in c.info.items()},
        "data": {f"0x{k:04X}": v for k, v in (c.data or {}).items()},
        "unsupported": [f"0x{k:04X}" for k in sorted(c.unsupported)],
        "last_update_success": c.last_update_success,
    }
