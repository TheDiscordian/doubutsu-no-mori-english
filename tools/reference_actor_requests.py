"""Exact approvals retaining native NPC0 requests in GameCube quest dialogue."""

import re

from aflib import sha256
from textcodec import decode, encode, tokenize


def validate_actor_request_approval(record):
    if "native_actor_request" not in record:
        return
    rule = record["native_actor_request"]
    if (not isinstance(rule, dict)
            or set(rule) != {"reference_command", "native_command", "offset", "adapted_sha256"}
            or not record["id"].startswith("message:")
            or "controller" in record or "native_choices" in record
            or type(rule["offset"]) is not int or not 0 <= rule["offset"] < 1024):
        raise ValueError("Invalid native actor-request approval")
    for key, pattern in (("reference_command", r"7F0C05[0-9A-F]{4}"),
                         ("native_command", r"7F0905[0-9A-F]{4}"),
                         ("adapted_sha256", r"[0-9a-f]{64}")):
        if not isinstance(rule[key], str) or not re.fullmatch(pattern, rule[key]):
            raise ValueError("Actor-request approval is limited to quest/NPC0 order slot five")


def adapt_actor_request_reference(reference, source, record, info):
    if not record or "native_actor_request" not in record:
        return reference["text"], []
    validate_actor_request_approval(record)
    raw = encode(reference["text"], info)
    if (sha256(source) != record["source_sha256"] or reference["id"] != record["reference_id"]
            or reference["sha256"] != record["reference_sha256"]
            or sha256(raw) != record["reference_sha256"]):
        raise ValueError("Stale native actor-request source or reference")
    rule = record["native_actor_request"]
    before, after = bytes.fromhex(rule["reference_command"]), bytes.fromhex(rule["native_command"])
    def actors(data):
        return [t for t in tokenize(data, info) if t.kind == "cmd" and 8 <= t.data[1] <= 12]
    native, english = actors(source), actors(raw)
    targets = [t for t in english if t.data == before]
    if (len(targets) != 1 or targets[0].offset != rule["offset"]
            or sum(t.data == after for t in native) != 1):
        raise ValueError("Native actor-request span is not uniquely present at its approved offset")
    offset = rule["offset"]
    adapted = raw[:offset]+after+raw[offset+5:]
    if [t.data for t in actors(adapted)] != [t.data for t in native]:
        raise ValueError("Actor-request adaptation must retain the complete native actor command sequence")
    return decode(adapted, info), [{"operation": "preserve_approved_native_npc0_request",
                                   "byte_offset": offset, "gamecube": rule["reference_command"],
                                   "n64": rule["native_command"]}]


def validate_actor_request_candidate(id, source, candidate, matches):
    record = matches.get(id)
    if record and "native_actor_request" in record:
        validate_actor_request_approval(record)
        if (sha256(source) != record["source_sha256"]
                or sha256(candidate) != record["native_actor_request"]["adapted_sha256"]):
            raise ValueError("Native actor-request candidate differs from its complete approval")
