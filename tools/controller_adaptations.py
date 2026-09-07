"""Individually approved controller wording without reference reflow."""

import re

from aflib import sha256
from textcodec import decode, encode

OPERATION = "inventory_y_to_start"
BEFORE = bytes.fromhex("7F505F7D9B08")+b"Y Button"
AFTER = bytes.fromhex("7F505F7D9B0C")+b"START Button"


def validate_approval(record):
    if "controller" not in record:
        return
    rule = record["controller"]
    if (not isinstance(rule, dict) or set(rule) != {"operation", "offset", "adapted_sha256"}
            or rule["operation"] != OPERATION or not record["id"].startswith("message:")
            or type(rule["offset"]) is not int or not 0 <= rule["offset"] < 1024
            or not isinstance(rule["adapted_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", rule["adapted_sha256"])):
        raise ValueError("Invalid controller-text approval")


def adapt_controller_reference(reference, source, record, info):
    if not record or "controller" not in record:
        return reference["text"], []
    validate_approval(record)
    raw = encode(reference["text"], info)
    if (sha256(source) != record["source_sha256"] or reference["id"] != record["reference_id"]
            or reference["sha256"] != record["reference_sha256"]
            or sha256(raw) != record["reference_sha256"]):
        raise ValueError("Stale controller-text reference")
    offset = record["controller"]["offset"]
    if raw[offset:offset+len(BEFORE)] != BEFORE:
        raise ValueError("Controller-text span does not match its approval")
    result = raw[:offset]+AFTER+raw[offset+len(BEFORE):]
    return decode(result, info), [{"operation": OPERATION, "byte_offset": offset,
                                  "before_sha256": sha256(BEFORE), "after_sha256": sha256(AFTER)}]


def validate_controller_candidate(id, source, candidate, matches):
    record = matches.get(id)
    if record and "controller" in record:
        validate_approval(record)
        if (sha256(source) != record["source_sha256"]
                or sha256(candidate) != record["controller"]["adapted_sha256"]):
            raise ValueError("Controller-text candidate differs from its complete approval")
