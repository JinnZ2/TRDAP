# =============================================================================
# SEED PROTOCOL v2 — FULL FORMAT WITH POSITION
# =============================================================================
#
# V2 extends v1 with spatial coupling: position encoding + neighbor hints.
# 21-byte CRC-protected packets, still LoRa-compatible.
#
# Fallback chain: [v2] → v1 → v_raw
#
# All core functions imported from seed_core.py (single source of truth).

import numpy as np

# Core functions from canonical source
from seed_core import (
    U, GRID_SCALE,
    encode_seed, decode_seed,
    position_to_anchor_offset, anchor_offset_to_position,
    encode_neighbor_hint, decode_neighbor_hint,
    seed_distance, combine_seeds,
    expand, normalize_energy,
)

# Packet functions from canonical source
from seed_packet import (
    V2 as VERSION,
    pack_v2 as pack_packet,
    unpack_v2 as unpack_packet,
)


# -----------------------------------------------------------------------------
# DEMO
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
    pos  = [123.4, 456.7, 78.9]

    print("\n--- PACK ---")
    pkt = pack_packet(seed, pos, epoch=42)
    print("packet bytes:", pkt)
    print("size:", len(pkt), "bytes")

    print("\n--- UNPACK ---")
    data = unpack_packet(pkt)

    print("decoded seed:", np.round(data["seed"], 4))
    print("decoded position:", np.round(data["position"], 2))
    print("neighbor dir:", data["neighbor_direction"])
    print("neighbor strength:", round(data["neighbor_strength"], 3))

    print("\n--- DISTANCE CHECK ---")
    print("seed error:", np.max(np.abs(data["seed"] - np.array(seed)/sum(seed))))
