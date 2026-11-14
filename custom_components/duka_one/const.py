"""Constants for DUKA One."""
from datetime import timedelta

DOMAIN = "duka_one"
MANUFACTURER = "DUKA Ventilation"

CONF_DEVICE_ID = "device_id"

SCAN_INTERVAL = timedelta(seconds=30)

PRESET_LOW = "low"
PRESET_MEDIUM = "medium"
PRESET_HIGH = "high"
PRESET_MANUAL = "manual"
PRESET_TO_SPEED = {PRESET_LOW: 1, PRESET_MEDIUM: 2, PRESET_HIGH: 3, PRESET_MANUAL: 0xFF}
SPEED_TO_PRESET = {v: k for k, v in PRESET_TO_SPEED.items()}

VENT_MODES = {0: "exhaust", 1: "regeneration", 2: "supply"}
VENT_MODES_REV = {v: k for k, v in VENT_MODES.items()}

TIMER_MODES = {0: "off", 1: "night", 2: "party"}
TIMER_MODES_REV = {v: k for k, v in TIMER_MODES.items()}
