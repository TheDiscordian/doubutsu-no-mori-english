"""Retain individually approved native menu IDs and selection order in English text."""

import re

from aflib import sha256
from textcodec import decode, encode, tokenize


def choice_command(value):
    if not isinstance(value, str) or not re.fullmatch(r"7F(?:16|17|18)[0-9A-F]+", value):
        raise ValueError("Invalid approved choice command")
    data = bytes.fromhex(value)
    if len(data) != 2+2*(data[1]-0x14):
        raise ValueError("Invalid approved choice command length")
    return data


def validate_choice_approval(record):
    if "native_choices" not in record:
        return
    rule = record["native_choices"]
    if (not isinstance(rule, dict)
            or set(rule) != {"reference_command", "native_command", "offset", "adapted_sha256"}
            or not record["id"].startswith("message:") or "controller" in record
            or type(rule["offset"]) is not int or not 0 <= rule["offset"] < 1024
            or not isinstance(rule["adapted_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", rule["adapted_sha256"])):
        raise ValueError("Invalid native-choice approval")
    before, after = choice_command(rule["reference_command"]), choice_command(rule["native_command"])
    if before == after or before[1] != after[1]:
        raise ValueError("Native-choice approval must retain the number of choices")


def adapt_choice_reference(reference, source, record, info):
    if not record or "native_choices" not in record:
        return reference["text"], []
    validate_choice_approval(record)
    # CUTARTICLE belongs to the untouched English reference, not to the native
    # command table. The ordinary adapter removes it only at an audited string
    # insertion after this exact menu edit; do not enable it at runtime here.
    reference_info = list(info)+[(0, 0)]*max(0, 0x75-len(info))
    reference_info[0x74] = (2, 0)
    raw = encode(reference["text"], reference_info)
    if (sha256(source) != record["source_sha256"] or reference["id"] != record["reference_id"]
            or reference["sha256"] != record["reference_sha256"]
            or sha256(raw) != record["reference_sha256"]):
        raise ValueError("Stale native-choice source or reference")
    rule = record["native_choices"]
    before, after = choice_command(rule["reference_command"]), choice_command(rule["native_command"])
    def choices(data, descriptors):
        return [t for t in tokenize(data, descriptors) if t.kind == "cmd" and 0x16 <= t.data[1] <= 0x18]
    native, english = choices(source, info), choices(raw, reference_info)
    if (len(native) != 1 or native[0].data != after or len(english) != 1
            or english[0].data != before or english[0].offset != rule["offset"]):
        raise ValueError("Approved choice span differs from the unique native/reference menu")
    offset = rule["offset"]
    adapted = raw[:offset]+after+raw[offset+len(before):]
    return decode(adapted, reference_info), [{"operation": "preserve_approved_native_choices",
                                   "byte_offset": offset, "gamecube": before.hex().upper(),
                                   "n64": after.hex().upper()}]


def validate_choice_candidate(id, source, candidate, matches):
    record = matches.get(id)
    if record and "native_choices" in record:
        validate_choice_approval(record)
        if (sha256(source) != record["source_sha256"]
                or sha256(candidate) != record["native_choices"]["adapted_sha256"]):
            raise ValueError("Native-choice candidate differs from its complete approval")
