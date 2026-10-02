#!/usr/bin/env python3
import argparse, base64, calendar, hashlib, hmac, json, math, os, re, secrets, shutil, socket, subprocess, sys, time, uuid

PROTO = "TRDAP/1.0"
MAX_BYTES = 512
DEFAULT_PORT = 47474

READ, UNAVAILABLE, DENIED, TIMEOUT, PARSE_FAIL = "READ", "UNAVAILABLE", "DENIED", "TIMEOUT", "PARSE_FAIL"

CHANNELS = {
    "batt_pct":     ("%",     0.5,  1),
    "batt_temp":    ("C",     0.3,  3),
    "cell_dbm":     ("dBm",   2.0,  1),
    "cell_n":       ("count", 0.5,  2),
    "wifi_rssi":    ("dBm",   2.0,  4),
    "wifi_ap_n":    ("count", 1.0,  2),
    "pressure":     ("hPa",   0.15, 1),
    "light":        ("lux",   5.0,  5),
    "mag_uT":       ("uT",    1.5,  4),
    "accel_rms":    ("m/s2",  0.05, 5),
}
DERIVED = {
    "batt_rate":    ("%/h",    1),
    "p_tend_3h":    ("hPa/3h", 1),   # weather-front indicator; flagged at |P_TEND_FLAG|
}
P_TEND_FLAG = 3.0   # hPa per 3 h. conventional "rapidly rising/falling" cut; stipulated, not fitted

class Reading:
    __slots__ = ("ch", "value", "status", "t")
    def __init__(self, ch, value, status, t):
        self.ch, self.value, self.status, self.t = ch, value, status, t

def _run_json(cmd, timeout=12):
    if shutil.which(cmd[0]) is None:
        return None, UNAVAILABLE
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, TIMEOUT
    out = (p.stdout or "").strip()
    if not out:
        err = (p.stderr or "").lower()
        return None, DENIED if "permission" in err else UNAVAILABLE
    try:
        return json.loads(out), READ
    except ValueError:
        return None, PARSE_FAIL

def probe_battery(t):
    obj, st = _run_json(["termux-battery-status"])
    if st == READ:
        return [Reading("batt_pct", obj.get("percentage"), READ, t),
                Reading("batt_temp", obj.get("temperature"), READ, t)]
    try:
        with open("/sys/class/power_supply/battery/capacity") as f:
            return [Reading("batt_pct", float(f.read().strip()), READ, t),
                    Reading("batt_temp", None, st, t)]
    except PermissionError:
        st2 = DENIED
    except (OSError, ValueError):
        st2 = st
    return [Reading("batt_pct", None, st2, t), Reading("batt_temp", None, st, t)]

def probe_cell(t):
    obj, st = _run_json(["termux-telephony-cellinfo"])
    if st != READ or not isinstance(obj, list):
        st = st if st != READ else PARSE_FAIL
        return [Reading("cell_dbm", None, st, t), Reading("cell_n", None, st, t)]
    reg = [c.get("dbm") for c in obj if c.get("registered") and c.get("dbm") is not None]
    return [Reading("cell_dbm", max(reg) if reg else None, READ if reg else UNAVAILABLE, t),
            Reading("cell_n", len(obj), READ, t)]

def probe_wifi(t):
    out = []
    obj, st = _run_json(["termux-wifi-connectioninfo"])
    rssi = obj.get("rssi") if st == READ else None
    if rssi is not None and rssi <= -127:
        rssi, st = None, UNAVAILABLE
    out.append(Reading("wifi_rssi", rssi, st if rssi is not None or st != READ else UNAVAILABLE, t))
    obj, st = _run_json(["termux-wifi-scaninfo"], timeout=20)
    out.append(Reading("wifi_ap_n", len(obj) if st == READ and isinstance(obj, list) else None,
                       st if st != READ or isinstance(obj, list) else PARSE_FAIL, t))
    return out

SENSOR_MATCH = {"pressure": "pressure", "light": "light", "mag_uT": "magnet", "accel_rms": "accel"}

def probe_sensors(t):
    out = []
    for ch, key in SENSOR_MATCH.items():
        obj, st = _run_json(["termux-sensor", "-s", key, "-n", "1"], timeout=10)
        val = None
        if st == READ and isinstance(obj, dict) and obj:
            vals = next(iter(obj.values())).get("values") or []
            if not vals:
                st = UNAVAILABLE
            elif ch in ("mag_uT", "accel_rms"):
                val = math.sqrt(sum(v * v for v in vals[:3]))
            else:
                val = vals[0]
        elif st == READ:
            st = UNAVAILABLE
        out.append(Reading(ch, val, st if val is not None else (st if st != READ else UNAVAILABLE), t))
    return out

