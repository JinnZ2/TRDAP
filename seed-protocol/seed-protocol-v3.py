# =============================================================================
# SEED PROTOCOL v3 — RANGE-LIMITED UDP MESH WITH JITTER
# =============================================================================
#
# Extends v2-udp-mesh with packet loss simulation and jitter.
# Uses v_raw packet format. Core functions from seed_core.py.
#
# Fallback: if nodes can't decode raw packets, they should try v2/v1.

import socket
import threading
import numpy as np
import random
import time

from seed_core import combine_seeds
from seed_packet import pack_raw as pack_packet, unpack_raw as unpack_packet

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
NUM_NODES = 5
BASE_PORT = 50000
COMM_RANGE = 200.0     # max distance for messages
SEED_DRIFT = 0.02
POS_DRIFT = 5.0
SIM_STEP = 1.0         # seconds per simulation step

PACKET_LOSS = 0.1      # 10% packet drop
JITTER = 0.05          # seconds of random delay

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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.port))
        self.sock.setblocking(False)
        self.lock = threading.Lock()

    # --- broadcast with range + loss/jitter ---
    def broadcast(self, nodes):
        pkt = pack_packet(self.seed, self.pos, self.energy, self.epoch)
        for n in nodes:
            if n.port == self.port:
                continue
            distance = np.linalg.norm(self.pos - n.pos)
            if distance > COMM_RANGE:
                continue
            if random.random() < PACKET_LOSS:
                continue
            # simulate jitter
            delay = random.uniform(0, JITTER)
            threading.Timer(delay, lambda: n.sock.sendto(pkt, ('localhost', n.port))).start()

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

    # --- update state ---
    def update(self):
        with self.lock:
            if not self.inbox:
                return
            neighbor_seeds = [msg["seed"] for msg in self.inbox]
            neighbor_positions = [msg["position"] for msg in self.inbox]
            self.seed = (1-SEED_DRIFT)*self.seed + SEED_DRIFT*combine_seeds([self.seed]+neighbor_seeds)
            self.seed /= self.seed.sum()
            avg_pos = np.mean(neighbor_positions, axis=0)
            self.pos += POS_DRIFT * (avg_pos - self.pos)/(np.linalg.norm(avg_pos - self.pos)+1e-6)
            self.pos += np.random.randn(3) * 0.5
            self.inbox = []
            self.epoch += 1

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
# RUN SIMULATION
# -----------------------------------------------------------------------------
try:
    while True:
        for n in nodes:
            n.broadcast(nodes)
        time.sleep(SIM_STEP)
        for n in nodes:
            n.update()
        seed_var = np.mean([np.var(n.seed) for n in nodes])
        positions = np.array([n.pos for n in nodes])
        centroid = np.mean(positions, axis=0)
        spread = np.mean(np.linalg.norm(positions - centroid, axis=1))
        print(f"epoch {nodes[0].epoch} | seed_var={seed_var:.4f} | spread={spread:.2f}")
except KeyboardInterrupt:
    print("UDP mesh terminated.")
