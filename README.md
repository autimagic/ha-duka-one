# DUKA One (Blauberg Vento Expert) for Home Assistant

[![Validate](https://github.com/autimagic/ha-duka-one/actions/workflows/validate.yml/badge.svg)](https://github.com/autimagic/ha-duka-one/actions/workflows/validate.yml)

Local control of single-room heat-recovery ventilation units built on the Blauberg Vento Expert platform, sold in Denmark as **DUKA One**. No cloud, no account: the integration talks to the unit over UDP on your own network using the documented Blauberg "Smart Home" protocol.

## Compatible units

| Status | Units |
|---|---|
| Confirmed | DUKA One type 14 and type 27 (firmware 0.5 and 1.4) |
| Expected to work (same platform and protocol, not tested by us) | Blauberg Vento Expert A30/A50/A100 W, Vents TwinFresh Expert, Siku RV Pro Wi-Fi |
| Unknown | Oxxify and other rebrands of the Vents/Blauberg platform |

If your unit is not listed: try it, then open an issue with the model name and the integration's diagnostics download (Settings → Devices → your unit → Download diagnostics). It contains unit type, firmware and the parameters the unit refused, nothing private.

## Entities per unit

| Entity | What it does |
|---|---|
| Fan | On/off, speed 1–3 as presets (percentage shows the step's configured value), setting a percentage switches to manual speed |
| Select: Ventilation mode | Exhaust, regeneration (heat recovery), supply |
| Select: Timer mode | Off, night, party |
| Number: Humidity threshold | 40–80 % |
| Number: Boost run-on time | 0–60 min |
| Number: Manual speed | 0–255 |
| Number: Speed 1–3 exhaust / supply | The value each speed step runs at, in % |
| Number: Filter interval | 1–365 days |
| Switch: Humidity sensor, relay input, 0-10 V input, weekly schedule, cloud | Enable/disable the unit's own automation inputs |
| Sensor: Humidity, fan 1/2 rpm, filter days left, operating time, timer countdown, device clock | |
| Binary sensor: Filter replacement, alarm, boost | |
| Button: Reset filter timer, sync device clock | |

## Setup

Settings → Devices & services → Add integration → search for DUKA or Blauberg. Units on the local network are found by broadcast; otherwise enter IP, the 16-character device ID (shown in the DUKA app under device info) and the device password (factory default `1111`).

Give each unit a fixed IP in your router.

## Notes

* The unit is polled every 30 seconds. Writes are confirmed by the unit and reflected immediately.
* Factory reset, Wi-Fi settings and the device password are deliberately not exposed.
* Speed 1–3 values (exhaust and supply, in %) and the filter interval (days) are exposed as configuration numbers; they were found by probing DUKA One units and confirmed against the DUKA app, so they may differ on other models. Weekly schedule contents are not exposed yet.

## Protocol

The units speak the protocol described in Blauberg's [Vento Expert: Connection to a "Smart Home" system](https://blaubergventilatoren.net/download/vento-expert-a100-1-s10-w-v2-manual-14758.pdf) (UDP port 4000, packets starting `FD FD 02`, a 16-character device ID, a password and a parameter table). Parameter numbers used here are listed in `protocol.py`. DUKA One units answered the full table 1:1 in testing.

## Installation (custom repository)

1. HA Market / HACS → Integrations → ⋮ → Custom repositories → add `https://github.com/autimagic/ha-duka-one`, category Integration.
2. Download "DUKA One (Blauberg Vento Expert)" and restart Home Assistant.
3. Settings → Devices & services → Add integration → search for DUKA or Blauberg. Units on your network are found automatically; the device password is `1111` unless you changed it in the DUKA app.

Manual alternative: copy `custom_components/duka_one` into your `config/custom_components/` folder and restart.

## Development notes

`duka_read.py` in the repository root is a stand-alone probe: `python duka_read.py <ip> <device_id> [password]` reads every known parameter from a unit without Home Assistant. Useful when reporting a new model.

## License

MIT. Not affiliated with DUKA Ventilation, Blauberg or Vents.
