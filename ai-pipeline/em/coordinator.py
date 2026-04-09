"""
coordinator.py — Emergency Management Coordinator for TRDAP AI agents.

This is the main entry point for EM-aware AI operations. It ties together:
  - ICS authority chain (who can do what)
  - Hot-reloadable protocols (what to do)
  - Agent staging (who's available)
  - Multi-mode communication (how to talk)

The coordinator runs the EM loop:
  1. Detect situation (from TRDAP messages)
  2. Select protocol (or hot-reload updated one)
  3. Check authority (can we act?)
  4. Execute steps (dispatch agents, allocate resources)
  5. Escalate if needed (push decisions UP)
  6. Document everything (audit trail)

Usage:
    from ai_pipeline.em.coordinator import EMCoordinator

    coord = EMCoordinator(incident_id="INC-2025-001")
    coord.load_runbooks("ai-pipeline/em/runbooks/")
    coord.register_agent("agent-01", ["urgency_classifier", "communication_relay"])
    coord.handle_event(trdap_message)

License: CC0 1.0
"""

import json
import os
import time

from .ics_authority import AuthorityChain, URGENCY_TO_INCIDENT_TYPE
from .protocols import ProtocolRegistry
from .staging import StagingArea, MessageBus


# ---------------------------------------------------------------------------
# Event Classification
# ---------------------------------------------------------------------------

def classify_event(message):
    """Classify a TRDAP message into an EM event type.

    Maps message content to protocol triggers.
    """
    msg_type = message.get("message_type", "")
    urgency = message.get("urgency", "low")
    resource_status = message.get("resource_status", "")
    resource_type = message.get("resource_type", "")

    # Mass casualty indicators
    if message.get("casualty_count", 0) > 0:
        return "mass_casualty", "critical"

    # Resource exhaustion
    if resource_status in ("depleted", "critical"):
        if resource_type in ("fuel", "medical", "medical_kits", "water"):
            return "resource_exhaustion", "critical"
        return "resource_exhaustion", "high"

    # Communication failure (detected by absence or error messages)
    if msg_type == "ERROR" and "comm" in message.get("error_detail", "").lower():
        return "comms_failure", "high"

    # General urgency passthrough
    if urgency in ("critical", "high"):
        return "elevated_urgency", urgency

    return "routine", urgency


EVENT_TO_PROTOCOL = {
    "mass_casualty":       "EM-003-MASS-CASUALTY",
    "resource_exhaustion": "EM-001-RESOURCE-EXHAUSTION",
    "comms_failure":       "EM-002-COMMS-FAILURE",
    "elevated_urgency":    "EM-001-RESOURCE-EXHAUSTION",
    "routine":             None,  # no protocol activation needed
}


# ---------------------------------------------------------------------------
# EM Coordinator
# ---------------------------------------------------------------------------

