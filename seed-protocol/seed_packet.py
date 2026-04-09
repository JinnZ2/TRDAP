"""
seed_packet.py — Unified packet layer with version fallback chain.

Packet versions (in degradation order):

  v2 (21 bytes) — full: seed + position + neighbor hint + CRC
   ↓ fallback
  v1 (13 bytes) — minimal: seed + energy + epoch + CRC
   ↓ fallback
  v_raw (44-48 bytes) — raw floats, no encoding, no CRC
                         Used when bandwidth is available but
                         encoding overhead isn't worth it (LAN/UDP)

Each version's pack/unpack is explicitly namespaced. The auto_pack()
and auto_unpack() functions handle version negotiation and fallback.

Fallback logic:
  - Pack: use the most compact format the data supports
  - Unpack: detect version from header byte, fall through if corrupt

All versions import encoding/decoding from seed_core.py.

License: CC0 1.0
"""

import struct
import zlib
import numpy as np

from seed_core import (
    encode_seed, decode_seed,
    position_to_anchor_offset, anchor_offset_to_position,
    encode_neighbor_hint, decode_neighbor_hint,
)

# =============================================================================
# VERSION CONSTANTS
# =============================================================================

V1 = 1
V2 = 2
V_RAW = 0  # raw float format (no version header)

# Ordered from most preferred to least
FALLBACK_CHAIN = [V2, V1, V_RAW]

# =============================================================================
# V1 — Minimal (13 bytes)
# =============================================================================
# Offset  Size  Field
# 0       1     Version (uint8) = 1
# 1       1     Frame ID (uint8)
# 2       1     Flags (uint8)
# 3       5     Seed (5 × uint8, 6th implicit)
# 8       1     Energy Hint (uint8)
# 9       2     Epoch (uint16)
# 11      2     CRC16

_V1_FMT_NOCRC = ">BBB5sBH"
_V1_FMT_FULL  = ">BBB5sBHH"
_V1_SIZE = struct.calcsize(_V1_FMT_FULL)  # 13 bytes


def pack_v1(seed, frame_id=1, flags=0, energy_hint=128, epoch=0):
    """Pack a v1 seed packet (13 bytes, CRC-protected).

    Minimal format for LoRa / extreme bandwidth constraints.
    No position data — identity + energy only.
    """
    seed_bytes = encode_seed(seed)

    header = struct.pack(_V1_FMT_NOCRC, V1, frame_id, flags,
                         seed_bytes, energy_hint, epoch)
    crc = zlib.crc32(header) & 0xFFFF

    return struct.pack(_V1_FMT_FULL, V1, frame_id, flags,
                       seed_bytes, energy_hint, epoch, crc)


def unpack_v1(packet):
    """Unpack a v1 seed packet. Raises ValueError on CRC mismatch."""
    if len(packet) != _V1_SIZE:
        raise ValueError(f"v1 packet must be {_V1_SIZE} bytes, got {len(packet)}")

    version, frame, flags, seed_bytes, energy, epoch, crc = \
        struct.unpack(_V1_FMT_FULL, packet)

    if version != V1:
        raise ValueError(f"expected version {V1}, got {version}")

    header = struct.pack(_V1_FMT_NOCRC, version, frame, flags,
                         seed_bytes, energy, epoch)
    if zlib.crc32(header) & 0xFFFF != crc:
        raise ValueError("CRC mismatch")

    return {
        "version": V1,
        "frame": frame,
        "flags": flags,
        "seed": decode_seed(seed_bytes),
        "energy_hint": energy,
        "epoch": epoch,
    }


# =============================================================================
# V2 — Full with position (21 bytes)
# =============================================================================
# Offset  Size  Field
# 0       1     Version (uint8) = 2
# 1       1     Frame ID
# 2       1     Flags
# 3       5     Seed (5 × uint8)
# 8       1     Energy Hint
# 9       2     Epoch
# 11      2     Anchor Cell (uint16)
# 13      3     Offset Vector (int8 × 3)
# 16      1     Neighbor Hint Index (uint8)
# 17      2     Neighbor Hint Projection (uint16)
# 19      2     CRC16