def probe_location(t):
    obj, st = _run_json(["termux-location", "-p", "network", "-r", "last"], timeout=15)
    if st == READ and "latitude" in obj:
        return (round(obj["latitude"], 3), round(obj["longitude"], 3))
    return None

LIVE_PROBES = [probe_battery, probe_cell, probe_wifi, probe_sensors]

class Baseline:
    def __init__(self, floor, alpha=0.1, warmup=12):
        self.floor, self.alpha, self.warmup = floor, alpha, warmup
        self.mean, self.dev, self.n = None, 0.0, 0

    def step(self, x):
        if self.mean is None:
            self.mean, self.n = x, 1
            return "WARMUP", 0.0
        d = x - self.mean
        z = d / max(self.dev, self.floor)
        warm = self.n < self.warmup
        self.mean += self.alpha * d
        self.dev = (1 - self.alpha) * self.dev + self.alpha * abs(d)
        self.n += 1
        if warm:
            return "WARMUP", z
        return ("SHIFT" if abs(z) > 4.0 else "ok"), z

class Slope:
    def __init__(self, window_s):
        self.w, self.pts = window_s, []

    def add(self, t, x):
        self.pts.append((t, x))
        self.pts = [p for p in self.pts if t - p[0] <= self.w]

    def per_hour(self):
        if len(self.pts) < 3 or self.pts[-1][0] - self.pts[0][0] < self.w * 0.25:
            return None
        n = len(self.pts)
        mt = sum(p[0] for p in self.pts) / n
        mx = sum(p[1] for p in self.pts) / n
        den = sum((p[0] - mt) ** 2 for p in self.pts)
        if den == 0:
            return None
        return sum((p[0] - mt) * (p[1] - mx) for p in self.pts) / den * 3600.0

class Monitor:
    def __init__(self):
        self.base = {ch: Baseline(spec[1]) for ch, spec in CHANNELS.items()}
        self.last_status = {}
        self.last_live = {}       # ch -> True iff a value arrived last cycle
        self.batt = Slope(3 * 3600)
        self.press = Slope(3 * 3600)

    def ingest(self, readings):
        rows = {}
        for r in readings:
            prev = self.last_live.get(r.ch, False)
            live = r.status == READ and r.value is not None
            if live:
                flag, z = self.base[r.ch].step(float(r.value))
                rows[r.ch] = {"v": round(float(r.value), 2), "st": READ, "flag": flag, "z": round(z, 2)}
                if r.ch == "batt_pct":
                    self.batt.add(r.t, float(r.value))
                if r.ch == "pressure":
                    self.press.add(r.t, float(r.value))
            else:
                flag = "DROPOUT" if prev else None
                # a READ carrying no value is a probe defect; name it rather than file it as read
                rows[r.ch] = {"v": None, "st": r.status if r.status != READ else PARSE_FAIL, "flag": flag, "z": None}
            self.last_status[r.ch] = r.status
            self.last_live[r.ch] = live
        br, pr = self.batt.per_hour(), self.press.per_hour()
        rows["batt_rate"] = {"v": None if br is None else round(br, 2), "st": READ if br is not None else "SPAN_SHORT"}
        pt = None if pr is None else pr * 3
        pflag = None if pt is None else ("FALLING_FAST" if pt <= -P_TEND_FLAG else "RISING_FAST" if pt >= P_TEND_FLAG else "ok")
        rows["p_tend_3h"] = {"v": None if pt is None else round(pt, 2), "st": READ if pt is not None else "SPAN_SHORT", "flag": pflag}
        return rows

def _prio(ch):
    return CHANNELS[ch][2] if ch in CHANNELS else DERIVED[ch][1]

