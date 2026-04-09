"""
seed_protocol_v1.py — Orbital Seed Transport + Reconstruction (v1)

V1 is the MINIMAL format: 13-byte CRC-protected packets for LoRa
and extreme bandwidth constraints. Identity + energy only, no position.

Fallback chain: v2 → [v1] → v_raw

All core functions (encoding, expansion, distance) are imported from
seed_core.py — the single source of truth.

Author: Jami + synthesis
License: MIT
"""

# All core functions come from seed_core (canonical source)
from seed_core import (
    U, encode_seed, decode_seed,
    expand, normalize_energy, angular_weight, build_weight_matrix as build_W,
    seed_distance, same_entity, combine_seeds,
)

# Packet functions come from seed_packet (canonical source)
from seed_packet import (
    V1 as VERSION,
    pack_v1 as pack_seed_packet,
    unpack_v1 as unpack_seed_packet,
)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":

    seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]

    print("\n--- PACK ---")
    pkt = pack_seed_packet(seed, epoch=42)
    print(f"bytes: {pkt}")
    print(f"size: {len(pkt)} bytes")

    print("\n--- UNPACK ---")
    data = unpack_seed_packet(pkt)
    print(data)

    print("\n--- EXPAND ---")
    shells = expand(data["seed"], steps=5)
    for i, s in enumerate(shells):
        print(i, np.round(s["S"], 3))