_V2_FMT_NOCRC = ">BBB5sBHH3bBH"
_V2_FMT_FULL  = ">BBB5sBHH3bBHH"
_V2_SIZE = struct.calcsize(_V2_FMT_FULL)  # 21 bytes


def pack_v2(seed, pos, frame_id=1, flags=0, energy_hint=128, epoch=0):
    """Pack a v2 seed packet (21 bytes, CRC-protected).

    Full format with position encoding and neighbor routing hint.
    """
    seed_bytes = encode_seed(seed)
    anchor, offset = position_to_anchor_offset(pos)
    dx, dy, dz = int(offset[0]), int(offset[1]), int(offset[2])
    dir_idx, proj = encode_neighbor_hint(seed)

    header = struct.pack(_V2_FMT_NOCRC, V2, frame_id, flags,
                         seed_bytes, energy_hint, epoch,
                         anchor, dx, dy, dz, dir_idx, proj)
    crc = zlib.crc32(header) & 0xFFFF

    return struct.pack(_V2_FMT_FULL, V2, frame_id, flags,
                       seed_bytes, energy_hint, epoch,
                       anchor, dx, dy, dz, dir_idx, proj, crc)


def unpack_v2(packet):
    """Unpack a v2 seed packet. Raises ValueError on CRC mismatch."""
    if len(packet) != _V2_SIZE:
        raise ValueError(f"v2 packet must be {_V2_SIZE} bytes, got {len(packet)}")

    (version, frame, flags, seed_bytes, energy, epoch,
     anchor, dx, dy, dz, dir_idx, proj, crc) = \
        struct.unpack(_V2_FMT_FULL, packet)

    if version != V2:
        raise ValueError(f"expected version {V2}, got {version}")

    header = struct.pack(_V2_FMT_NOCRC, version, frame, flags,
                         seed_bytes, energy, epoch,
                         anchor, dx, dy, dz, dir_idx, proj)
    if zlib.crc32(header) & 0xFFFF != crc:
        raise ValueError("CRC mismatch")

    seed = decode_seed(seed_bytes)
    pos = anchor_offset_to_position(anchor, (dx, dy, dz))
    direction, strength = decode_neighbor_hint(dir_idx, proj)

    return {
        "version": V2,
        "frame": frame,
        "flags": flags,
        "seed": seed,
        "energy_hint": energy,
        "epoch": epoch,
        "position": pos,
        "neighbor_direction": direction,
        "neighbor_strength": strength,
    }


# =============================================================================
# V_RAW — Raw float format (no encoding, no CRC)
# =============================================================================
# Used on LAN/UDP where bandwidth is plentiful.
# 44 bytes without node_id, 48 bytes with.

_VRAW_FMT = "6f3f2i"          # 44 bytes: seed(6f) + pos(3f) + energy(i) + epoch(i)
_VRAW_FMT_NODE = "i6f3f2i"    # 48 bytes: node_id(i) + seed(6f) + pos(3f) + energy(i) + epoch(i)
_VRAW_SIZE = struct.calcsize(_VRAW_FMT)
_VRAW_NODE_SIZE = struct.calcsize(_VRAW_FMT_NODE)


def pack_raw(seed, pos, energy=100, epoch=0, node_id=None):
    """Pack a raw float packet (44 or 48 bytes).

    No encoding overhead. Use when bandwidth isn't constrained.
    """
    seed = np.asarray(seed, dtype=float)
    pos = np.asarray(pos, dtype=float)

    if node_id is not None:
        return struct.pack(_VRAW_FMT_NODE, node_id,
                           *seed.tolist(), *pos.tolist(), energy, epoch)
    return struct.pack(_VRAW_FMT,
                       *seed.tolist(), *pos.tolist(), energy, epoch)


