"""
staging.py — Agent staging and multi-agent communication for TRDAP EM.

In ICS, staging areas are where resources wait for assignment.
This module implements the same concept for AI agents:

  - Agents register in staging areas by capability
  - Dispatch assigns agents to tasks based on urgency and capability
  - Agents communicate via message bus (works over TRDAP mesh)
  - Degraded mode: agents operate autonomously with last-known protocols

Communication modes (in order of preference):
  1. TCP direct — full bandwidth, structured messages
  2. UDP multicast — broadcast discovery, mesh sync
  3. LoRa/Meshtastic — degraded, 512-byte TRDAP packets
  4. Morse/optical — extreme fallback, beacon-only

License: CC0 1.0
"""

import json
import time
import uuid

# ---------------------------------------------------------------------------
# Agent Capabilities (ICS resource typing)
# ---------------------------------------------------------------------------

AGENT_CAPABILITIES = {
    "resource_predictor":   {"ics_type": "planning", "priority": 2},
    "urgency_classifier":   {"ics_type": "operations", "priority": 1},
    "route_optimizer":      {"ics_type": "logistics", "priority": 2},
    "communication_relay":  {"ics_type": "operations", "priority": 1},
    "status_monitor":       {"ics_type": "planning", "priority": 3},
    "data_validator":       {"ics_type": "planning", "priority": 3},
}

# Communication modes in degradation order
COMM_MODES = [
    {"mode": "tcp_direct",    "bandwidth": "high",   "latency": "low",    "max_bytes": None},
    {"mode": "udp_multicast", "bandwidth": "medium", "latency": "low",    "max_bytes": 65535},
    {"mode": "trdap_mesh",    "bandwidth": "low",    "latency": "medium", "max_bytes": 512},
    {"mode": "morse_beacon",  "bandwidth": "minimal","latency": "high",   "max_bytes": 64},
]


# ---------------------------------------------------------------------------
# Agent Registration
# ---------------------------------------------------------------------------

class AgentRecord:
    """Registration record for a staged agent."""

    def __init__(self, agent_id, capabilities, position=None, comm_modes=None):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.position = position        # [x, y, z] or None
        self.comm_modes = comm_modes or ["tcp_direct"]
        self.status = "staged"          # staged, assigned, active, offline
        self.assigned_task = None
        self.last_heartbeat = time.time()
        self.registered_at = time.time()

    def is_alive(self, timeout=60):
        return (time.time() - self.last_heartbeat) < timeout

    def heartbeat(self):
        self.last_heartbeat = time.time()

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "position": self.position,
            "comm_modes": self.comm_modes,
            "status": self.status,
            "assigned_task": self.assigned_task,
            "last_heartbeat": self.last_heartbeat,
        }


# ---------------------------------------------------------------------------
# Staging Area
# ---------------------------------------------------------------------------

class StagingArea:
    """ICS-style staging area for AI agents.

    Agents register here and wait for dispatch. The staging area
    tracks capabilities, availability, and communication status.
    """

    def __init__(self, staging_id=None):
        self.staging_id = staging_id or f"STG-{uuid.uuid4().hex[:8]}"
        self.agents = {}        # agent_id -> AgentRecord
        self.task_queue = []    # pending tasks
        self.dispatch_log = []  # assignment history

    def register(self, agent_id, capabilities, position=None, comm_modes=None):
        """Register an agent in the staging area."""
        record = AgentRecord(agent_id, capabilities, position, comm_modes)
        self.agents[agent_id] = record
        return record

    def deregister(self, agent_id):
        """Remove an agent from staging."""
        self.agents.pop(agent_id, None)

    def get_available(self, capability=None):
        """Get agents that are staged and alive."""
        available = []
        for record in self.agents.values():
            if not record.is_alive():
                record.status = "offline"
                continue
            if record.status not in ("staged", "active"):
                continue
            if capability and capability not in record.capabilities:
                continue
            available.append(record)
        return available

    def dispatch(self, task):
        """Assign the best available agent to a task.

        Matches by capability and priority. Returns the assigned agent
        or None if no suitable agent is available.
        """
        required_cap = task.get("required_capability")
        urgency = task.get("urgency", "medium")

        candidates = self.get_available(required_cap)
        if not candidates:
            self.task_queue.append(task)
            return None

        # Sort by capability priority (lower = higher priority)
        def priority_key(record):
            cap_info = AGENT_CAPABILITIES.get(required_cap, {})
            return cap_info.get("priority", 99)

        candidates.sort(key=priority_key)
        assigned = candidates[0]

        assigned.status = "assigned"
        assigned.assigned_task = task

        self.dispatch_log.append({
            "timestamp": time.time(),
            "task": task,
            "agent_id": assigned.agent_id,
            "urgency": urgency,
        })

        return assigned

    def process_queue(self):
        """Try to dispatch queued tasks."""
        remaining = []
        for task in self.task_queue:
            result = self.dispatch(task)
            if result is None:
                remaining.append(task)
        self.task_queue = remaining

    def status_report(self):
        """Generate an ICS-style status report."""
        total = len(self.agents)
        by_status = {}
        by_capability = {}

        for record in self.agents.values():
            by_status[record.status] = by_status.get(record.status, 0) + 1
            for cap in record.capabilities:
                by_capability[cap] = by_capability.get(cap, 0) + 1

        return {
            "staging_id": self.staging_id,
            "timestamp": time.time(),
            "total_agents": total,
            "by_status": by_status,
            "by_capability": by_capability,
            "queued_tasks": len(self.task_queue),
        }


