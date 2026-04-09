"""
test_seed_protocol.py — Comprehensive test suite for Seed Protocol.

Tests:
  1. Core: encoding roundtrip, expansion determinism, distance properties
  2. Packets: v1/v2/raw pack/unpack roundtrip, CRC validation, fallback
  3. Physics guard: constraint validation on valid/tampered expansions
  4. Cross-version: canonical functions produce identical results everywhere
  5. Edge cases: zero seeds, single-axis seeds, max values

Run:
    cd seed-protocol/
    python -m pytest test_seed_protocol.py -v
    # or without pytest:
    python test_seed_protocol.py

License: CC0 1.0
"""

import sys
import os
import numpy as np

# Ensure we can import from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seed_core import (
    encode_seed, decode_seed,
    expand, normalize_energy, build_weight_matrix,
    seed_distance, same_entity, combine_seeds,
    position_to_anchor_offset, anchor_offset_to_position,
    encode_neighbor_hint, decode_neighbor_hint,
    U,
)
from seed_packet import (
    pack_v1, unpack_v1, pack_v2, unpack_v2,
    pack_raw, unpack_raw, auto_pack, auto_unpack,
    V1, V2, V_RAW, FALLBACK_CHAIN,
    _V1_SIZE, _V2_SIZE,
)

# =============================================================================
# TEST DATA
# =============================================================================

SEED_A = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
SEED_B = [0.48, 0.22, 0.14, 0.09, 0.05, 0.02]
SEED_UNIFORM = [1/6] * 6
SEED_SINGLE_AXIS = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
POS_A = [123.4, 456.7, 78.9]
POS_ORIGIN = [0.0, 0.0, 0.0]

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


# =============================================================================
# 1. CORE: ENCODING
# =============================================================================

def test_encoding():
    print("\n=== ENCODING ===")

    # Roundtrip: encode then decode should be close to original
    for name, seed in [("standard", SEED_A), ("uniform", SEED_UNIFORM),
                       ("single_axis", SEED_SINGLE_AXIS)]:
        original = np.array(seed) / np.sum(seed)
        encoded = encode_seed(seed)
        decoded = decode_seed(encoded)

        check(f"roundtrip_{name}_length", len(encoded) == 5,
              f"got {len(encoded)}")
        check(f"roundtrip_{name}_sums_to_1",
              abs(decoded.sum() - 1.0) < 1e-10,
              f"sum={decoded.sum()}")
        check(f"roundtrip_{name}_close",
              np.max(np.abs(decoded - original)) < 0.02,
              f"max_err={np.max(np.abs(decoded - original)):.4f}")

    # Non-negative output
    decoded = decode_seed(encode_seed(SEED_A))
    check("decode_non_negative", np.all(decoded >= 0))

    # 6th value is implicit (reconstructed)
    check("decode_has_6_values", len(decoded) == 6)


# =============================================================================
# 2. CORE: EXPANSION
# =============================================================================

def test_expansion():
    print("\n=== EXPANSION ===")

    seed = np.array(SEED_A) / np.sum(SEED_A)
    shells = expand(seed, steps=5)

    # Correct number of shells
    check("shell_count", len(shells) == 6, f"got {len(shells)}")

    # Energy conservation at every shell
    for s in shells:
        residual = abs(s["S"].sum() - s["E"])
        check(f"energy_conservation_shell_{s['id']}", residual < 1e-10,
              f"residual={residual:.2e}")

    # Non-negative amplitudes
    for s in shells:
        check(f"non_negative_shell_{s['id']}", np.all(s["S"] >= 0))

    # Causality: radii strictly increasing
    for i in range(1, len(shells)):
        check(f"causality_shell_{i}",
              shells[i]["r"] > shells[i-1]["r"],
              f"r[{i}]={shells[i]['r']:.4f} <= r[{i-1}]={shells[i-1]['r']:.4f}")

    # Radial scaling: r_{n+1} / r_n == rho
    rho = 1.5
    for i in range(1, len(shells)):
        ratio = shells[i]["r"] / shells[i-1]["r"]
        check(f"radial_scaling_shell_{i}",
              abs(ratio - rho) < 1e-10,
              f"ratio={ratio:.6f}")

    # Energy decay: E_{n+1} / E_n == epsilon
    eps = 0.6
    for i in range(1, len(shells)):
        ratio = shells[i]["E"] / shells[i-1]["E"]
        check(f"energy_decay_shell_{i}",
              abs(ratio - eps) < 1e-10,
              f"ratio={ratio:.6f}")

    # Shell IDs are present
    for i, s in enumerate(shells):
        check(f"shell_id_{i}", s["id"] == i)


