# =============================================================================
# SEED PROTOCOL v2 — MULTI-NODE SIMULATION HARNESS
# =============================================================================

import numpy as np
import random

# ---- imports from seed-protocol-v2.py ----
from seed_protocol_v2 import pack_packet, unpack_packet, seed_distance, combine_seeds

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

NUM_NODES = 40
SPACE_SIZE = 1000.0
COMM_RANGE = 200.0
STEPS = 50

SEED_DRIFT = 0.02
POS_DRIFT  = 5.0

# -----------------------------------------------------------------------------
# NODE DEFINITION
# -----------------------------------------------------------------------------

class Node:
    def __init__(self, node_id):
        self.id = node_id

        # random position
        self.pos = np.random.rand(3) * SPACE_SIZE

        # random seed (normalized)
        s = np.random.rand(6)
        self.seed = s / s.sum()

        self.energy = random.randint(80, 200)
        self.epoch = 0

        self.inbox = []

    def broadcast(self):
        pkt = pack_packet(
            self.seed,
            self.pos,
            energy=self.energy,
            epoch=self.epoch
        )
        return pkt

    def receive(self, pkt):
        try:
            data = unpack_packet(pkt)
            self.inbox.append(data)
        except ValueError:
            pass  # drop corrupted

    def update(self):
        if not self.inbox:
            return

        neighbor_seeds = []
        neighbor_positions = []

        for msg in self.inbox:
            neighbor_seeds.append(msg["seed"])
            neighbor_positions.append(msg["position"])

        # --- SEED UPDATE (field coupling) ---
        combined = combine_seeds([self.seed] + neighbor_seeds)
        self.seed = (1 - SEED_DRIFT) * self.seed + SEED_DRIFT * combined
        self.seed /= self.seed.sum()

        # --- POSITION UPDATE (attraction) ---
        avg_pos = np.mean(neighbor_positions, axis=0)
        self.pos += POS_DRIFT * (avg_pos - self.pos) / (np.linalg.norm(avg_pos - self.pos) + 1e-6)

        # small noise to prevent collapse
        self.pos += np.random.randn(3) * 0.5

        # clear inbox
        self.inbox = []
        self.epoch += 1


# -----------------------------------------------------------------------------
# SIMULATION
# -----------------------------------------------------------------------------

nodes = [Node(i) for i in range(NUM_NODES)]

def distance(a, b):
    return np.linalg.norm(a - b)

def step_sim():
    # broadcast phase
    packets = []
    for node in nodes:
        pkt = node.broadcast()
        packets.append((node, pkt))

    # receive phase (range-limited)
    for sender, pkt in packets:
        for receiver in nodes:
            if sender.id == receiver.id:
                continue
            if distance(sender.pos, receiver.pos) < COMM_RANGE:
                receiver.receive(pkt)

    # update phase
    for node in nodes:
        node.update()


# -----------------------------------------------------------------------------
# METRICS
# -----------------------------------------------------------------------------

def compute_metrics():
    seeds = np.array([n.seed for n in nodes])
    positions = np.array([n.pos for n in nodes])

    # seed variance (cluster formation)
    seed_var = np.mean(np.var(seeds, axis=0))

    # spatial spread
    centroid = np.mean(positions, axis=0)
    spatial_spread = np.mean(np.linalg.norm(positions - centroid, axis=1))

    return seed_var, spatial_spread


# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    print("\n=== SIMULATION START ===\n")

    for step in range(STEPS):
        step_sim()

        if step % 5 == 0:
            seed_var, spread = compute_metrics()
            print(f"step {step:02d} | seed_var={seed_var:.4f} | spread={spread:.2f}")

    print("\n=== FINAL STATE ===\n")

    # show a few nodes
    for i in range(5):
        n = nodes[i]
        print(f"Node {n.id}")
        print("  pos:", np.round(n.pos, 1))
        print("  seed:", np.round(n.seed, 3))
        print()


    # -------------------------------------------------------------------------
    # OPTIONAL: ROUTING TEST
    # -------------------------------------------------------------------------

    def route(source_id, target_id, max_hops=10):
        current = nodes[source_id]
        target = nodes[target_id]

        path = [current.id]

        for _ in range(max_hops):
            # find neighbors in range
            neighbors = [
                n for n in nodes
                if n.id != current.id and distance(n.pos, current.pos) < COMM_RANGE
            ]

            if not neighbors:
                break

            # choose best next hop
            next_node = min(
                neighbors,
                key=lambda n:
                    0.7 * seed_distance(n.seed, target.seed) +
                    0.3 * distance(n.pos, target.pos)
            )

            current = next_node
            path.append(current.id)

            if current.id == target.id:
                break

        return path


    print("\n=== ROUTING TEST ===\n")

    src = 0
    dst = random.randint(1, NUM_NODES - 1)

    path = route(src, dst)

    print(f"Route {src} → {dst}:")
    print(" -> ".join(map(str, path)))
