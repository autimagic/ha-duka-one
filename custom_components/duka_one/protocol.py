"""Local UDP protocol for DUKA One / Blauberg Vento Expert units (port 4000).

Packet: FD FD | 02 | len(id) id | len(pw) pw | func | data... | checksum (uint16 LE, sum of bytes after FD FD)
Func: 1 read, 2 write, 3 write+read, 4 inc, 5 dec, 6 response.
Response data: `param value` (1 byte) by default, `FE n param value[n]` for n-byte values,
`FD param` = unsupported, `FF hi` changes the high byte of following parameter numbers.
"""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
from dataclasses import dataclass, field
from typing import Any

_LOGGER = logging.getLogger(__name__)

PORT = 4000
DEFAULT_PASSWORD = "1111"
SEARCH_ID = "DEFAULT_DEVICEID"

FUNC_READ = 0x01
FUNC_WRITE = 0x02
FUNC_WRITEREAD = 0x03
FUNC_RESPONSE = 0x06


class P:
    """Parameter numbers (Blauberg Smart Home table, low byte, high byte 0)."""

    ON_OFF = 0x01
    SPEED = 0x02  # 1,2,3, 0xFF manual
    BOOST_ACTIVE = 0x06  # read-only
    TIMER_MODE = 0x07  # 0 off, 1 night, 2 party
    TIMER_COUNTDOWN = 0x0B  # s, m, h
    HUMIDITY_SENSOR = 0x0F
    RELAY_SENSOR = 0x14
    ANALOG_SENSOR = 0x16
    HUMIDITY_THRESHOLD = 0x19  # 40..80 %
    HUMIDITY = 0x25
    # Speed step settings, 0..255, two per step (found by probing DUKA One type 14/27, confirmed against the DUKA app)
    SPEED1_EXHAUST = 0x3A
    SPEED1_SUPPLY = 0x3B
    SPEED2_EXHAUST = 0x3C
    SPEED2_SUPPLY = 0x3D
    SPEED3_EXHAUST = 0x3E
    SPEED3_SUPPLY = 0x3F
    MANUAL_SPEED = 0x44  # 0..255
    FAN1_RPM = 0x4A
    FAN2_RPM = 0x4B
    FILTER_INTERVAL = 0x63  # days, uint16 (DUKA app: 1..365)
    FILTER_COUNTDOWN = 0x64  # m, h, days(2)
    FILTER_RESET = 0x65
    BOOST_DELAY = 0x66  # 0..60 min
    RTC_TIME = 0x6F  # s, m, h
    RTC_DATE = 0x70  # day, weekday, month, year
    WEEKLY_SCHEDULE = 0x72
    SEARCH = 0x7C
    MACHINE_HOURS = 0x7E  # m, h, days(2)
    ALARM = 0x83  # 0 none, 1 alarm, 2 warning
    CLOUD = 0x85
    FIRMWARE = 0x86  # major, minor, day, month, year(2)
    FILTER_INDICATOR = 0x88
    WIFI_MODE = 0x94  # 1 client, 2 AP
    WIFI_IP = 0xA3
    VENT_MODE = 0xB7  # 0 ventilation(exhaust), 1 heat recovery, 2 supply
    UNIT_TYPE = 0xB9


# Everything the coordinator reads each cycle.
STATUS_PARAMS: tuple[int, ...] = (
    P.ON_OFF, P.SPEED, P.BOOST_ACTIVE, P.TIMER_MODE, P.TIMER_COUNTDOWN,
    P.HUMIDITY_SENSOR, P.RELAY_SENSOR, P.ANALOG_SENSOR, P.HUMIDITY_THRESHOLD,
    P.HUMIDITY, P.MANUAL_SPEED, P.FAN1_RPM, P.FAN2_RPM, P.FILTER_COUNTDOWN,
    P.SPEED1_EXHAUST, P.SPEED1_SUPPLY, P.SPEED2_EXHAUST, P.SPEED2_SUPPLY, P.SPEED3_EXHAUST, P.SPEED3_SUPPLY, P.FILTER_INTERVAL,
    P.BOOST_DELAY, P.RTC_TIME, P.RTC_DATE, P.WEEKLY_SCHEDULE, P.MACHINE_HOURS,
    P.ALARM, P.CLOUD, P.FILTER_INDICATOR, P.WIFI_MODE, P.VENT_MODE,
)
INFO_PARAMS: tuple[int, ...] = (P.FIRMWARE, P.UNIT_TYPE)


def u16(v: bytes) -> int:
    return v[0] | (v[1] << 8)


def decode(param: int, raw: bytes) -> Any:
    """Turn raw bytes into a usable Python value."""
    if param in (P.TIMER_COUNTDOWN,):
        return raw[0] + 60 * raw[1] + 3600 * raw[2]  # seconds
    if param in (P.FILTER_COUNTDOWN, P.MACHINE_HOURS):
        days = u16(raw[2:4]) if len(raw) >= 4 else raw[2]
        return days * 1440 + raw[1] * 60 + raw[0]  # minutes
    if param in (P.FAN1_RPM, P.FAN2_RPM, P.UNIT_TYPE, P.FILTER_INTERVAL):
        return u16(raw)
    if param == P.RTC_TIME:
        return f"{raw[2]:02d}:{raw[1]:02d}:{raw[0]:02d}"
    if param == P.RTC_DATE:
        return f"20{raw[3]:02d}-{raw[2]:02d}-{raw[0]:02d}"
    if param == P.FIRMWARE:
        return f"{raw[0]}.{raw[1]} ({u16(raw[4:6])}-{raw[3]:02d}-{raw[2]:02d})"
    if param == P.WIFI_IP:
        return ".".join(str(b) for b in raw)
    if param == P.SEARCH:
        return raw.decode("ascii", "replace")
    if len(raw) == 1:
        return raw[0]
    return raw.hex()