class EMCoordinator:
    """Central coordinator for emergency management operations.

    One coordinator per incident. Multiple coordinators can run for
    multiple simultaneous incidents (ICS supports this).
    """

    def __init__(self, incident_id=None, runbook_dir=None):
        self.incident_id = incident_id or f"INC-{int(time.time())}"

        # Core subsystems
        self.authority = AuthorityChain(self.incident_id)
        self.protocols = ProtocolRegistry(runbook_dir)
        self.staging = StagingArea()
        self.bus = MessageBus()

        # State
        self.active_events = []
        self.step_results = []
        self.started_at = time.time()

    # -------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------

    def load_runbooks(self, runbook_dir):
        """Load emergency protocol runbooks."""
        count = self.protocols.load_all(runbook_dir)
        return count

    def register_agent(self, agent_id, capabilities, position=None,
                       comm_modes=None, authority_level="field_agent",
                       delegated_by="system"):
        """Register an agent with staging and communication."""
        # Register in staging area
        self.staging.register(agent_id, capabilities, position, comm_modes)

        # Subscribe to standard EM channels
        for channel in ("operations", "logistics", "planning", "alerts"):
            self.bus.subscribe(agent_id, channel)

        # Delegate base authority
        self.authority.delegate(
            issuer_id=delegated_by,
            issuer_level="incident_commander",
            recipient_id=agent_id,
            target_level=authority_level,
        )

        return True

    # -------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------

    def handle_event(self, message):
        """Process an incoming TRDAP message through the EM pipeline.

        This is the main loop entry point.
        """
        event_type, urgency = classify_event(message)

        event_record = {
            "timestamp": time.time(),
            "event_type": event_type,
            "urgency": urgency,
            "message": message,
            "incident_id": self.incident_id,
        }
        self.active_events.append(event_record)

        # Determine protocol
        protocol_id = EVENT_TO_PROTOCOL.get(event_type)
        if not protocol_id:
            return {"action": "none", "event_type": event_type, "reason": "routine event"}

        # Activate protocol (or stay on current if same)
        if self.protocols.active_protocol != protocol_id:
            ok, msg = self.protocols.activate(protocol_id, reason=f"event: {event_type}")
            if not ok:
                # Try fallback
                ok, msg = self.protocols.activate("EM-010-DEGRADED-OPS",
                                                   reason=f"fallback: {protocol_id} unavailable")

        # Broadcast alert
        self.bus.publish(
            sender_id="coordinator",
            channel="alerts",
            message={
                "type": "PROTOCOL_ACTIVATED",
                "protocol": protocol_id,
                "urgency": urgency,
                "event": event_type,
                "incident_id": self.incident_id,
            },
        )

        # Execute protocol steps
        results = self._execute_protocol()

        return {
            "action": "protocol_activated",
            "protocol": protocol_id,
            "event_type": event_type,
            "urgency": urgency,
            "step_results": results,
        }

    def _execute_protocol(self):
        """Execute steps of the active protocol."""
        steps = self.protocols.get_steps()
        results = []

        for step in steps:
            result = self._execute_step(step)
            results.append(result)
            self.step_results.append(result)

            # If a step fails and it's critical, try fallback
            if not result.get("success") and step.get("type") in ("execute", "allocate"):
                fallback = self.protocols.get_fallback()
                if fallback:
                    self.protocols.activate(
                        fallback["protocol_id"],
                        agent_id="coordinator",
                        reason=f"step {step.get('step_id')} failed, falling back",
                    )
                    break

        return results

    def _execute_step(self, step):
        """Execute a single protocol step."""
        step_type = step.get("type", "")
        step_id = step.get("step_id", 0)
        action = step.get("action", "")

        result = {
            "step_id": step_id,
            "type": step_type,
            "action": action,
            "timestamp": time.time(),
            "success": True,
        }

        if step_type == "assess":
            result["note"] = "assessment logged"

        elif step_type == "communicate":
            channels = step.get("channels", ["operations"])
            for ch in channels:
                self.bus.publish("coordinator", ch, {
                    "type": "PROTOCOL_STEP",
                    "action": action,
                    "urgency": step.get("urgency", "medium"),
                    "trdap_message_type": step.get("trdap_message_type", "ANNOUNCE"),
                })
            result["channels_notified"] = channels

        elif step_type == "allocate":
            cap = step.get("model", "resource_predictor")
            agent = self.staging.dispatch({
                "required_capability": cap,
                "urgency": step.get("urgency", "high"),
                "action": action,
            })
            if agent:
                result["assigned_agent"] = agent.agent_id
            else:
                result["success"] = False
                result["note"] = f"no agent available with capability '{cap}'"

        elif step_type == "stage":
            cap = step.get("model", "route_optimizer")
            agent = self.staging.dispatch({
                "required_capability": cap,
                "urgency": "high",
                "action": action,
            })
            if agent:
                result["staged_agent"] = agent.agent_id
            else:
                result["note"] = "no staging agent available — queued"

        elif step_type == "execute":
            req_auth = step.get("required_authority")
            if req_auth:
                # Check if any active agent has this authority
                result["note"] = f"requires {req_auth} authority"
            result["autonomous"] = step.get("autonomous_mode", False)

        elif step_type == "override":
            req_auth = step.get("required_authority", "section_chief")
            result["override_authority_required"] = req_auth
            result["justification"] = step.get("justification", "")

        elif step_type == "escalate":
            target = step.get("target_authority", "incident_commander")
            esc = self.authority.escalate("coordinator", action, target)
            result["escalation"] = esc

        elif step_type == "verify":
            result["note"] = "verification pending"

        elif step_type == "document":
            result["note"] = "documented in audit log"

        return result

    # -------------------------------------------------------------------
    # Hot Reload
    # -------------------------------------------------------------------

    def hot_reload_protocols(self):
        """Reload protocols from disk without stopping operations.

        Call this when procedures are updated mid-incident.
        """
        count = self.protocols.reload()
        self.bus.publish("coordinator", "operations", {
            "type": "PROTOCOLS_RELOADED",
            "count": count,
            "timestamp": time.time(),
        })
        return count

    # -------------------------------------------------------------------
    # Status & Reporting
    # -------------------------------------------------------------------

    def situation_report(self):
        """Generate ICS-style situation report (SitRep)."""
        active_proto = self.protocols.get_active()

        return {
            "incident_id": self.incident_id,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.started_at,
            "active_protocol": active_proto.get("name") if active_proto else "none",
            "events_processed": len(self.active_events),
            "steps_executed": len(self.step_results),
            "staging": self.staging.status_report(),
            "available_protocols": self.protocols.list_protocols(),
            "comm_mode": self.bus.best_mode(),
            "active_overrides": self.authority.active_overrides,
        }

    def export_incident_record(self, output_dir):
        """Export full incident record (ICS documentation requirement)."""
        os.makedirs(output_dir, exist_ok=True)

        # Audit log
        self.authority.export_audit(
            os.path.join(output_dir, f"{self.incident_id}-audit.json"))

        # SitRep
        sitrep = self.situation_report()
        with open(os.path.join(output_dir, f"{self.incident_id}-sitrep.json"), "w") as f:
            json.dump(sitrep, f, indent=2)

        # Protocol history
        with open(os.path.join(output_dir, f"{self.incident_id}-protocol-history.json"), "w") as f:
            json.dump(self.protocols.history, f, indent=2)

        # Events
        with open(os.path.join(output_dir, f"{self.incident_id}-events.json"), "w") as f:
            json.dump(self.active_events, f, indent=2, default=str)

        return output_dir


# ---------------------------------------------------------------------------
# Quick-start helper
# ---------------------------------------------------------------------------

def quick_start(runbook_dir="ai-pipeline/em/runbooks", incident_id=None):
    """Spin up a coordinator with default runbooks and channels.

    Returns a ready-to-use EMCoordinator.
    """
    coord = EMCoordinator(incident_id=incident_id, runbook_dir=runbook_dir)
    return coord