# =============================================================================
# 3. CORE: DETERMINISM
# =============================================================================

def test_determinism():
    print("\n=== DETERMINISM ===")

    seed = np.array(SEED_A) / np.sum(SEED_A)

    # Same seed → identical shells (run twice)
    shells_1 = expand(seed, steps=10)
    shells_2 = expand(seed, steps=10)

    for i in range(len(shells_1)):
        max_dev = np.max(np.abs(shells_1[i]["S"] - shells_2[i]["S"]))
        check(f"deterministic_shell_{i}", max_dev < 1e-15,
              f"deviation={max_dev:.2e}")

    # Different seed → different shells
    seed_b = np.array(SEED_B) / np.sum(SEED_B)
    shells_b = expand(seed_b, steps=5)
    diff = np.max(np.abs(shells_1[3]["S"] - shells_b[3]["S"]))
    check("different_seed_different_result", diff > 0.001,
          f"diff={diff:.6f}")


# =============================================================================
# 4. CORE: DISTANCE & COMBINATION
# =============================================================================

def test_distance_and_combine():
    print("\n=== DISTANCE & COMBINE ===")

    a = np.array(SEED_A) / np.sum(SEED_A)
    b = np.array(SEED_B) / np.sum(SEED_B)

    # Distance to self is 0
    check("distance_self_zero", seed_distance(a, a) < 1e-15)

    # Distance is symmetric
    check("distance_symmetric",
          abs(seed_distance(a, b) - seed_distance(b, a)) < 1e-15)

    # Distance is non-negative
    check("distance_non_negative", seed_distance(a, b) >= 0)

    # Triangle inequality
    c = np.array(SEED_UNIFORM)
    d_ab = seed_distance(a, b)
    d_ac = seed_distance(a, c)
    d_bc = seed_distance(b, c)
    check("triangle_inequality", d_ab <= d_ac + d_bc + 1e-10)

    # same_entity: seed vs itself
    check("same_entity_self", same_entity(a, a))

    # same_entity: similar seeds
    check("same_entity_similar", same_entity(a, b, threshold=0.2))

    # combine_seeds: single seed returns itself (normalized)
    combined = combine_seeds([a])
    check("combine_single", np.max(np.abs(combined - a)) < 1e-10)

    # combine_seeds: result sums to 1
    combined = combine_seeds([a, b])
    check("combine_sums_to_1", abs(combined.sum() - 1.0) < 1e-10)

    # combine_seeds: non-negative
    check("combine_non_negative", np.all(combined >= 0))


# =============================================================================
# 5. PACKETS: V1
# =============================================================================

def test_packets_v1():
    print("\n=== PACKETS V1 ===")

    # Pack and unpack roundtrip
    pkt = pack_v1(SEED_A, frame_id=1, flags=0, energy_hint=128, epoch=42)

    check("v1_size", len(pkt) == _V1_SIZE, f"got {len(pkt)}")

    data = unpack_v1(pkt)
    check("v1_version", data["version"] == V1)
    check("v1_frame", data["frame"] == 1)
    check("v1_flags", data["flags"] == 0)
    check("v1_energy", data["energy_hint"] == 128)
    check("v1_epoch", data["epoch"] == 42)

    # Seed roundtrip accuracy
    original = np.array(SEED_A) / np.sum(SEED_A)
    check("v1_seed_close",
          np.max(np.abs(data["seed"] - original)) < 0.02)

    # CRC catches corruption
    corrupted = bytearray(pkt)
    corrupted[5] ^= 0xFF  # flip a seed byte
    try:
        unpack_v1(bytes(corrupted))
        check("v1_crc_detects_corruption", False, "should have raised ValueError")
    except ValueError:
        check("v1_crc_detects_corruption", True)

    # Wrong size rejected
    try:
        unpack_v1(pkt[:5])
        check("v1_rejects_wrong_size", False)
    except ValueError:
        check("v1_rejects_wrong_size", True)


# =============================================================================
# 6. PACKETS: V2
# =============================================================================

