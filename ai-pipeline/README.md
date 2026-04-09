# TRDAP AI Pipeline

Secure AI training and inference pipeline for TRDAP emergency mesh networks.

## Components

| Module | Purpose |
|--------|---------|
| `pipeline.py` | Core pipeline: data loading, preprocessing, training, inference |
| `config/pipeline.yaml` | Pipeline configuration (paths, hyperparams, security) |
| `scripts/validate_data.py` | Input validation and sanitization |
| `training/` | Data, models, checkpoints, and training logs |

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
python ai-pipeline/pipeline.py infer --model ai-pipeline/training/models/latest.pt --input sample.json
```

## Security

- All inputs validated and sanitized before processing
- Model files integrity-checked via SHA-256 before loading
- No `pickle.load()` on untrusted data — uses SafeTensors format
- Training data schema-validated against TRDAP message spec
- Sandboxed inference with resource limits

## Fieldlinks

- [Infrastructure-assistance](https://github.com/JinnZ2/Infrastructure-assistance) — Infrastructure modeling that feeds training data
- [Nexus-emergency-management](https://github.com/JinnZ2/Nexus-emergency-management) — Emergency management integration for real-time inference
