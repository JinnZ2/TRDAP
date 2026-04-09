# TRDAP AI Pipeline

Secure AI training, inference, and ICS-aligned emergency management for TRDAP mesh networks.

## Components

| Module | Purpose |
|--------|---------|
| `pipeline.py` | Core pipeline: data loading, preprocessing, training, inference |
| `config/pipeline.yaml` | Pipeline configuration (paths, hyperparams, security, EM settings) |
| `scripts/validate_data.py` | Input validation and sanitization |
| `training/` | Data, models, checkpoints, and training logs |
| `em/` | Emergency management: ICS authority, protocols, staging, coordination |

## Emergency Management (`em/`)

ICS/NIMS-aligned AI coordination built on FEMA best practices:

| Module | Purpose |
|--------|---------|
| `em/coordinator.py` | Main EM loop: detect, classify, activate protocol, dispatch, escalate |
| `em/ics_authority.py` | ICS authority chain: delegation, override authorization, audit trail |
| `em/protocols.py` | Hot-reloadable protocol registry — update procedures without restart |
| `em/staging.py` | Agent staging areas + multi-mode message bus (TCP > UDP > LoRa > Morse) |
| `em/runbooks/` | JSON protocol definitions (drop new files to add procedures) |

### Runbooks

| Runbook | Urgency | Trigger |
|---------|---------|---------|
| `resource-exhaustion.json` | critical | Hub resource status = depleted |
| `comms-failure.json` | high | Primary comm channels lost |
| `mass-casualty.json` | critical | Casualties exceed local capacity |
| `degraded-ops.json` | medium | Fallback when other protocols fail |

### ICS Authority Levels

```
Incident Commander (100) — full authority, can override anything
  Section Chief (80)     — override protocols, authorize resources
    Branch Director (60) — authorize resources, reassign units
      Division Sup (40)  — reassign units, request resources
        Unit Leader (20) — request resources, escalate
          Field Agent (10) — report status, escalate
```

AI agents receive time-limited authority tokens from human commanders. Tokens expire — no permanent AI autonomy. Every decision is audited.

### Override / Bypass

When lives are at stake, standard procedures can be bypassed:
1. Agent requests override with justification
2. Authority chain validates (section_chief+ required)
3. Override activated and logged
4. Full audit trail preserved for after-action review

### Communication Degradation

Agents automatically fall back through available modes:
```
TCP direct → UDP multicast → TRDAP mesh (512B) → Morse beacon (64B)
```
Messages auto-truncate to fit constrained channels. In degraded mode, agents cache decisions locally and SYNC when connectivity restores.

## Models

- **Resource Predictor** — Forecasts hub resource needs from historical TRDAP messages
- **Urgency Classifier** — Classifies emergency urgency from QUERY/ANNOUNCE messages
- **Route Optimizer** — Seed-space gradient routing optimization

## Usage

```bash
# Setup environment
./setup-ai-pipeline.sh

# Validate training data
python ai-pipeline/scripts/validate_data.py --data-dir ai-pipeline/training/data/

# Train a model
python ai-pipeline/pipeline.py train --config ai-pipeline/config/pipeline.yaml

# Run inference
python ai-pipeline/pipeline.py infer --model ai-pipeline/training/models/latest.json --input sample.json
```

### EM Quick Start (Python)

```python
from ai_pipeline.em.coordinator import EMCoordinator

coord = EMCoordinator(runbook_dir="ai-pipeline/em/runbooks")
coord.register_agent("agent-01", ["urgency_classifier", "communication_relay"])
coord.register_agent("agent-02", ["resource_predictor", "route_optimizer"])

# Handle incoming TRDAP message
result = coord.handle_event({
    "message_type": "ANNOUNCE",
    "resource_type": "medical",
    "resource_status": "depleted",
    "urgency": "critical",
})

# Hot-reload protocols mid-incident
coord.hot_reload_protocols()

# Generate situation report
sitrep = coord.situation_report()
```

## Security

- All inputs validated and sanitized before processing
- Model files integrity-checked via SHA-256 before loading
- No `pickle.load()` on untrusted data — JSON model serialization only
- Training data schema-validated against TRDAP message spec
- Time-bounded inference (30s max)
- Authority tokens expire — no permanent AI autonomy
- Every command decision audited with full chain of custody

## Fieldlinks

- [Infrastructure-assistance](https://github.com/JinnZ2/Infrastructure-assistance) — Infrastructure modeling that feeds training data
- [Nexus-emergency-management](https://github.com/JinnZ2/Nexus-emergency-management) — Emergency management integration for real-time inference
- [Seed-physics](https://github.com/JinnZ2/Seed-physics) — Seed protocol physics constraints
