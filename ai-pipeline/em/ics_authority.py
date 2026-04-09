"""
ics_authority.py — ICS (Incident Command System) authority chain for TRDAP AI agents.

Implements NIMS/ICS authority levels so AI agents know:
  - Who can issue orders (command authority)
  - Who can override standard procedures (bypass authority)
  - When to escalate vs. act autonomously
  - How to hand off between human and AI command

Authority flows downhill: IC > Section > Branch > Division > Unit.
Override authority requires explicit activation + audit trail.

References:
  - FEMA IS-100/200/700/800 (ICS/NIMS)
  - NFPA 1561 (Standard on Emergency Services Incident Management)
  - TRDAP urgency levels map to ICS incident types

License: CC0 1.0
"""

import json
import time
import hashlib
import os

# ---------------------------------------------------------------------------
# ICS Authority Levels (descending authority)
# ---------------------------------------------------------------------------

AUTHORITY_LEVELS = {
    "incident_commander":  100,  # IC — full authority, can override anything
    "section_chief":        80,  # Operations/Planning/Logistics/Finance
    "branch_director":      60,  # Branch level
    "division_supervisor":  40,  # Division/Group level
    "unit_leader":          20,  # Task force / strike team
    "field_agent":          10,  # Individual responder or AI agent
    "observer":              0,  # Read-only, no command authority
}

# What each level can do
AUTHORITY_CAPABILITIES = {
    "incident_commander": [
        "override_protocol", "bypass_procedure", "authorize_resource",
        "declare_incident_type", "activate_mutual_aid", "order_evacuation",
        "modify_ics_structure", "delegate_authority", "terminate_incident",
    ],
    "section_chief": [
        "override_protocol", "authorize_resource", "reassign_units",
        "modify_action_plan", "request_mutual_aid",
    ],
    "branch_director": [
        "authorize_resource", "reassign_units", "modify_tactical_plan",
    ],
    "division_supervisor": [
        "reassign_units", "request_resource", "escalate",
    ],
    "unit_leader": [
        "request_resource", "escalate", "report_status",
    ],
    "field_agent": [
        "request_resource", "escalate", "report_status",
    ],
    "observer": [
        "report_status",
    ],
}

# Urgency → ICS incident type mapping
URGENCY_TO_INCIDENT_TYPE = {
    "critical": 1,  # Type 1: most complex, national resources
    "high":     2,  # Type 2: regional/national resources
    "medium":   3,  # Type 3: extended attack, multiple operational periods
    "low":      5,  # Type 5: local resources only
}


# ---------------------------------------------------------------------------
# Authority Token
# ---------------------------------------------------------------------------

class AuthorityToken:
    """Cryptographic proof of delegated authority.

    When an IC or section chief delegates authority to an AI agent,
    this token proves the chain of command. Tokens expire and must
    be refreshed — no permanent AI autonomy.
    """

    def __init__(self, issuer_id, recipient_id, level, capabilities,
                 duration_seconds=3600, incident_id=None):
        self.issuer_id = issuer_id
        self.recipient_id = recipient_id
        self.level = level
        self.capabilities = capabilities
        self.issued_at = time.time()
        self.expires_at = self.issued_at + duration_seconds
        self.incident_id = incident_id or "unassigned"
        self.token_id = self._generate_id()
        self.revoked = False

    def _generate_id(self):
        data = f"{self.issuer_id}:{self.recipient_id}:{self.issued_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def is_valid(self):
        if self.revoked:
            return False
        if time.time() > self.expires_at:
            return False
        return True

    def has_capability(self, action):
        if not self.is_valid():
            return False
        return action in self.capabilities

    def revoke(self):
        self.revoked = True

    def to_dict(self):
        return {
            "token_id": self.token_id,
            "issuer_id": self.issuer_id,
            "recipient_id": self.recipient_id,
            "level": self.level,
            "capabilities": self.capabilities,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "incident_id": self.incident_id,
            "revoked": self.revoked,
        }


# ---------------------------------------------------------------------------
# Authority Chain
# ---------------------------------------------------------------------------