def test_packets_v2():
    print("\n=== PACKETS V2 ===")

    pkt = pack_v2(SEED_A, POS_A, frame_id=2, flags=1, energy_hint=200, epoch=99)

    check("v2_size", len(pkt) == _V2_SIZE, f"got {len(pkt)}")

    data = unpack_v2(pkt)
    check("v2_version", data["version"] == V2)
    check("v2_frame", data["frame"] == 2)
    check("v2_flags", data["flags"] == 1)
    check("v2_energy", data["energy_hint"] == 200)
    check("v2_epoch", data["epoch"] == 99)

    # Seed roundtrip
    original = np.array(SEED_A) / np.sum(SEED_A)
    check("v2_seed_close",
          np.max(np.abs(data["seed"] - original)) < 0.02)

    # Position roundtrip (lossy due to grid encoding, but reasonable)
    check("v2_has_position", "position" in data)
    check("v2_has_neighbor_direction", "neighbor_direction" in data)
    check("v2_has_neighbor_strength", "neighbor_strength" in data)

    # CRC catches corruption
    corrupted = bytearray(pkt)
    corrupted[5] ^= 0xFF
    try:
        unpack_v2(bytes(corrupted))
        check("v2_crc_detects_corruption", False)
    except ValueError:
        check("v2_crc_detects_corruption", True)


# =============================================================================
# 7. PACKETS: V_RAW
# =============================================================================

def test_packets_raw():
    print("\n=== PACKETS RAW ===")

    seed = np.array(SEED_A) / np.sum(SEED_A)
    pos = np.array(POS_A)

    # Without node_id
    pkt = pack_raw(seed, pos, energy=150, epoch=7)
    check("raw_size_no_node", len(pkt) == 44, f"got {len(pkt)}")

    data = unpack_raw(pkt)
    check("raw_version", data["version"] == V_RAW)
    check("raw_seed_exact", np.allclose(data["seed"], seed))
    check("raw_pos_exact", np.allclose(data["position"], pos))
    check("raw_energy", data["energy_hint"] == 150)
    check("raw_epoch", data["epoch"] == 7)

    # With node_id
    pkt_node = pack_raw(seed, pos, energy=150, epoch=7, node_id=42)
    check("raw_size_with_node", len(pkt_node) == 48, f"got {len(pkt_node)}")

    data_node = unpack_raw(pkt_node)
    check("raw_node_id", data_node.get("node_id") == 42)
    check("raw_seed_with_node", np.allclose(data_node["seed"], seed))


# =============================================================================
# 8. AUTO PACK / UNPACK — FALLBACK
# =============================================================================

def test_auto_fallback():
    print("\n=== AUTO FALLBACK ===")

    seed = SEED_A
    pos = POS_A

    # With position → should pick v2
    pkt_v2 = auto_pack(seed, pos=pos, epoch=10)
    check("auto_with_pos_is_v2", len(pkt_v2) == _V2_SIZE)

    # Without position → should pick v1
    pkt_v1 = auto_pack(seed, epoch=10)
    check("auto_no_pos_is_v1", len(pkt_v1) == _V1_SIZE)

    # Explicit version override
    pkt_raw = auto_pack(seed, pos=pos, prefer_version=V_RAW)
    check("auto_explicit_raw", len(pkt_raw) == 44)

    # auto_unpack handles all versions
    data_v1 = auto_unpack(pkt_v1)
    check("auto_unpack_v1", data_v1["version"] == V1)

    data_v2 = auto_unpack(pkt_v2)
    check("auto_unpack_v2", data_v2["version"] == V2)

    data_raw = auto_unpack(pkt_raw)
    check("auto_unpack_raw", data_raw["version"] == V_RAW)

    # Fallback chain is correct
    check("fallback_chain", FALLBACK_CHAIN == [V2, V1, V_RAW])


# =============================================================================
# 9. PHYSICS GUARD
# =============================================================================

def test_physics_guard():
    print("\n=== PHYSICS GUARD ===")

    from physics_guard import validate_shells, verify_deterministic, guard

    seed = np.array(SEED_A) / np.sum(SEED_A)
    shells = expand(seed, steps=5)

    # Valid expansion passes all checks
    result = validate_shells(shells)
    check("guard_valid_expansion", result["valid"])

    for name, check_result in result["checks"].items():
        check(f"guard_{name}", check_result["passed"])

    # Deterministic verification
    det = verify_deterministic(seed, shells)
    check("guard_deterministic", det["match"],
          f"max_dev={det['max_deviation']:.2e}")

    # Full guard
    full = guard(seed, shells)
    check("guard_full_pass", full["valid"])

    # Tampered expansion fails
    tampered = expand(seed, steps=5)
    tampered[3]["S"] = tampered[3]["S"] * 2.0  # break energy conservation
    result_bad = validate_shells(tampered)
    check("guard_detects_tampering", not result_bad["valid"])

    # Negative amplitude injection
    neg_shells = expand(seed, steps=5)
    neg_shells[1]["S"][0] = -0.1
    result_neg = validate_shells(neg_shells)
    check("guard_detects_negative", not result_neg["valid"])


