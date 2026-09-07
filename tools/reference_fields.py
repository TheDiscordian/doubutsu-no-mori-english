"""Hash-bound permissions for reviewed current-player and current-town insertions."""

from dataclasses import dataclass
import re

from aflib import sha256
from textcodec import encode


@dataclass(frozen=True)
class ReferenceFieldPermit:
    source_sha256: str
    encoded_sha256: str
    fields: frozenset


def validate_field_approval(record):
    if "available_fields" not in record:
        return
    rule = record["available_fields"]
    if (not isinstance(rule, dict) or set(rule) != {"commands", "adapted_sha256"}
            or not record["id"].startswith("message:")
            or any(key in record for key in ("controller", "native_choices", "native_actor_request"))
            or not isinstance(rule["commands"], list) or not rule["commands"]
            or any(type(c) is not str or c not in ("1A", "2F") for c in rule["commands"])
            or rule["commands"] != sorted(set(rule["commands"]))
            or not isinstance(rule["adapted_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", rule["adapted_sha256"])):
        raise ValueError("Invalid reviewed player/town-field approval")


def verify_field_reference(reference, source, record, info):
    if not record or "available_fields" not in record:
        return
    validate_field_approval(record)
    # CUTARTICLE remains part of the complete reference hash. Only the existing
    # adapter removes supported redundant prefixes before native encoding.
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    raw = encode(reference["text"], reference_info)
    if (sha256(source) != record["source_sha256"] or reference["id"] != record["reference_id"]
            or reference["sha256"] != record["reference_sha256"]
            or sha256(raw) != record["reference_sha256"]):
        raise ValueError("Stale reviewed player/town-field source or reference")


def field_permit(id, source, candidate, matches):
    record = matches.get(id)
    if not record or "available_fields" not in record:
        return None
    validate_field_approval(record)
    rule = record["available_fields"]
    if (sha256(source) != record["source_sha256"] or sha256(candidate) != rule["adapted_sha256"]):
        raise ValueError("Reviewed field candidate differs from its complete approval")
    return ReferenceFieldPermit(record["source_sha256"], rule["adapted_sha256"],
                                frozenset(int(c, 16) for c in rule["commands"]))
