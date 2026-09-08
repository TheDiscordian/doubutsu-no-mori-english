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
    required = {"reference_command", "native_command", "offset", "adapted_sha256"}
    if (not isinstance(rule, dict)
            or not required <= set(rule) <= required | {'answer_permutation'}
            or not record["id"].startswith("message:") or "controller" in record
            or type(rule["offset"]) is not int or not 0 <= rule["offset"] < 1024
            or not isinstance(rule["adapted_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", rule["adapted_sha256"])):
        raise ValueError("Invalid native-choice approval")
    before, after = choice_command(rule["reference_command"]), choice_command(rule["native_command"])
    if before == after or before[1] != after[1]:
        raise ValueError("Native-choice approval must retain the number of choices")
    if 'answer_permutation' in rule:
        permutation = rule['answer_permutation']
        count = before[1]-0x14
        if (not isinstance(permutation, list) or len(permutation) != count
                or any(type(n) is not int for n in permutation)
                or sorted(permutation) != list(range(count))
                or permutation == list(range(count))):
            raise ValueError('Native-choice answer permutation must reorder every answer exactly once')


def permuted_routes(source, reference, permutation, native_info, reference_info):
    """Prove each destination's equivalent answer index before restoring it."""
    def routes(data, info):
        result = [t for t in tokenize(data, info) if t.kind == 'cmd' and 0x0F <= t.data[1] <= 0x12]
        if ([t.data[1] for t in result] != list(range(0x0F, 0x0F+len(permutation)))
                or any(b.offset != a.offset+4 for a, b in zip(result, result[1:]))):
            raise ValueError('Answer permutation requires one contiguous ordered branch per answer')
        return result
    native, english = routes(source, native_info), routes(reference, reference_info)
    if any(native[i].data[2:] != english[j].data[2:] for i, j in enumerate(permutation)):
        raise ValueError('Answer permutation changes a native destination or its meaning')
    return [(english[i].offset, native[i].data) for i in range(len(permutation))]


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
    adapted = bytearray(raw[:offset]+after+raw[offset+len(before):])
    changes = [{"operation": "preserve_approved_native_choices",
                                   "byte_offset": offset, "gamecube": before.hex().upper(),
                                   "n64": after.hex().upper()}]
    if 'answer_permutation' in rule:
        routes = permuted_routes(source, raw, rule['answer_permutation'], info, reference_info)
        for at, command in routes:
            adapted[at:at+4] = command
        changes.append({'operation': 'preserve_approved_native_answer_indices',
                        'native_to_reference': rule['answer_permutation'],
                        'routes': [{'offset': at, 'native': cmd.hex().upper()} for at, cmd in routes]})
    return decode(bytes(adapted), reference_info), changes


def validate_choice_candidate(id, source, candidate, matches):
    record = matches.get(id)
    if record and "native_choices" in record:
        validate_choice_approval(record)
        if (sha256(source) != record["source_sha256"]
                or sha256(candidate) != record["native_choices"]["adapted_sha256"]):
            raise ValueError("Native-choice candidate differs from its complete approval")
