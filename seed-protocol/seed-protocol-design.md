# Seed Protocol — Design Notes

## Overview

The Seed Protocol is a minimal, deterministic identity and coordination system for decentralized networks. It encodes node identity as a 6D normalized vector ("seed") mapped to octahedral directions, enabling stateless reconstruction, gradient-based routing, and self-organizing topology — all within radio-safe packet sizes.

## v1 Packet Format (13 bytes)

| Offset | Size | Field                              |
|--------|------|------------------------------------|
| 0      | 1    | Version (uint8)                    |
| 1      | 1    | Frame ID (uint8)                   |
| 2      | 1    | Flags (uint8)                      |
| 3      | 5    | Seed (5 × uint8, 6th implicit)     |
| 8      | 1    | Energy Hint (uint8, log-scaled)    |
| 9      | 2    | Epoch (uint16)                     |
| 11     | 2    | CRC16 (lower 16 bits of CRC32)    |

### Frame IDs

- `0x01` — Global earth frame
- `0x02` — Local mesh frame
- `0x03` — Inertial frame

### Flags

- bit 0 — seed is authoritative
- bit 1 — request sync
- bit 2 — compressed relay
- bit 3 — exploration-enabled

### Seed Encoding

5 values stored (uint8 each). The 6th value is implicit: `p6 = 1 - sum(p1..p5)`.

Directional amplitude across: `[+X, -X, +Y, -Y, +Z, -Z]`

### Energy Hint

0–255, log-scaled available energy. Used to determine:
- Expansion depth
- Explore vs expand mode

### Epoch

Monotonic counter or coarse timestamp.

## v2 Packet Format (21 bytes)

Extends v1 with spatial coupling:

| Offset | Size | Field                              |
|--------|------|------------------------------------|
| 0      | 1    | Version                            |
| 1      | 1    | Frame ID                           |
| 2      | 1    | Flags                              |
| 3      | 5    | Seed (5 × uint8)                   |
| 8      | 1    | Energy Hint (uint8)                |
| 9      | 2    | Epoch (uint16)                     |
| 11     | 2    | Anchor Cell (uint16)               |
| 13     | 3    | Offset Vector (int8 × 3)           |
| 16     | 3    | Neighbor Hint (compressed)         |
| 19     | 2    | CRC16                              |

### v2 Flags (extended)

- bit 0 — authoritative seed
- bit 1 — request sync
- bit 2 — relay packet
- bit 3 — exploration enabled
- bit 4 — high-energy node
- bit 5–7 — reserved

### Anchor Grid

World mapped to discrete lattice. Examples:
- Geohash (Earth)
- Local cubic grid (disaster zone)
- Relative mesh (no GPS)

## Protocol Behavior

### Transmission

- Mode: broadcast
- Retry: none required
- Ordering: irrelevant
- Loss: tolerated

### Fault Tolerance

- Packet loss — no issue
- Partial reception — ignored (CRC fail)
- Delayed packet — still valid (epoch-relative)

### Cross-Layer Integration

**TCP layer** (structured): sync, negotiation, multi-hop coordination

**UDP layer** (discovery): identity propagation, recovery after outage

### Recovery Flow

```
[offline nodes]
    ↓
store seed only
    ↓
network returns
    ↓
UDP broadcast seeds
    ↓
agents reconstruct peers locally
    ↓
TCP connections form (optional)
    ↓
refinement / coordination
```

## Core Algorithms

### Multiagent Field Combination

```python
def combine_seeds(seeds, weights=None):
    seeds = [s / s.sum() for s in seeds]
    if weights is None:
        weights = np.ones(len(seeds))
    field = np.zeros(6)
    for s, w in zip(seeds, weights):
        field += w * s
    return field / field.sum()
```

`S_total = Σ S_i → normalized`

### Gradient Routing

Routing = gradient descent in seed space. Packets move "downhill":

```python
def next_hop(target_seed, neighbors):
    return min(neighbors, key=lambda n: seed_distance(n, target_seed))
```

With probabilistic escape for exploration:
```python
if random() < epsilon:
    hop = random.choice(neighbors)
```

### Seed-Space Clustering

```python
def cluster(seeds, threshold=0.1):
    clusters = []
    for s in seeds:
        placed = False
        for c in clusters:
            if seed_distance(s, c[0]) < threshold:
                c.append(s)
                placed = True
                break
        if not placed:
            clusters.append([s])
    return clusters
```

### Convergence

```
routing → brings seeds together
superposition → merges fields
result → shared structure
```

Network converges without central coordination via relaxation:
```python
def relax(seeds, iterations=5):
    for _ in range(iterations):
        seeds = [combine_seeds(seeds) for _ in seeds]
    return seeds
```

## Spatial Coupling (v2+)

### Node State

```python
NodeState = {
    "seed": S,                 # 6D normalized
    "pos": np.array([x,y,z]),  # physical position (meters or local frame)
    "vel": np.array([vx,vy,vz]),
    "energy": E,               # scalar
    "frame": frame_id
}
```

### Cost Function

```
J = α · D_seed(S_i, S_j) + β · D_space(x_i, x_j) + γ · ΔE
```

Where:
- `D_seed` = L1 or cosine distance in 6D
- `D_space` = Euclidean distance
- `ΔE` = energy mismatch penalty

This drives: similar seeds → move closer, dissimilar seeds → separate.

### Stability Conditions

- Bound velocity damping: `node["vel"] *= 0.9`
- Tune seed update rate (`k`)
- Tune neighbor radius

## Key Properties

1. ≤ 24 bytes per packet (radio-safe)
2. Stateless reconstruction (seed sufficient)
3. Deterministic identity
4. Spatial coupling without full coordinates
5. Routing without tables
6. Backward compatibility with v1 seeds

## Constraints

- `expand(seed)` must be identical everywhere
- `combine_seeds()` must be identical everywhere
- Protocol version = hash(expansion rules)

## Emergent Behavior

- Clusters form in space
- Clusters share similar seeds
- Routing becomes spatially coherent
- Field gradients align with geography

## Summary

```
agents = moving field samples
network = dynamic lattice
routing = gradient flow
identity = stable attractor in seed-space
```

This is a distributed physical simulation + network protocol + identity system.

## Next Steps

1. Packet loss + noise injection testing
2. Partition / reconnection test
3. Energy-based authority weighting
4. Real UDP transport swap (drop-in)
5. Multi-frequency / channel layering
