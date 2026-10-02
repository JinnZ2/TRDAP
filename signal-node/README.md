# signal-node

`trdap_signal_node.py` is an ambient-signal node for an old phone in Termux:
probes (battery, cell, wifi, pressure, light, magnetometer, accelerometer)
through a per-channel baseline and detector, into a TRDAP ANNOUNCE under
512 bytes with an HMAC trailer (README 8.2), plus a verifying listener.
Stdlib only, CC0.

```
python3 signal-node/trdap_signal_node.py --selftest           # 31 cases
python3 signal-node/trdap_signal_node.py --simulate --cycles 90
python3 signal-node/trdap_signal_node.py --genkey group.key
python3 signal-node/trdap_signal_node.py --node TRK01 --key group.key
python3 signal-node/trdap_signal_node.py --listen --key group.key
```

## Provenance

The node arrived as two pasted revisions (unsigned, then with the HMAC
trailer and listener) and was run as delivered before anything moved.
`REPAIRS.patch` is the diff from the second revision to the file here,
taken against a transcription with comments stripped, so the hunks carry
the code and not the delivered comments. Ten repairs, each pinned by a
selftest case (T21..T31) that fails on the delivered code:

| id | site | repair | pin |
|----|------|--------|-----|
| F1 | `_parse_ts` | `calendar.timegm`; `mktime - timezone` read 3600 s off under DST, so a listener in a DST zone returned STALE on every peer | T21 T22 |
| F2 | `Verifier` | `NO_TIMESTAMP`: an absent stamp is not a late one | T23 |
| F3 | `Verifier` | `BAD_TRAILER`: a signed packet damaged in transit is not junk | T24 T25 |
| F4 | `listen` | `LogLimiter`, 10 lines per (addr, status) per 60 s, the rest counted into one summary line (8.2 item 4, receive side) | T26 T27 |
| F5 | `Monitor` | `p_tend_3h` carries `FALLING_FAST` / `RISING_FAST` at 3 hPa per 3 h; `P_TEND_FLAG` is stipulated, not fitted | T28 |
| F6 | `Monitor` | `DROPOUT` keyed on a value having arrived, not on the status word; a READ with no value files as `PARSE_FAIL` | T29 |
| F7 | `build_announce` | drop order: flagless levels, then unread names, then flagged; the absence record outranks an unflagged level | T30 |
| F8 | `run` | reserve is the 45 bytes the trailer adds, since it replaces the closing brace | T31 |
| F9 | `run` | sleep for what is left of the interval; `probe_s` logged per cycle | none |
| F10 | `SimProbes` | the simulated front runs at 3 hPa/h, a severe real one; 24 hPa/h was eight times anything the atmosphere does | none |

Under `TZ=America/Chicago` the delivered selftest reads 15/20. The patched
file reads 31/31 in UTC, Chicago, Berlin, Sydney and Kolkata.

## Standing limits, not repaired

- `SHIFT` is an edge detector with an adaptive baseline. It does not see
  a real pressure front (0 flags at 6 hPa/h) and after a large step its
  deviation estimate masks a reversal for about 40 cycles. The slope path
  carries fronts; the masking is a tuning decision.
- The replay cache is process memory. A listener restart accepts one
  replay of anything inside `max_age`.
- `Baseline` runs per sample and `Slope` per second. Probe timeouts sum
  to about 111 s against a 60 s interval, so the two clocks part under
  slow probes; F9 holds the period where it can.
- `x_trunc` is one count. A receiver with the shared channel schema can
  recover which names were cut; one without it cannot.
- `DEFAULT_PORT` 47474 is a placeholder; draft-00 names no port.
- `x_mobile_node`, `x_sig`, `x_unread`, `x_kid`, `x_mac` are extensions.
  The ANNOUNCE in README 4.3 carries `capabilities` and `resource_summary`;
  this packet carries neither.
