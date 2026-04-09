"""
protocols.py — Hot-reloadable emergency protocols for TRDAP AI agents.

In a real emergency, procedures change fast:
  - New hazards identified → updated safety protocols
  - Resources exhausted → alternative procedures activated
  - Communication channels lost → fallback protocols loaded
  - Authority transferred → command structure updated

This module lets AI agents load, reload, and switch protocols at runtime
without retraining or restarting. Protocols are JSON runbooks stored in
ai-pipeline/em/runbooks/ and validated before activation.

Design principles:
  1. Protocols are DATA, not code — no eval/exec, ever
  2. Every protocol change is audited
  3. Fallback chain: always have a degraded-mode protocol
  4. Agents MUST check protocol version before acting

License: CC0 1.0
"""

import json
import os
import time
import hashlib

# ---------------------------------------------------------------------------
# Protocol Schema
# ---------------------------------------------------------------------------

REQUIRED_PROTOCOL_FIELDS = {
    "protocol_id", "version", "name", "urgency_level",
    "steps", "fallback_protocol_id",
}

VALID_STEP_TYPES = {
    "assess",       # evaluate situation
    "communicate",  # send message / alert
    "allocate",     # assign resources
    "stage",        # pre-position resources
    "execute",      # take action
    "escalate",     # push decision upward
    "override",     # bypass normal procedure (requires authority)
    "verify",       # confirm action completed
    "document",     # record decision / outcome
}


# ---------------------------------------------------------------------------
# Protocol Validator
# ---------------------------------------------------------------------------

def validate_protocol(protocol):
    """Validate a protocol dict against the schema.

    Returns (valid: bool, errors: list[str]).
    """
    errors = []

    missing = REQUIRED_PROTOCOL_FIELDS - set(protocol.keys())
    if missing:
        errors.append(f"missing fields: {missing}")

    steps = protocol.get("steps", [])
    if not steps:
        errors.append("protocol has no steps")

    for i, step in enumerate(steps):
        if "type" not in step:
            errors.append(f"step[{i}]: missing 'type'")
        elif step["type"] not in VALID_STEP_TYPES:
            errors.append(f"step[{i}]: invalid type '{step['type']}'")

        if "action" not in step:
            errors.append(f"step[{i}]: missing 'action'")

        # Override steps must declare required authority
        if step.get("type") == "override" and "required_authority" not in step:
            errors.append(f"step[{i}]: override step must declare 'required_authority'")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Protocol Registry (hot-reloadable)
# ---------------------------------------------------------------------------

class ProtocolRegistry:
    """Runtime registry of emergency protocols.

    Loads from JSON runbook files. Supports hot-reload: when conditions
    change, call reload() or load_protocol() to update without restart.
    """

    def __init__(self, runbook_dir=None):
        self.protocols = {}       # protocol_id -> protocol dict
        self.active_protocol = None
        self.history = []         # protocol activation history
        self.runbook_dir = runbook_dir

        if runbook_dir and os.path.isdir(runbook_dir):
            self.load_all(runbook_dir)

    def load_all(self, runbook_dir):
        """Load all .json runbooks from a directory."""
        self.runbook_dir = runbook_dir
        loaded = 0

        for fname in sorted(os.listdir(runbook_dir)):
            if not fname.endswith(".json"):
                continue
            filepath = os.path.join(runbook_dir, fname)
            try:
                self.load_protocol(filepath)
                loaded += 1
            except (json.JSONDecodeError, ValueError) as e:
                print(f"WARN: skipping {fname}: {e}")

        return loaded

    def load_protocol(self, filepath):
        """Load a single protocol from a JSON file.

        Validates before accepting. Replaces existing protocol with
        same ID if version is newer.
        """
        with open(filepath, "r") as f:
            protocol = json.load(f)

        valid, errors = validate_protocol(protocol)
        if not valid:
            raise ValueError(f"invalid protocol: {errors}")

        pid = protocol["protocol_id"]

        # Version check: only accept newer versions
        if pid in self.protocols:
            existing_ver = self.protocols[pid].get("version", 0)
            new_ver = protocol.get("version", 0)
            if new_ver <= existing_ver:
                return  # skip older version

        # Compute integrity hash
        raw = json.dumps(protocol, sort_keys=True)
        protocol["_hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]
        protocol["_loaded_at"] = time.time()
        protocol["_source"] = filepath

        self.protocols[pid] = protocol

    def reload(self):
        """Hot-reload all protocols from the runbook directory."""
        if self.runbook_dir:
            return self.load_all(self.runbook_dir)
        return 0

    def activate(self, protocol_id, agent_id="system", reason=""):
        """Set the active protocol. Logged for audit."""
        if protocol_id not in self.protocols:
            return False, f"unknown protocol: {protocol_id}"

        prev = self.active_protocol
        self.active_protocol = protocol_id

        self.history.append({
            "timestamp": time.time(),
            "from_protocol": prev,
            "to_protocol": protocol_id,
            "agent_id": agent_id,
            "reason": reason,
        })

        return True, f"activated {protocol_id}"

    def get_active(self):
        """Get the currently active protocol."""
        if self.active_protocol and self.active_protocol in self.protocols:
            return self.protocols[self.active_protocol]
        return None

    def get_steps(self, protocol_id=None):
        """Get steps for a protocol (default: active)."""
        pid = protocol_id or self.active_protocol
        if pid and pid in self.protocols:
            return self.protocols[pid].get("steps", [])
        return []

    def get_fallback(self, protocol_id=None):
        """Get the fallback protocol for degraded operations."""
        pid = protocol_id or self.active_protocol
        if pid and pid in self.protocols:
            fallback_id = self.protocols[pid].get("fallback_protocol_id")
            if fallback_id and fallback_id in self.protocols:
                return self.protocols[fallback_id]
        return None

    def list_protocols(self):
        """List all loaded protocols with metadata."""
        result = []
        for pid, proto in self.protocols.items():
            result.append({
                "protocol_id": pid,
                "name": proto.get("name", ""),
                "version": proto.get("version", 0),
                "urgency_level": proto.get("urgency_level", ""),
                "steps_count": len(proto.get("steps", [])),
                "active": pid == self.active_protocol,
            })
        return result