# =============================================================================
# 10. CROSS-VERSION CONSISTENCY
# =============================================================================

def test_cross_version():
    print("\n=== CROSS-VERSION CONSISTENCY ===")

    # V1 and V2 should produce same seed from same input
    pkt_v1 = pack_v1(SEED_A, epoch=42)
    pkt_v2 = pack_v2(SEED_A, POS_A, epoch=42)

    data_v1 = unpack_v1(pkt_v1)
    data_v2 = unpack_v2(pkt_v2)

    check("cross_seed_match",
          np.allclose(data_v1["seed"], data_v2["seed"]),
          f"max_diff={np.max(np.abs(data_v1['seed'] - data_v2['seed'])):.6f}")

    check("cross_epoch_match", data_v1["epoch"] == data_v2["epoch"])
    check("cross_energy_match", data_v1["energy_hint"] == data_v2["energy_hint"])

    # Expansion from either decoded seed should be identical
    shells_v1 = expand(data_v1["seed"], steps=5)
    shells_v2 = expand(data_v2["seed"], steps=5)

    for i in range(len(shells_v1)):
        max_dev = np.max(np.abs(shells_v1[i]["S"] - shells_v2[i]["S"]))
        check(f"cross_expansion_shell_{i}",
              max_dev < 1e-14,
              f"deviation={max_dev:.2e}")


# =============================================================================
# 11. EDGE CASES
# =============================================================================

def test_edge_cases():
    print("\n=== EDGE CASES ===")

    # Uniform seed
    shells = expand(SEED_UNIFORM, steps=3)
    check("uniform_seed_valid", len(shells) == 4)
    for s in shells:
        check(f"uniform_energy_conservation_{s['id']}",
              abs(s["S"].sum() - s["E"]) < 1e-10)

    # Single-axis seed
    shells = expand(SEED_SINGLE_AXIS, steps=3)
    check("single_axis_valid", len(shells) == 4)
    check("single_axis_energy", abs(shells[0]["S"].sum() - 1.0) < 1e-10)

    # Zero steps
    shells = expand(SEED_A, steps=0)
    check("zero_steps", len(shells) == 1)

    # Many steps
    shells = expand(SEED_A, steps=50)
    check("many_steps", len(shells) == 51)
    check("many_steps_energy_conserved",
          abs(shells[-1]["S"].sum() - shells[-1]["E"]) < 1e-10)

    # W matrix properties
    W = build_weight_matrix()
    check("W_shape", W.shape == (6, 6))
    for i in range(6):
        check(f"W_row_{i}_sums_to_1", abs(W[i].sum() - 1.0) < 1e-10)
    check("W_non_negative", np.all(W >= 0))

    # Position encoding edge cases
    anchor, offset = position_to_anchor_offset(POS_ORIGIN)
    pos_back = anchor_offset_to_position(anchor, offset)
    check("position_origin_roundtrip",
          np.linalg.norm(pos_back) < 1.0,
          f"got {pos_back}")

    # combine_seeds with weights
    a = np.array(SEED_A) / np.sum(SEED_A)
    combined = combine_seeds([a, a], weights=[1.0, 1.0])
    check("combine_identical_seeds",
          np.max(np.abs(combined - a)) < 1e-10)

    # Distance to opposite seed
    d = seed_distance(
        np.array([1, 0, 0, 0, 0, 0], dtype=float),
        np.array([0, 0, 0, 0, 0, 1], dtype=float),
    )
    check("distance_opposite_is_2", abs(d - 2.0) < 1e-10, f"got {d}")


# =============================================================================
# RUNNER
# =============================================================================

def run_all():
    print("=" * 60)
    print("SEED PROTOCOL TEST SUITE")
    print("=" * 60)

    test_encoding()
    test_expansion()
    test_determinism()
    test_distance_and_combine()
    test_packets_v1()
    test_packets_v2()
    test_packets_raw()
    test_auto_fallback()
    test_physics_guard()
    test_cross_version()
    test_edge_cases()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 60)

    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
