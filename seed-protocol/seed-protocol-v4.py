# =============================================================================
# SEED PROTOCOL v4 — MULTI-MACHINE LAN UDP MESH
# =============================================================================
#
# Extends v3 with multicast for multi-machine LAN operation.
# Uses v_raw packet format with node_id. Core functions from seed_core.py.
#
# Fallback chain: v4 (multicast/raw) → v3 (udp/raw) → v2 (encoded) → v1 (minimal)

import socket
import struct
import threading
import numpy as np
import random
import time

from seed_core import combine_seeds
from seed_packet import pack_raw, unpack_raw

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 50000

NUM_NODES_LOCAL = 1       # each machine runs 1 or more nodes
COMM_RANGE = 200.0        # virtual distance range (for filtering)
SEED_DRIFT = 0.02
POS_DRIFT = 5.0
SIM_STEP = 1.0             # seconds per simulation step
PACKET_LOSS = 0.05         # 5% packet drop
JITTER = 0.05              # seconds of random delay


# Thin wrappers to maintain v4's (node_id, seed, pos) calling convention
def pack_packet(node_id, seed, pos, energy=100, epoch=0):
    return pack_raw(seed, pos, energy, epoch, node_id=node_id)

def unpack_packet(pkt):
    data = unpack_raw(pkt)
    # Map to v4's expected key names
    return {
        "id": data.get("node_id", 0),
        "seed": data["seed"],
        "position": data["position"],
        "energy": data["energy_hint"],
        "epoch": data["epoch"],
    }

# -----------------------------------------------------------------------------
# NODE DEFINITION
# -----------------------------------------------------------------------------
class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.pos = np.random.rand(3) * 1000.0
        s = np.random.rand(6)
        self.seed = s / s.sum()
        self.energy = random.randint(80, 200)
        self.epoch = 0
        self.inbox = []
        self.lock = threading.Lock()

    # --- broadcast to multicast group ---
    def broadcast(self, sock):
        pkt = pack_packet(self.id, self.seed, self.pos, self.energy, self.epoch)
        if random.random() < PACKET_LOSS:
            return
        delay = random.uniform(0, JITTER)
        threading.Timer(delay, lambda: sock.sendto(pkt, (MULTICAST_GROUP, MULTICAST_PORT))).start()

    # --- update node state from inbox ---
    def update(self):
        with self.lock:
            if not self.inbox:
                return
            neighbor_seeds = [msg["seed"] for msg in self.inbox if msg["id"] != self.id]
            neighbor_positions = [msg["position"] for msg in self.inbox if msg["id"] != self.id]
            if neighbor_seeds:
                self.seed = (1-SEED_DRIFT)*self.seed + SEED_DRIFT*combine_seeds([self.seed]+neighbor_seeds)
                self.seed /= self.seed.sum()
            if neighbor_positions:
                avg_pos = np.mean(neighbor_positions, axis=0)
                self.pos += POS_DRIFT * (avg_pos - self.pos)/(np.linalg.norm(avg_pos - self.pos)+1e-6)
                self.pos += np.random.randn(3) * 0.5
            self.inbox = []
            self.epoch += 1

# -----------------------------------------------------------------------------
# MULTICAST SOCKET
# -----------------------------------------------------------------------------
def create_multicast_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setblocking(False)
    return sock

# -----------------------------------------------------------------------------
# RECEIVE LOOP
# -----------------------------------------------------------------------------
def receive_loop(sock, nodes):
    while True:
        try:
            pkt, addr = sock.recvfrom(1024)
            data = unpack_packet(pkt)
            # range filtering (optional, virtual distance)
            for n in nodes:
                distance = np.linalg.norm(n.pos - data["position"])
                if distance <= COMM_RANGE:
                    with n.lock:
                        n.inbox.append(data)
        except BlockingIOError:
            time.sleep(0.01)

# -----------------------------------------------------------------------------
# INIT NODES
# -----------------------------------------------------------------------------
nodes = [Node(i) for i in range(NUM_NODES_LOCAL)]
sock = create_multicast_socket()

t = threading.Thread(target=receive_loop, args=(sock, nodes), daemon=True)
t.start()

# -----------------------------------------------------------------------------
# RUN SIMULATION
# -----------------------------------------------------------------------------
try:
    while True:
        for n in nodes:
            n.broadcast(sock)
        time.sleep(SIM_STEP)
        for n in nodes:
            n.update()
        seed_var = np.mean([np.var(n.seed) for n in nodes])
        positions = np.array([n.pos for n in nodes])
        centroid = np.mean(positions, axis=0)
        spread = np.mean(np.linalg.norm(positions - centroid, axis=1))
        print(f"epoch {nodes[0].epoch} | seed_var={seed_var:.4f} | spread={spread:.2f}")
except KeyboardInterrupt:
    print("LAN multicast mesh terminated.")