def build(device_id: str, password: str, func: int, data: bytes) -> bytes:
    body = (
        bytes([0x02, len(device_id)]) + device_id.encode("ascii")
        + bytes([len(password)]) + password.encode("ascii")
        + bytes([func]) + data
    )
    return b"\xfd\xfd" + body + struct.pack("<H", sum(body) & 0xFFFF)


def encode_write(param: int, value: bytes) -> bytes:
    if len(value) == 1:
        return bytes([param]) + value
    return bytes([0xFE, len(value), param]) + value


@dataclass
class Response:
    device_id: str
    func: int
    values: dict[int, Any] = field(default_factory=dict)
    unsupported: set[int] = field(default_factory=set)


def parse(pkt: bytes) -> Response | None:
    if len(pkt) < 8 or pkt[:2] != b"\xfd\xfd" or pkt[2] != 0x02:
        return None
    body = pkt[2:-2]
    if sum(body) & 0xFFFF != struct.unpack("<H", pkt[-2:])[0]:
        _LOGGER.debug("Checksum mismatch: %s", pkt.hex())
        return None
    i = 1
    n = body[i]; dev = body[i + 1:i + 1 + n].decode("ascii", "replace"); i += 1 + n
    n = body[i]; i += 1 + n
    func = body[i]; i += 1
    resp = Response(dev, func)
    data = body[i:]
    i = 0
    high = 0
    while i < len(data):
        p = data[i]; i += 1
        if p == 0xFF:
            high = data[i]; i += 1
            continue
        if p == 0xFD:
            resp.unsupported.add(high << 8 | data[i]); i += 1
            continue
        if p == 0xFE:
            size, p2 = data[i], data[i + 1]
            raw = data[i + 2:i + 2 + size]; i += 2 + size
            key = high << 8 | p2
        else:
            raw = data[i:i + 1]; i += 1
            key = high << 8 | p
        try:
            resp.values[key] = decode(key, raw)
        except (IndexError, ValueError):
            resp.values[key] = raw.hex()
    return resp


class _UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self, client: DukaClient) -> None:
        self.client = client

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        resp = parse(data)
        if resp is None:
            return
        self.client.dispatch(resp, addr[0])

    def error_received(self, exc: Exception) -> None:
        _LOGGER.debug("UDP error: %s", exc)


class DukaClient:
    """One shared UDP socket for all units; one outstanding request per device."""

    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        self._waiters: dict[str, asyncio.Future[tuple[Response, str]]] = {}
        self._search: list[tuple[str, str]] | None = None
        self._lock = asyncio.Lock()

    async def async_start(self) -> None:
        if self._transport is not None:
            return
        loop = asyncio.get_running_loop()
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(self), local_addr=("0.0.0.0", 0), allow_broadcast=True
        )

    def close(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None

    def dispatch(self, resp: Response, ip: str) -> None:
        if self._search is not None and resp.device_id != SEARCH_ID:
            self._search.append((resp.device_id, ip))
        fut = self._waiters.get(resp.device_id)
        if fut is not None and not fut.done():
            fut.set_result((resp, ip))

    async def request(
        self, ip: str, device_id: str, password: str, func: int, data: bytes, timeout: float = 3.0
    ) -> Response:
        await self.async_start()
        assert self._transport is not None
        async with self._lock:
            fut: asyncio.Future[tuple[Response, str]] = asyncio.get_running_loop().create_future()
            self._waiters[device_id] = fut
            try:
                self._transport.sendto(build(device_id, password, func, data), (ip, PORT))
                resp, _ = await asyncio.wait_for(fut, timeout)
            finally:
                self._waiters.pop(device_id, None)
        return resp

    async def read(self, ip: str, device_id: str, password: str, params: tuple[int, ...]) -> Response:
        return await self.request(ip, device_id, password, FUNC_READ, bytes(params))

    async def write(self, ip: str, device_id: str, password: str, param: int, value: bytes) -> Response:
        return await self.request(ip, device_id, password, FUNC_WRITEREAD, encode_write(param, value))

    async def write_noval(self, ip: str, device_id: str, password: str, param: int) -> Response:
        """Parameters written without a value (filter reset)."""
        return await self.request(ip, device_id, password, FUNC_WRITE, bytes([param]))

    async def search(self, wait: float = 2.0) -> list[tuple[str, str]]:
        """Broadcast discovery. Returns [(device_id, ip), ...]."""
        await self.async_start()
        assert self._transport is not None
        found: list[tuple[str, str]] = []
        self._search = found
        try:
            pkt = build(SEARCH_ID, "", FUNC_READ, bytes([P.SEARCH]))
            # Only the limited broadcast: "<broadcast>" raises WinError 10022 on Windows and
            # subnet broadcast did not reach all units in testing.
            # Units do not always answer the first broadcast; send twice.
            for _ in range(2):
                self._transport.sendto(pkt, ("255.255.255.255", PORT))
                await asyncio.sleep(wait / 2)
        finally:
            self._search = None
        uniq: dict[str, str] = {}
        for dev, ip in found:
            uniq.setdefault(dev, ip)
        return sorted(uniq.items())
