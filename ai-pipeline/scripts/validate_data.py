"""
validate_data.py — Input validation and sanitization for TRDAP AI pipeline.

Validates training data against TRDAP message schema before it enters
the pipeline. Rejects malformed, oversized, or suspicious inputs.

Usage:
    python validate_data.py --data-dir ai-pipeline/training/data/
"""

import argparse
import json
import os
import sys

# ---------------------------------------------------------------------------
# TRDAP schema constraints
# ---------------------------------------------------------------------------

MAX_MESSAGE_BYTES = 512
REQUIRED_FIELDS = {"message_id", "hub_id", "message_type"}
VALID_MESSAGE_TYPES = {"QUERY", "RESPONSE", "ANNOUNCE", "PING", "SYNC", "REDIRECT", "ERROR"}
VALID_URGENCY = {"critical", "high", "medium", "low"}
VALID_RESOURCE_TYPES = {
    "fuel", "fuel_jet_a", "fuel_diesel", "fuel_gasoline",
    "medical", "medical_kits", "medical_personnel",
    "transport", "transport_bus", "transport_rail",
    "shelter", "food", "water", "personnel",
}
ALLOWED_EXTENSIONS = {".json", ".csv"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_file_safety(filepath):
    """Check file size and extension before reading."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"disallowed extension: {ext}"

    size = os.path.getsize(filepath)
    if size > MAX_FILE_SIZE:
        return False, f"file too large: {size} bytes (max {MAX_FILE_SIZE})"

    return True, "ok"


def validate_message(msg, index=0):
    """Validate a single TRDAP message dict."""
    errors = []

    raw = json.dumps(msg)
    if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
        errors.append(f"message[{index}]: exceeds {MAX_MESSAGE_BYTES} byte limit")

    missing = REQUIRED_FIELDS - set(msg.keys())
    if missing:
        errors.append(f"message[{index}]: missing fields: {missing}")

    msg_type = msg.get("message_type")
    if msg_type and msg_type not in VALID_MESSAGE_TYPES:
        errors.append(f"message[{index}]: invalid message_type: {msg_type}")

    urgency = msg.get("urgency")
    if urgency and urgency not in VALID_URGENCY:
        errors.append(f"message[{index}]: invalid urgency: {urgency}")

    resource = msg.get("resource_type")
    if resource and resource not in VALID_RESOURCE_TYPES:
        errors.append(f"message[{index}]: unknown resource_type: {resource}")

    hub_id = msg.get("hub_id", "")
    if hub_id and not all(c in "0123456789abcdef-" for c in hub_id):
        errors.append(f"message[{index}]: hub_id contains invalid characters")

    return errors


def validate_json_file(filepath):
    """Validate a JSON file containing TRDAP messages."""
    safe, reason = validate_file_safety(filepath)
    if not safe:
        return [reason]

    errors = []
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return [f"parse error: {e}"]

    if isinstance(data, list):
        for i, msg in enumerate(data):
            errors.extend(validate_message(msg, i))
    elif isinstance(data, dict):
        errors.extend(validate_message(data, 0))
    else:
        errors.append("expected JSON object or array")

    return errors


def validate_directory(data_dir):
    """Validate all data files in a directory."""
    if not os.path.isdir(data_dir):
        print(f"ERROR: {data_dir} is not a directory")
        return False

    total_files = 0
    total_errors = 0

    for root, _dirs, files in os.walk(data_dir):
        for fname in sorted(files):
            filepath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()

            if ext not in ALLOWED_EXTENSIONS:
                continue

            total_files += 1
            errors = validate_json_file(filepath)

            if errors:
                total_errors += len(errors)
                print(f"FAIL {filepath}")
                for e in errors:
                    print(f"  - {e}")
            else:
                print(f"  OK {filepath}")

    print(f"\n--- {total_files} files scanned, {total_errors} errors ---")
    return total_errors == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate TRDAP training data")
    parser.add_argument("--data-dir", required=True, help="Path to data directory")
    args = parser.parse_args()

    ok = validate_directory(args.data_dir)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
