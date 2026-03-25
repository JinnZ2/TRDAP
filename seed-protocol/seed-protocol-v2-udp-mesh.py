# =============================================================================
# SEED PROTOCOL v2 — REAL UDP MESH
# =============================================================================

import socket
import threading
import numpy as np
import struct
import random
import time

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
NUM_NODES = 5              # adjust as needed
BASE_PORT = 50000
COMM_RANGE = 200.0
SEED_DRIFT = 0.02
POS_DRIFT = 5.0
SIM_STEP = 1.0             # seconds per step

# -----------------------------------------------------------------------------
# PACKET UTILITIES (simple float arrays)
# -----------------------------------------------------------------------------
def pack_packet(seed, pos, energy=100, epoch=0):
    # seed: 6 floats, pos: 3 floats, energy, epoch: int
    return struct.pack('6f3f2i', *(list(seed)+list(pos)+[energy, epoch]))

def unpack_packet(pkt):
    data = struct.unpack('6f3f2i', pkt)
    seed = np.array(data[0:6])
    pos  = np.array(data[6:9])
    energy, epoch = data[9:11]
    return {"seed": seed, "position": pos, "energy": energy, "epoch": epoch}

# -----------------------------------------------------------------------------
# NODE DEFINITION
# -----------------------------------------------------------------------------
class Node:
    def __init__(self, node_id, port):
        self.id = node_id
        self.port = port

        self.pos = np.random.rand(3) * 1000.0
        s = np.random.rand(6)
        self.seed = s / s.sum()
        self.energy = random.randint(80, 200)
        self.epoch = 0

        self.inbox = []

        # UDP socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.port))
        self.sock.setblocking(False)

        # threading lock
        self.lock = threading.Lock()

    # --- broadcast to all known node ports ---
    def broadcast(self, ports):
        pkt = pack_packet(self.seed, self.pos, self.energy, self.epoch)
        for p in ports:
            if p == self.port:
                continue
            self.sock.sendto(pkt, ('localhost', p))

    # --- receive loop ---
    def receive_loop(self):
        while True:
            try:
                pkt, addr = self.sock.recvfrom(1024)
                data = unpack_packet(pkt)
                with self.lock:
                    self.inbox.append(data)
            except BlockingIOError:
                time.sleep(0.01)

    # --- update state based on inbox ---
    def update(self):
        with self.lock:
            if not self.inbox:
                return

            neighbor_seeds = [msg["seed"] for msg in self.inbox]
            neighbor_positions = [msg["position"] for msg in self.inbox]

            # --- SEED UPDATE ---
            combined = combine_seeds([self.seed]+neighbor_seeds)
            self.seed = (1 - SEED_DRIFT)*self.seed + SEED_DRIFT*combined
            self.seed /= self.seed.sum()

            # --- POSITION UPDATE ---
            avg_pos = np.mean(neighbor_positions, axis=0)
            self.pos += POS_DRIFT * (avg_pos - self.pos)/(np.linalg.norm(avg_pos - self.pos)+1e-6)
            self.pos += np.random.randn(3) * 0.5  # noise

            self.inbox = []
            self.epoch += 1

# -----------------------------------------------------------------------------
# COMBINE SEEDS (same as simulation)
# -----------------------------------------------------------------------------
def seed_distance(a, b):
    return np.linalg.norm(a - b)

def combine_seeds(seeds):
    return np.mean(seeds, axis=0)

# -----------------------------------------------------------------------------
# INIT NODES
# -----------------------------------------------------------------------------
nodes = []
ports = [BASE_PORT+i for i in range(NUM_NODES)]

for i in range(NUM_NODES):
    n = Node(i, ports[i])
    t = threading.Thread(target=n.receive_loop, daemon=True)
    t.start()
    nodes.append(n)

# -----------------------------------------------------------------------------
# RUN MESH
# -----------------------------------------------------------------------------
try:
    while True:
        for n in nodes:
            n.broadcast(ports)
        time.sleep(SIM_STEP)
        for n in nodes:
            n.update()
        # show metrics
        seed_var = np.mean([np.var(n.seed) for n in nodes])
        positions = np.array([n.pos for n in nodes])
        centroid = np.mean(positions, axis=0)
        spread = np.mean(np.linalg.norm(positions - centroid, axis=1))
        print(f"epoch {nodes[0].epoch} | seed_var={seed_var:.4f} | spread={spread:.2f}")
except KeyboardInterrupt:
    print("UDP mesh terminated.")
