"""
seed_core.py — Canonical shared foundation for all Seed Protocol versions.

This is the SINGLE SOURCE OF TRUTH for:
  - Seed encoding / decoding (6D <-> 5 bytes)
  - Deterministic expansion (physics-compliant shell generation)
  - Seed distance (Manhattan — canonical metric)
  - Seed combination (field aggregation)
  - Energy normalization
  - Octahedral geometry

All version-specific files (v1–v4) import from here. If you change
expansion rules, change them HERE and bump VERSION_PHYSICS.

Invariants (enforced by physics_guard.py):
  - Energy conservation: sum(S_i) == E at every shell
  - Causality: radii strictly increasing
  - Non-negative amplitudes: all S_i >= 0
  - Radial scaling: r_{n+1} / r_n == rho
  - Energy decay: E_{n+1} / E_n == epsilon
  - Determinism: expand(seed) identical everywhere

License: CC0 1.0
"""

import numpy as np

# =============================================================================
# VERSION — bump this when expansion rules change
# =============================================================================

VERSION_PHYSICS = 1  # expansion algorithm version (all packet versions share this)

# =============================================================================
# GEOMETRY — octahedral unit directions
# =============================================================================

U = np.array([
    [1, 0, 0], [-1, 0, 0],   # +X, -X
    [0, 1, 0], [0, -1, 0],   # +Y, -Y
    [0, 0, 1], [0, 0, -1],   # +Z, -Z
], dtype=float)

# =============================================================================
# SEED ENCODING / DECODING
# =============================================================================

def encode_seed(proportions, bits=8):
    """Encode 6D seed proportions into 5 bytes (6th value implicit).

    Args:
        proportions: 6-element array/list of non-negative values.
        bits: Quantization bits per value (default 8 = uint8).

    Returns:
        bytes: 5 encoded bytes. Decode with decode_seed().
    """
    p = np.array(proportions, dtype=float)
    total = p.sum()
    if total > 0:
        p = p / total

    max_val = (1 << bits) - 1
    encoded = []
    for i in range(5):
        v = int(p[i] * max_val)
        v = max(0, min(max_val, v))
        encoded.append(v)

    return bytes(encoded)


def decode_seed(encoded, bits=8):
    """Decode 5 bytes back to 6D normalized proportions.

    The 6th value is reconstructed as 1 - sum(first 5).

    Args:
        encoded: 5 bytes from encode_seed().
        bits: Must match encoding bits.

    Returns:
        np.array: 6D normalized proportions (sums to 1.0).
    """
    max_val = (1 << bits) - 1
    p = [b / max_val for b in encoded]
    remainder = 1.0 - sum(p)
    p.append(max(0.0, remainder))

    p = np.array(p)
    total = p.sum()
    if total > 0:
        p = p / total
    return p


# =============================================================================
# EXPANSION — deterministic shell generation
# =============================================================================

def angular_weight(u1, u2):
    """Coupling weight between two directions (clamped dot product)."""
    return max(0.0, np.dot(u1, u2))


def build_weight_matrix():
    """Build the 6x6 angular coupling matrix W.

    W[i,j] = how much direction j influences direction i,
    row-normalized so each row sums to 1.
    """
    W = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            W[i, j] = angular_weight(U[i], U[j])
        s = W[i].sum()
        if s > 0:
            W[i] /= s
    return W


# Module-level cache — W is constant
_W = None

def _get_W():
    global _W
    if _W is None:
        _W = build_weight_matrix()
    return _W


def normalize_energy(v, E):
    """Normalize amplitude vector to total energy E, clamping negatives to 0."""
    v = np.maximum(v, 0)
    s = v.sum()
    if s == 0:
        return np.ones(6) * (E / 6)
    return v * (E / s)