def unpack_raw(packet):
    """Unpack a raw float packet (44 or 48 bytes)."""
    if len(packet) == _VRAW_NODE_SIZE:
        data = struct.unpack(_VRAW_FMT_NODE, packet)
        return {
            "version": V_RAW,
            "node_id": data[0],
            "seed": np.array(data[1:7]),
            "position": np.array(data[7:10]),
            "energy_hint": data[10],
            "epoch": data[11],
        }
    elif len(packet) == _VRAW_SIZE:
        data = struct.unpack(_VRAW_FMT, packet)
        return {
            "version": V_RAW,
            "seed": np.array(data[0:6]),
            "position": np.array(data[6:9]),
            "energy_hint": data[9],
            "epoch": data[10],
        }
    else:
        raise ValueError(f"raw packet must be {_VRAW_SIZE} or {_VRAW_NODE_SIZE} bytes, "
                         f"got {len(packet)}")


# =============================================================================
# AUTO PACK / UNPACK — version negotiation + fallback
# =============================================================================

def auto_pack(seed, pos=None, frame_id=1, flags=0, energy_hint=128,
              epoch=0, node_id=None, prefer_version=None):
    """Pack using the best available format.

    Fallback chain: v2 → v1 → v_raw

    Args:
        seed: 6D seed (required).
        pos: 3D position (required for v2, optional for v1/raw).
        prefer_version: Force a specific version (V1, V2, V_RAW).
        node_id: Node identifier (only used in raw format).

    Returns:
        bytes: Packed packet.
    """
    if prefer_version is not None:
        # Explicit version requested
        if prefer_version == V2:
            if pos is None:
                raise ValueError("v2 requires position data")
            return pack_v2(seed, pos, frame_id, flags, energy_hint, epoch)
        elif prefer_version == V1:
            return pack_v1(seed, frame_id, flags, energy_hint, epoch)
        elif prefer_version == V_RAW:
            return pack_raw(seed, pos or [0, 0, 0], energy_hint, epoch, node_id)

    # Auto-select: use most compact format the data supports
    if pos is not None:
        return pack_v2(seed, pos, frame_id, flags, energy_hint, epoch)
    else:
        return pack_v1(seed, frame_id, flags, energy_hint, epoch)


def auto_unpack(packet):
    """Unpack any packet version, with fallback on failure.

    Tries versions in order based on packet size and header byte.
    Falls through to next version if parsing fails.

    Returns:
        dict with at minimum: version, seed, energy_hint, epoch.
    """
    errors = []

    # Check raw formats first (they have no version header)
    if len(packet) in (_VRAW_SIZE, _VRAW_NODE_SIZE):
        try:
            return unpack_raw(packet)
        except (struct.error, ValueError) as e:
            errors.append(f"raw: {e}")

    # Check versioned formats by header byte
    if len(packet) >= 1:
        version_byte = packet[0]

        if version_byte == V2 and len(packet) == _V2_SIZE:
            try:
                return unpack_v2(packet)
            except (struct.error, ValueError) as e:
                errors.append(f"v2: {e}")

        if version_byte == V1 and len(packet) == _V1_SIZE:
            try:
                return unpack_v1(packet)
            except (struct.error, ValueError) as e:
                errors.append(f"v1: {e}")

    # Try all formats as fallback
    for version, unpack_fn, expected_size in [
        (V2, unpack_v2, _V2_SIZE),
        (V1, unpack_v1, _V1_SIZE),
    ]:
        if len(packet) == expected_size:
            try:
                return unpack_fn(packet)
            except (struct.error, ValueError) as e:
                errors.append(f"v{version}_fallback: {e}")

    raise ValueError(f"could not unpack packet ({len(packet)} bytes): {errors}")


# =============================================================================
# FORMAT INFO
# =============================================================================

def packet_info():
    """Return metadata about available packet formats."""
    return {
        V1: {"name": "v1_minimal", "size": _V1_SIZE, "has_position": False,
             "has_crc": True, "lora_compatible": True},
        V2: {"name": "v2_full", "size": _V2_SIZE, "has_position": True,
             "has_crc": True, "lora_compatible": True},
        V_RAW: {"name": "v_raw", "size_range": (_VRAW_SIZE, _VRAW_NODE_SIZE),
                "has_position": True, "has_crc": False, "lora_compatible": False},
    }
