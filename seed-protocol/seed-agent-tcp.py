"""
seed_agent_tcp.py — Seed-native agents over TCP

Requires:
- seed_protocol_v1.py (same directory or importable)
- your existing Agent / TCPTransport

Behavior:
- Agents exchange SeedPackets instead of strings
- Each agent reconstructs local field from received seed
- Identity + sync derived from seed similarity
"""

import time
import numpy as np

from core import Agent, Message
from transports import TCPTransport

from seed_protocol_v1 import (
    pack_seed_packet,
    unpack_seed_packet,
    expand,
    same_entity
)


# =============================================================================
# BASE SEED AGENT
# =============================================================================

class SeedAgent(Agent):

    def __init__(self, seed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seed = np.array(seed, dtype=float)
        self.shells = expand(self.seed, steps=4)
        self.known_seeds = []

    # -------------------------------------------------------------------------

    def build_packet(self):
        return pack_seed_packet(
            self.seed,
            frame_id=1,
            flags=0b00000001,  # authoritative
            energy_hint=128,
            epoch=int(time.time()) & 0xFFFF
        )

    # -------------------------------------------------------------------------

    def broadcast_seed(self):
        pkt = self.build_packet()
        for peer_id in self.peers:
            self.send(
                Message(
                    verb="SEED",
                    recipient=peer_id,
                    body=pkt
                )
            )

    # -------------------------------------------------------------------------

    def on_message(self, msg: Message):

        if msg.verb != "SEED":
            return

        data = unpack_seed_packet(msg.body)
        incoming_seed = data["seed"]

        # Compare identity
        for known in self.known_seeds:
            if same_entity(incoming_seed, known):
                return  # already known

        self.known_seeds.append(incoming_seed)

        # Reconstruct field locally
        shells = expand(incoming_seed, steps=4)

        print(f"[{self.id}] received seed → reconstructed:")
        for i, s in enumerate(shells[:3]):
            print(f"  shell {i}: {np.round(s['S'], 3)}")

        # Optional: respond back (mesh propagation)
        self.broadcast_seed()


# =============================================================================
# MAIN
# =============================================================================

def main():

    t_a = TCPTransport(host="127.0.0.1", port=9300)
    t_b = TCPTransport(host="127.0.0.1", port=9301)

    t_a.add_peer("agent_B", "127.0.0.1", 9301)
    t_b.add_peer("agent_A", "127.0.0.1", 9300)

    agent_A = SeedAgent(
        seed=[0.5, 0.2, 0.15, 0.08, 0.05, 0.02],
        agent_id="agent_A",
        agent_type="SeedNode",
        transport=t_a,
        capabilities=["seed_field"]
    )

    agent_B = SeedAgent(
        seed=[0.48, 0.22, 0.14, 0.09, 0.05, 0.02],
        agent_id="agent_B",
        agent_type="SeedNode",
        transport=t_b,
        capabilities=["seed_field"]
    )

    agent_A.start()
    agent_B.start()

    time.sleep(0.5)

    print("\n--- Seed Exchange ---")
    agent_A.broadcast_seed()

    time.sleep(1.0)

    agent_A.stop()
    agent_B.stop()


if __name__ == "__main__":
    main()