def build_announce(node, rows, loc=None, hub_status="operational", now=None, reserve=0):
    now = now or time.gmtime()
    hub = {"id": node, "type": "x_mobile_node", "status": hub_status}
    if loc:
        hub["location"] = {"lat": loc[0], "lon": loc[1]}
    sig, unread = {}, []
    for ch, r in rows.items():
        if r["v"] is None:
            unread.append(ch)
        else:
            f = r.get("flag")
            sig[ch] = [r["v"], f] if f and f not in ("ok", "WARMUP") else r["v"]
    msg = {"protocol": PROTO, "message_id": str(uuid.uuid4()), "type": "ANNOUNCE",
           "from": node, "to": "ALL", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", now),
           "ttl": 2, "data": {"hub": hub, "x_sig": sig, "x_unread": unread, "x_trunc": 0}}

    def size():
        return len(json.dumps(msg, separators=(",", ":")).encode())

    # drop order: flagless signals by priority, then unread names, then flagged.
    # the absence record outranks an unflagged level because the RULE is that it is carried.
    order = sorted([c for c in sig if not isinstance(sig[c], list)], key=_prio, reverse=True)
    order += sorted(unread, key=_prio, reverse=True)
    order += sorted([c for c in sig if isinstance(sig[c], list)], key=_prio, reverse=True)
    for ch in order:
        if size() + reserve <= MAX_BYTES:
            break
        if ch in msg["data"]["x_unread"]:
            msg["data"]["x_unread"].remove(ch)
        else:
            del msg["data"]["x_sig"][ch]
        msg["data"]["x_trunc"] += 1
    return msg, size()