# ---------------------------------------------------------------------------
# Message Bus (multi-mode communication)
# ---------------------------------------------------------------------------

class MessageBus:
    """Multi-mode message bus for agent-to-agent communication.

    Automatically degrades communication mode based on what's available.
    Messages are TRDAP-compatible (<=512 bytes when on mesh mode).
    """

    def __init__(self):
        self.subscribers = {}    # channel -> [agent_ids]
        self.message_log = []
        self.available_modes = ["tcp_direct"]  # start with best available

    def set_available_modes(self, modes):
        """Update available communication modes (e.g., after network change)."""
        self.available_modes = modes

    def best_mode(self):
        """Return the highest-bandwidth available mode."""
        for mode_info in COMM_MODES:
            if mode_info["mode"] in self.available_modes:
                return mode_info
        return COMM_MODES[-1]  # morse_beacon as last resort

    def subscribe(self, agent_id, channel):
        """Subscribe an agent to a communication channel."""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        if agent_id not in self.subscribers[channel]:
            self.subscribers[channel].append(agent_id)

    def unsubscribe(self, agent_id, channel):
        """Unsubscribe an agent from a channel."""
        if channel in self.subscribers:
            self.subscribers[channel] = [
                a for a in self.subscribers[channel] if a != agent_id
            ]

    def publish(self, sender_id, channel, message):
        """Publish a message to a channel.

        Automatically truncates for constrained modes.
        """
        mode = self.best_mode()
        max_bytes = mode.get("max_bytes")

        msg_envelope = {
            "id": uuid.uuid4().hex[:12],
            "sender": sender_id,
            "channel": channel,
            "timestamp": time.time(),
            "mode": mode["mode"],
            "payload": message,
        }

        # Enforce size limits for constrained channels
        if max_bytes:
            raw = json.dumps(msg_envelope)
            if len(raw.encode("utf-8")) > max_bytes:
                # Truncate payload to fit
                overhead = len(json.dumps({**msg_envelope, "payload": ""}).encode("utf-8"))
                available = max_bytes - overhead - 10  # safety margin
                if isinstance(message, str):
                    msg_envelope["payload"] = message[:available]
                    msg_envelope["truncated"] = True
                elif isinstance(message, dict):
                    # Keep only essential fields
                    essential = {}
                    for key in ("urgency", "type", "action", "hub_id"):
                        if key in message:
                            essential[key] = message[key]
                    msg_envelope["payload"] = essential
                    msg_envelope["truncated"] = True

        self.message_log.append(msg_envelope)

        # Return list of recipient agent_ids
        recipients = self.subscribers.get(channel, [])
        return {
            "message_id": msg_envelope["id"],
            "mode": mode["mode"],
            "recipients": recipients,
            "truncated": msg_envelope.get("truncated", False),
        }

    def broadcast(self, sender_id, message):
        """Broadcast to ALL channels (critical/emergency use)."""
        results = []
        for channel in self.subscribers:
            result = self.publish(sender_id, channel, message)
            results.append(result)
        return results

    def get_messages(self, channel=None, since=None):
        """Retrieve messages, optionally filtered by channel and time."""
        msgs = self.message_log
        if channel:
            msgs = [m for m in msgs if m["channel"] == channel]
        if since:
            msgs = [m for m in msgs if m["timestamp"] >= since]
        return msgs
