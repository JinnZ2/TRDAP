"""
seed_udp.py — minimal seed broadcast over UDP

Designed for:
- lossy networks
- intermittent connectivity
- broadcast discovery
"""

import socket
import sys
import time
import numpy as np

from seed_protocol_v1 import (
    pack_seed_packet,
    unpack_seed_packet,
    expand
)

PORT = 9400
BROADCAST_IP = "255.255.255.255"


# =============================================================================
# SENDER
# =============================================================================

def send_loop(seed):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        pkt = pack_seed_packet(
            seed,
            frame_id=1,
            flags=0b00000001,
            energy_hint=128,
            epoch=int(time.time()) & 0xFFFF
        )

        sock.sendto(pkt, (BROADCAST_IP, PORT))
        print("sent seed packet")

        time.sleep(1.0)


# =============================================================================
# RECEIVER
# =============================================================================

def receive_loop():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT))

    seen = []

    while True:
        data, addr = sock.recvfrom(1024)

        try:
            decoded = unpack_seed_packet(data)
        except ValueError:
            continue

        seed = decoded["seed"]

        # deduplicate
        if any(np.allclose(seed, s, atol=0.05) for s in seen):
            continue

        seen.append(seed)

        print(f"\nreceived from {addr}")
        shells = expand(seed, steps=3)

        for i, s in enumerate(shells):
            print(f"  shell {i}: {np.round(s['S'], 3)}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python seed-udp.py [send|recv]")
        sys.exit(1)

    if sys.argv[1] == "send":
        seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
        send_loop(seed)

    elif sys.argv[1] == "recv":
        receive_loop()