def send(wire, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        s.sendto(wire, ("255.255.255.255", port))
        return "SENT"
    except OSError as e:
        return "SEND_FAIL:%s" % e.errno
    finally:
        s.close()

TRAILER_RE = re.compile(rb',"x_kid":"([0-9a-f]{8})","x_mac":"([A-Za-z0-9_-]{22})"\}$')
TRAILER_LEN = len(b',"x_kid":"00000000","x_mac":"' + b"A" * 22 + b'"}')
TRAILER_ADD = TRAILER_LEN - 1   # the trailer replaces the body's closing brace

VERIFIED, UNSIGNED, UNKNOWN_KEY, BAD_MAC, BAD_JSON, STALE, FUTURE, REPLAY, NO_TIMESTAMP, BAD_TRAILER = (
    "VERIFIED", "UNSIGNED", "UNKNOWN_KEY", "BAD_MAC", "BAD_JSON", "STALE", "FUTURE", "REPLAY",
    "NO_TIMESTAMP", "BAD_TRAILER")

def kid_of(key):
    return hashlib.sha256(key).hexdigest()[:8]

def _tag(key, body):
    return base64.urlsafe_b64encode(hmac.new(key, body, hashlib.sha256).digest()[:16]).rstrip(b"=")

def sign(msg, key):
    body = json.dumps(msg, separators=(",", ":")).encode()
    wire = body[:-1] + b',"x_kid":"' + kid_of(key).encode() + b'","x_mac":"' + _tag(key, body) + b'"}'
    return wire

def load_key(path):
    with open(path) as f:
        k = bytes.fromhex(f.read().strip())
    if len(k) < 16:
        raise ValueError("key shorter than 128 bits")
    return k

def genkey(path):
    if os.path.exists(path):
        raise SystemExit("refusing to overwrite %s" % path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(secrets.token_bytes(32).hex() + "\n")
    print("wrote %s  kid=%s  (copy this file to every node in the group, by hand)" % (path, kid_of(load_key(path))))

def _parse_ts(s):
    try:
        # timegm, not mktime: the stamp is UTC and mktime reads local time, off by 3600 s under DST
        return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return None

class Verifier:
    def __init__(self, keys, max_age=300, max_future=60):
        self.keys = {kid_of(k): k for k in keys}
        self.max_age, self.max_future = max_age, max_future
        self.seen = {}

    def check(self, wire, now=None):
        now = time.time() if now is None else now
        m = TRAILER_RE.search(wire)
        if not m:
            if b'"x_kid":' in wire or b'"x_mac":' in wire:
                return BAD_TRAILER, None   # signed and damaged in transit, not an unsigned peer
            try:
                return UNSIGNED, json.loads(wire)
            except ValueError:
                return BAD_JSON, None
        kid, tag = m.group(1).decode(), m.group(2)
        key = self.keys.get(kid)
        if key is None:
            return UNKNOWN_KEY, None
        body = wire[:m.start()] + b"}"
        if not hmac.compare_digest(_tag(key, body), tag):
            return BAD_MAC, None
        try:
            msg = json.loads(body)
        except ValueError:
            return BAD_JSON, None
        ts = _parse_ts(msg.get("timestamp"))
        if ts is None:
            return NO_TIMESTAMP, msg   # absent is not late
        if now - ts > self.max_age:
            return STALE, msg
        if ts - now > self.max_future:
            return FUTURE, msg
        mid = msg.get("message_id")
        if mid in self.seen:
            return REPLAY, msg
        self.seen[mid] = ts
        cut = now - 2 * self.max_age
        if len(self.seen) > 4096:
            self.seen = {i: t for i, t in self.seen.items() if t > cut}
        return VERIFIED, msg

class LogLimiter:
    """per (addr, status) at most `burst` lines per `window` s; the rest are counted and
    flushed as one summary line, so a flood costs bytes once per window, not once per packet."""
    def __init__(self, burst=10, window=60.0):
        self.burst, self.window, self.win = burst, window, {}

    def admit(self, addr, status, now):
        """returns (write_this_line, summary_or_None)"""
        k = (addr, status)
        start, n, dropped = self.win.get(k, (now, 0, 0))
        summary = None
        if now - start >= self.window:
            if dropped:
                summary = {"addr": addr, "status": status, "suppressed": dropped,
                           "window_s": round(now - start, 1)}
            start, n, dropped = now, 0, 0
        n += 1
        if n > self.burst:
            dropped += 1
            self.win[k] = (start, n, dropped)
            return False, summary
        self.win[k] = (start, n, dropped)
        return True, summary

def listen(port, keys, max_age, logpath):
    v, lim = Verifier(keys, max_age), LogLimiter()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", port))
    print("listening udp/%d  keys=%s" % (port, ",".join(v.keys) or "none"))
    while True:
        wire, addr = s.recvfrom(2048)
        now = time.time()
        st, msg = v.check(wire, now)
        frm = msg.get("from") if isinstance(msg, dict) else None
        write, summary = (True, None) if st == VERIFIED else lim.admit(addr[0], st, now)
        with open(logpath, "a") as f:
            if summary:
                f.write(json.dumps({"t": round(now, 1), "summary": summary}) + "\n")
            if write:
                f.write(json.dumps({"t": round(now, 1), "addr": addr[0], "status": st,
                                    "from": frm, "bytes": len(wire),
                                    "msg": msg if st == VERIFIED else None}) + "\n")
        if write:
            print("%-12s %-15s %-10s %dB" % (st, addr[0], frm, len(wire)))

class SimProbes:
    def __init__(self, dt):
        self.k, self.dt = 0, dt

    def __call__(self, t):
        k = self.k = self.k + 1
        jit = lambda a: a * math.sin(k * 1.7)
        r = [Reading("batt_pct", 90 - k * 0.2, READ, t),
             Reading("batt_temp", 31 + jit(0.2), READ, t),
             # 3 hPa/h is a severe real front. below SHIFT's reach by design; p_tend_3h carries it.
             Reading("pressure", 1013 + jit(0.05) - (3.0 / 3600 * self.dt * (k - 30) if k > 30 else 0), READ, t),
             Reading("wifi_ap_n", 14 + round(jit(1)) if k < 40 else 1, READ, t),
             Reading("cell_n", 4 if k < 50 else 0, READ, t),
             Reading("cell_dbm", -95 + jit(2) if k < 50 else None, READ if k < 50 else UNAVAILABLE, t),
             Reading("light", None, UNAVAILABLE, t)]
        return r

def run(node, interval, cycles, simulate, do_send, port, logpath, key=None):
    mon, sim = Monitor(), (SimProbes(interval) if simulate else None)
    t0 = time.time()
    k = 0
    while cycles <= 0 or k < cycles:
        t = t0 + k * interval if simulate else time.time()
        cycle_start = time.time()
        readings = sim(t) if simulate else [r for p in LIVE_PROBES for r in p(t)]
        loc = None if simulate else probe_location(t)
        rows = mon.ingest(readings)
        msg, _ = build_announce(node, rows, loc, now=time.gmtime(t),
                                reserve=TRAILER_ADD if key else 0)
        wire = sign(msg, key) if key else json.dumps(msg, separators=(",", ":")).encode()
        n = len(wire)
        tx = send(wire, port) if do_send else "NOT_SENT"
        with open(logpath, "a") as f:
            f.write(json.dumps({"t": round(t, 1), "rows": rows, "bytes": n, "tx": tx,
                                "signed": bool(key), "probe_s": round(time.time() - cycle_start, 1)}) + "\n")
        flags = {c: r["flag"] for c, r in rows.items() if r.get("flag") not in (None, "ok", "WARMUP")}
        print("%04d %4dB %-9s %s" % (k, n, tx[:9], flags if flags else "-"))
        k += 1
        if not simulate:
            # probe timeouts can sum past the interval (~111 s worst case); hold the period where possible
            time.sleep(max(0.0, interval - (time.time() - cycle_start)))

def selftest():
    res = []
    def case(name, ok):
        res.append((name, ok)); print(("PASS " if ok else "FAIL ") + name)

    b = Baseline(0.15)
    flags = [b.step(1013 + 0.05 * math.sin(i))[0] for i in range(12)]
    case("T1 no flag during warmup", all(f == "WARMUP" for f in flags[:12]))
    for i in range(20):
        b.step(1013 + 0.05 * math.sin(i))
    case("T2 10 hPa step flagged SHIFT", b.step(1003.0)[0] == "SHIFT")
    m = Monitor()
    m.ingest([Reading("pressure", 1013.0, READ, 0)])
    rows = m.ingest([Reading("pressure", None, UNAVAILABLE, 60)])
    case("T3 unread is None not 0, DROPOUT flagged",
         rows["pressure"]["v"] is None and rows["pressure"]["flag"] == "DROPOUT")
    case("T4 baseline untouched by unread", m.base["pressure"].n == 1)
    s = Slope(3 * 3600)
    for i in range(13):
        s.add(i * 900, 1013 - i * 0.25)
    case("T5 slope -1 hPa/h -> -3 hPa/3h", abs(s.per_hour() * 3 + 3.0) < 1e-6)
    s2 = Slope(3 * 3600); s2.add(0, 1); s2.add(60, 1)
    case("T6 short span returns None", s2.per_hour() is None)
    rows = {c: {"v": -123.45, "st": READ, "flag": "SHIFT"} for c in CHANNELS}
    rows.update({c: {"v": -1.23, "st": READ} for c in DERIVED})
    msg, n = build_announce("NODE-LONG-IDENTIFIER-01", rows, (44.123, -90.456))
    case("T7 packet <= 512 B", n <= MAX_BYTES)
    kept = len(msg["data"]["x_sig"]) + len(msg["data"]["x_unread"])
    case("T8 drops counted: kept + x_trunc == total",
         kept + msg["data"]["x_trunc"] == len(rows))
    rows = {"pressure": {"v": None, "st": TIMEOUT}, "cell_n": {"v": 0, "st": READ, "flag": "ok"}}
    msg, _ = build_announce("N", rows)
    case("T9 real zero sent as 0, unread listed separately",
         msg["data"]["x_sig"].get("cell_n") == 0 and "pressure" in msg["data"]["x_unread"])

    key, other = bytes(range(32)), bytes(range(1, 33))
    now = time.time()
    msg, _ = build_announce("TRK01", {"pressure": {"v": 1012.4, "st": READ, "flag": "ok"}},
                            now=time.gmtime(now), reserve=TRAILER_LEN)
    wire = sign(msg, key)
    v = Verifier([key])
    case("T10 signed packet verifies", v.check(wire, now)[0] == VERIFIED)
    case("T11 same packet again -> REPLAY", v.check(wire, now)[0] == REPLAY)
    i = wire.index(b"1012.4")
    flipped = wire[:i] + b"9" + wire[i + 1:]
    case("T12 one byte changed -> BAD_MAC", Verifier([key]).check(flipped, now)[0] == BAD_MAC)
    case("T13 key not held -> UNKNOWN_KEY", Verifier([other]).check(wire, now)[0] == UNKNOWN_KEY)
    case("T14 400 s old -> STALE", Verifier([key]).check(wire, now + 400)[0] == STALE)
    case("T15 120 s ahead -> FUTURE", Verifier([key]).check(wire, now - 120)[0] == FUTURE)
    plain = json.dumps(msg, separators=(",", ":")).encode()
    case("T16 unsigned reported UNSIGNED, not dropped", Verifier([key]).check(plain, now)[0] == UNSIGNED)
    v2 = Verifier([key])
    v2.check(flipped, now)
    case("T17 forged packet does not enter replay cache", v2.check(wire, now)[0] == VERIFIED)
    case("T18 trailer length constant", len(wire) - len(plain) + 1 == TRAILER_LEN)
    rows = {c: {"v": -123.45, "st": READ, "flag": "SHIFT"} for c in CHANNELS}
    rows.update({c: {"v": -1.23, "st": READ} for c in DERIVED})
    msg, _ = build_announce("NODE-LONG-IDENTIFIER-01", rows, (44.123, -90.456), reserve=TRAILER_LEN)
    w = sign(msg, key)
    case("T19 worst case signed packet <= 512 B", len(w) <= MAX_BYTES)
    case("T20 worst case still verifies", Verifier([key]).check(w, time.time())[0] == VERIFIED)
    # --- repairs, each pinned
    old = os.environ.get("TZ")
    try:
        os.environ["TZ"] = "America/Chicago"; time.tzset()
        case("T21 UTC stamp parses to the same instant in a DST zone",
             _parse_ts("2026-07-01T12:00:00Z") == 1782907200)   # date -u -d 2026-07-01T12:00:00Z +%s
        case("T22 fresh packet verifies in a DST zone", Verifier([key]).check(wire, now)[0] == VERIFIED)
    finally:
        if old is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old
        time.tzset()
    m2 = dict(msg); del m2["timestamp"]
    case("T23 missing stamp -> NO_TIMESTAMP, not STALE",
         Verifier([key]).check(sign(m2, key), now)[0] == NO_TIMESTAMP)
    case("T24 damaged trailer -> BAD_TRAILER, not BAD_JSON",
         Verifier([key]).check(wire[:-6] + b'AAAAA}', now)[0] == BAD_TRAILER)
    case("T25 junk still BAD_JSON", Verifier([key]).check(b"\xff\x00junk", now)[0] == BAD_JSON)
    lim = LogLimiter(burst=10, window=60)
    writes = sum(1 for i in range(100) if lim.admit("10.0.0.9", BAD_MAC, 1000.0 + i * 0.1)[0])
    w2, summ = lim.admit("10.0.0.9", BAD_MAC, 1100.0)
    case("T26 100 BAD_MAC in one window -> 10 lines, summary counts 90",
         writes == 10 and w2 and bool(summ) and summ["suppressed"] == 90)
    case("T27 another source not throttled by the first", lim.admit("10.0.0.8", BAD_MAC, 1000.5)[0])
    mm = Monitor()
    for i in range(13):
        mm.ingest([Reading("pressure", 1013 - i * 0.25, READ, i * 900)])
    r = mm.ingest([Reading("pressure", 1013 - 13 * 0.25, READ, 13 * 900)])
    case("T28 -1 hPa/h front flags FALLING_FAST on p_tend_3h", r["p_tend_3h"].get("flag") == "FALLING_FAST")
    mm = Monitor()
    mm.ingest([Reading("batt_pct", 80, READ, 0)])
    fl = [mm.ingest([Reading("batt_pct", None, READ, 60 * i)])["batt_pct"]["flag"] for i in (1, 2, 3)]
    case("T29 READ with no value: DROPOUT once, then quiet", fl == ["DROPOUT", None, None])
    rows = {c: {"v": 1234.56, "st": READ, "flag": "ok"} for c in CHANNELS}
    rows.update({c: {"v": -12.34, "st": READ} for c in DERIVED})
    rows["light"] = {"v": None, "st": DENIED}
    msg2, _ = build_announce("NODE-LONG-IDENTIFIER-01", rows, (44.123, -90.456))
    case("T30 under byte pressure a flagless level drops before the absence record",
         msg2["data"]["x_trunc"] > 0 and "light" in msg2["data"]["x_unread"])
    rows = {c: {"v": -123.45, "st": READ, "flag": "SHIFT"} for c in CHANNELS}
    rows.update({c: {"v": -1.23, "st": READ} for c in DERIVED})
    msg3, body = build_announce("NODE-LONG-IDENTIFIER-01", rows, (44.123, -90.456), reserve=TRAILER_ADD)
    w3 = sign(msg3, key)
    case("T31 reserve = bytes the trailer adds; wire <= 512 and body + add == wire",
         len(w3) <= MAX_BYTES and body + TRAILER_ADD == len(w3))

    bad = sum(1 for _, ok in res if not ok)
    print("%d/%d pass" % (len(res) - bad, len(res)))
    return bad == 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="NODE01")
    ap.add_argument("--interval", type=float, default=60)
    ap.add_argument("--cycles", type=int, default=0)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--log", default="trdap_signals.jsonl")
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--no-send", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--key", action="append", default=[])
    ap.add_argument("--genkey", metavar="PATH")
    ap.add_argument("--listen", action="store_true")
    ap.add_argument("--max-age", type=float, default=300)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.genkey:
        genkey(a.genkey); sys.exit(0)
    keys = [load_key(p) for p in a.key]
    if a.listen:
        listen(a.port, keys, a.max_age, "trdap_rx.jsonl" if a.log == "trdap_signals.jsonl" else a.log)
    else:
        run(a.node, a.interval, a.cycles, a.simulate, not a.no_send and not a.simulate,
            a.port, a.log, keys[0] if keys else None)
