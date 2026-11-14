"""Read-only probe af DUKA One (Blauberg Vento Expert-protokol, UDP 4000). 2026-11-14.
Brug: py -3 duka/duka_read.py <ip> <device_id> [password]
Sender én READ-pakke (funktion 0x01) og dekoder svaret ud fra Blaubergs parametertabel.
Skriver INTET til enheden."""
import socket, sys, struct

FUNC_READ, FUNC_RESP = 0x01, 0x06

# parameter -> (navn, bytes i svar, dekoder)
def b(v): return v[0]
def onoff(v): return {0: "off", 1: "on"}.get(v[0], v[0])
def u16(v): return v[0] | v[1] << 8
PARAMS = {
    0x01: ("on_off", 1, onoff),
    0x02: ("speed", 1, lambda v: {1: "1", 2: "2", 3: "3", 0xFF: "manual"}.get(v[0], v[0])),
    0x06: ("boost_active", 1, onoff),
    0x07: ("timer_mode", 1, lambda v: {0: "off", 1: "night", 2: "party"}.get(v[0], v[0])),
    0x0B: ("timer_countdown", 3, lambda v: f"{v[2]}h {v[1]}m {v[0]}s"),
    0x0F: ("humidity_sensor", 1, onoff),
    0x14: ("relay_sensor", 1, onoff),
    0x16: ("analog_0_10v_sensor", 1, onoff),
    0x19: ("humidity_threshold_pct", 1, b),
    0x25: ("humidity_pct", 1, b),
    0x44: ("manual_speed_0_255", 1, b),
    0x4A: ("fan1_rpm", 2, u16),
    0x4B: ("fan2_rpm", 2, u16),
    0x64: ("filter_countdown", 3, lambda v: f"{v[2]} dage {v[1]}h {v[0]}m"),
    0x66: ("boost_delay_min", 1, b),
    0x6F: ("rtc_time", 3, lambda v: f"{v[2]:02d}:{v[1]:02d}:{v[0]:02d}"),
    0x70: ("rtc_date", 4, lambda v: f"20{v[3]:02d}-{v[2]:02d}-{v[0]:02d} (ugedag {v[1]})"),
    0x72: ("weekly_schedule", 1, onoff),
    0x7E: ("machine_hours", 4, lambda v: f"{u16(v[2:4])} dage {v[1]}h {v[0]}m"),
    0x83: ("alarm_indicator", 1, lambda v: {0: "none", 1: "alarm", 2: "warning"}.get(v[0], v[0])),
    0x85: ("cloud_server", 1, onoff),
    0x86: ("firmware", 6, lambda v: f"{v[0]}.{v[1]} ({v[2]:02d}.{v[3]:02d}.{u16(v[4:6])})"),
    0x88: ("filter_replacement_indicator", 1, onoff),
    0x94: ("wifi_mode", 1, lambda v: {1: "client", 2: "AP"}.get(v[0], v[0])),
    0xB7: ("ventilation_mode", 1, lambda v: {0: "ventilation(udsugning)", 1: "heat_recovery(regeneration)", 2: "air_supply(indtræk)"}.get(v[0], v[0])),
    0xB9: ("unit_type", 2, u16),
}

def build(dev_id: str, pw: str, params):
    body = bytes([0x02, len(dev_id)]) + dev_id.encode() + bytes([len(pw)]) + pw.encode() + bytes([FUNC_READ]) + bytes(params)
    chk = sum(body) & 0xFFFF
    return b"\xfd\xfd" + body + struct.pack("<H", chk)

def parse(pkt: bytes):
    assert pkt[:2] == b"\xfd\xfd", "ikke FD FD"
    body, chk = pkt[2:-2], struct.unpack("<H", pkt[-2:])[0]
    assert sum(body) & 0xFFFF == chk, "checksum fejl"
    i = 1
    n = body[i]; dev = body[i+1:i+1+n].decode(); i += 1 + n
    n = body[i]; i += 1 + n  # password echo
    func = body[i]; i += 1
    out, high = {}, 0
    data = body[i:]
    i = 0
    while i < len(data):
        p = data[i]; i += 1
        if p == 0xFF:  # skift high byte
            high = data[i]; i += 1; continue
        if p == 0xFE:  # variabel størrelse: FE size param value...
            size = data[i]; p2 = data[i+1]; val = data[i+2:i+2+size]; i += 2 + size
            out[f"0x{high:02X}{p2:02X}"] = (PARAMS.get(p2, (f"param_{p2:02X}", size, bytes.hex))[0], val.hex())
            continue
        if p == 0xFD:  # parameter ikke understøttet
            p2 = data[i]; i += 1
            out[f"0x{high:02X}{p2:02X}"] = (PARAMS.get(p2, (f"param_{p2:02X}",))[0], "IKKE UNDERSTØTTET")
            continue
        name, size, dec = PARAMS.get(p, (f"param_{p:02X}", 1, bytes.hex))
        val = data[i:i+size]; i += size
        try:
            out[f"0x{high:02X}{p:02X}"] = (name, dec(val))
        except Exception as e:
            out[f"0x{high:02X}{p:02X}"] = (name, f"raw {val.hex()} ({e})")
    return dev, func, out

def main():
    ip, dev_id = sys.argv[1], sys.argv[2]
    pw = sys.argv[3] if len(sys.argv) > 3 else "1111"
    params = sorted(PARAMS)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(3)
    s.sendto(build(dev_id, pw, params), (ip, 4000))
    pkt, addr = s.recvfrom(1024)
    print(f"svar fra {addr}, {len(pkt)} bytes, raw: {pkt.hex()}")
    dev, func, out = parse(pkt)
    print(f"device {dev}, funktion 0x{func:02X} ({'response' if func == FUNC_RESP else '?'})")
    for k, (name, val) in out.items():
        print(f"  {k} {name:32s} {val}")

if __name__ == "__main__":
    main()