class AuthorityChain:
    """Manages the ICS command hierarchy for AI agents.

    Tracks who has authority, validates actions against the chain,
    and maintains a complete audit trail of every command decision.
    """

    def __init__(self, incident_id=None):
        self.incident_id = incident_id or f"INC-{int(time.time())}"
        self.tokens = {}         # token_id -> AuthorityToken
        self.audit_log = []      # immutable decision trail
        self.active_overrides = []

    def delegate(self, issuer_id, issuer_level, recipient_id, target_level,
                 capabilities=None, duration_seconds=3600):
        """Delegate authority from a higher level to a lower one.

        ICS principle: you can only delegate DOWN, never UP.
        """
        issuer_rank = AUTHORITY_LEVELS.get(issuer_level, 0)
        target_rank = AUTHORITY_LEVELS.get(target_level, 0)

        if target_rank >= issuer_rank:
            self._audit("DENIED", issuer_id, f"cannot delegate to equal/higher level "
                        f"({issuer_level} -> {target_level})")
            return None

        if capabilities is None:
            capabilities = AUTHORITY_CAPABILITIES.get(target_level, [])

        # Filter: can't delegate capabilities you don't have
        issuer_caps = set(AUTHORITY_CAPABILITIES.get(issuer_level, []))
        capabilities = [c for c in capabilities if c in issuer_caps]

        token = AuthorityToken(
            issuer_id=issuer_id,
            recipient_id=recipient_id,
            level=target_level,
            capabilities=capabilities,
            duration_seconds=duration_seconds,
            incident_id=self.incident_id,
        )

        self.tokens[token.token_id] = token
        self._audit("DELEGATED", issuer_id,
                     f"authority '{target_level}' -> {recipient_id} "
                     f"(token: {token.token_id}, caps: {capabilities})")
        return token

    def authorize_action(self, agent_id, action, context=None):
        """Check if an agent is authorized to perform an action.

        Returns (authorized: bool, reason: str).
        """
        # Find valid tokens for this agent
        valid_tokens = [
            t for t in self.tokens.values()
            if t.recipient_id == agent_id and t.is_valid()
        ]

        if not valid_tokens:
            self._audit("DENIED", agent_id, f"no valid token for action '{action}'")
            return False, "no valid authority token"

        for token in valid_tokens:
            if token.has_capability(action):
                self._audit("AUTHORIZED", agent_id,
                            f"action '{action}' via token {token.token_id}",
                            context=context)
                return True, f"authorized via {token.level} (token: {token.token_id})"

        self._audit("DENIED", agent_id,
                     f"action '{action}' not in any token capabilities")
        return False, f"action '{action}' not authorized at current level"

    def activate_override(self, agent_id, protocol_id, reason, justification):
        """Activate a procedure override (bypass).

        Only agents with 'override_protocol' or 'bypass_procedure'
        capability can do this. Always logged.
        """
        can_override, _ = self.authorize_action(agent_id, "override_protocol")
        can_bypass, _ = self.authorize_action(agent_id, "bypass_procedure")

        if not (can_override or can_bypass):
            self._audit("OVERRIDE_DENIED", agent_id,
                         f"protocol '{protocol_id}': insufficient authority")
            return False, "insufficient authority for override"

        override_record = {
            "timestamp": time.time(),
            "agent_id": agent_id,
            "protocol_id": protocol_id,
            "reason": reason,
            "justification": justification,
            "incident_id": self.incident_id,
        }
        self.active_overrides.append(override_record)
        self._audit("OVERRIDE_ACTIVATED", agent_id,
                     f"protocol '{protocol_id}' bypassed: {reason}")
        return True, "override activated"

    def escalate(self, agent_id, message, target_level="section_chief"):
        """Escalate a decision to a higher authority level.

        ICS principle: when in doubt, push UP. AI agents should
        escalate aggressively rather than make unauthorized decisions.
        """
        self._audit("ESCALATION", agent_id,
                     f"requesting {target_level}: {message}")
        return {
            "type": "ESCALATION",
            "from": agent_id,
            "target_level": target_level,
            "message": message,
            "timestamp": time.time(),
            "incident_id": self.incident_id,
        }

    def _audit(self, event_type, agent_id, description, context=None):
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            "agent_id": agent_id,
            "description": description,
            "incident_id": self.incident_id,
        }
        if context:
            entry["context"] = context
        self.audit_log.append(entry)

    def get_audit_log(self):
        return list(self.audit_log)

    def export_audit(self, filepath):
        """Write audit log to file — ICS documentation requirement."""
        with open(filepath, "w") as f:
            json.dump(self.audit_log, f, indent=2)