def expand(seed, steps=6, E0=1.0, r0=1.0, rho=1.5, epsilon=0.6):
    """Deterministic shell expansion from a seed.

    This is the canonical expansion algorithm. All protocol versions
    must produce identical results from the same seed + parameters.

    Args:
        seed: 6D array (will be normalized to energy E0).
        steps: Number of shells to generate beyond the initial.
        E0: Initial energy.
        r0: Initial radius.
        rho: Radial scaling factor (r_{n+1} = rho * r_n).
        epsilon: Energy decay factor (E_{n+1} = epsilon * E_n).

    Returns:
        list of dicts, each with keys: 'id', 'r', 'E', 'S'
    """
    W = _get_W()
    seed = np.array(seed, dtype=float)
    S = normalize_energy(seed, E0)

    shells = [{"id": 0, "r": r0, "E": E0, "S": S.copy()}]

    for i in range(steps):
        r_new = rho * shells[-1]["r"]
        E_new = epsilon * shells[-1]["E"]

        field = np.zeros(6)
        for sh in shells:
            if sh["r"] >= r_new:
                continue
            field += W @ sh["S"]

        S_new = normalize_energy(field, E_new)
        shells.append({"id": i + 1, "r": r_new, "E": E_new, "S": S_new.copy()})

    return shells


# =============================================================================
# SEED DISTANCE — canonical metric
# =============================================================================

def seed_distance(a, b):
    """Manhattan (L1) distance between two seeds.

    This is the canonical distance metric used for:
      - Identity comparison (same_entity)
      - Gradient routing (next_hop)
      - Cluster formation

    Manhattan is preferred over Euclidean because:
      - Each axis is an independent direction (+X/-X/+Y/-Y/+Z/-Z)
      - L1 respects axis independence
      - More sensitive to single-axis differences (important for routing)
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.sum(np.abs(a - b))


def same_entity(a, b, threshold=0.05):
    """Check if two seeds represent the same entity."""
    return seed_distance(a, b) < threshold


# =============================================================================
# SEED COMBINATION — field aggregation
# =============================================================================

def combine_seeds(seeds, weights=None):
    """Combine multiple seeds into a single field.

    Uses weighted sum normalized to 1. When weights are uniform,
    this is equivalent to averaging.

    Args:
        seeds: List/array of 6D seed vectors.
        weights: Optional weight per seed (default: uniform).

    Returns:
        np.array: Combined 6D seed (sums to 1.0).
    """
    seeds = [np.asarray(s, dtype=float) for s in seeds]

    if weights is None:
        weights = np.ones(len(seeds))
    else:
        weights = np.asarray(weights, dtype=float)

    field = np.zeros(6)
    for s, w in zip(seeds, weights):
        total = s.sum()
        if total > 0:
            field += w * (s / total)
        else:
            field += w * s

    total = field.sum()
    if total > 0:
        return field / total
    return np.ones(6) / 6


# =============================================================================
# POSITION ENCODING (v2+)
# =============================================================================

GRID_SCALE = 100.0  # meters per grid cell

def position_to_anchor_offset(pos):
    """Encode a 3D position as a grid anchor ID + local offset.

    Used in v2 packets for compact position representation.

    Args:
        pos: [x, y, z] in meters.

    Returns:
        (anchor_id: uint16, offset: [dx, dy, dz] as int8)
    """
    pos = np.array(pos, dtype=float)
    anchor = np.floor(pos / GRID_SCALE).astype(int)
    anchor_id = ((anchor[0] & 0x1F) << 10) | ((anchor[1] & 0x1F) << 5) | (anchor[2] & 0x1F)

    local = pos - (anchor * GRID_SCALE)
    offset = np.clip((local / GRID_SCALE * 127), -128, 127).astype(int)

    return int(anchor_id), offset


def anchor_offset_to_position(anchor_id, offset):
    """Decode anchor ID + offset back to 3D position."""
    x = (anchor_id >> 10) & 0x1F
    y = (anchor_id >> 5) & 0x1F
    z = anchor_id & 0x1F

    anchor = np.array([x, y, z], dtype=float)
    base = anchor * GRID_SCALE

    offset = np.array(offset, dtype=float) / 127.0 * GRID_SCALE
    return base + offset


# =============================================================================
# NEIGHBOR HINT ENCODING (v2+)
# =============================================================================

def encode_neighbor_hint(seed):
    """Encode dominant direction as neighbor routing hint."""
    seed = np.asarray(seed, dtype=float)
    idx = int(np.argmax(seed))
    proj = int(seed[idx] * 65535)
    return idx, proj


def decode_neighbor_hint(idx, proj):
    """Decode neighbor hint to direction + strength."""
    direction = U[idx].copy()
    strength = proj / 65535.0
    return direction, strength
