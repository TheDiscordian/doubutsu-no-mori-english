#!/usr/bin/env python3
"""Measure persistent template snapshots against actual local English mail banks."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from mail_record import FIELD_BYTES, RECORD_BYTES, snapshot_size
from mail_controls import NATIVE_CODES
from textbanks import Bank

CLASSIC = ("super", "mail", "ps")
COMPOSITE = ("superz", "maila", "mailb", "mailc", "psz")
REPLY_CODE_SHA256 = "97919d8a755e399b85a058203f2b48bbac5efbfdd2ba6f3dff17f24b4784bdc3"


def template_fields(data):
    """Mail commands are two-byte tokens; other GC bytes are single glyphs."""
    fields, pos = set(), 0
    while pos < len(data):
        if data[pos] != 0x7F:
            pos += 1
            continue
        if pos+1 >= len(data):
            raise ValueError("Truncated reference mail command")
        opcode = data[pos+1]
        if opcode in NATIVE_CODES:
            fields.add(opcode-0x24 if opcode <= 0x2D else opcode-0x36+10)
        elif opcode not in (0x74, 0x75):
            raise ValueError("Unknown reference mail command")
        pos += 2
    return frozenset(fields)


def reachable_fields(parts):
    """Exact unions of independently selected parts, with one witness per union.

    Deduplicating field sets avoids enumerating every wording combination while
    preserving every possible union. Witnesses retain the original part IDs.
    """
    states = {frozenset(): ()}
    for entries in parts:
        if not entries:
            raise ValueError("Empty mail component range")
        unique = {}
        for index, fields in entries:
            unique.setdefault(fields, index)
        following = {}
        for used, witness in states.items():
            for fields, index in unique.items():
                following.setdefault(used | fields, witness+(index,))
        states = following
    return states


def reply_groups(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    function = code[0x800A8DB4-CODE_RAM:0x800A8F30-CODE_RAM]
    if sha256(function) != REPLY_CODE_SHA256:
        raise ValueError("Unexpected native composite reply selection code")
    pointers = struct.unpack_from(">2I", code, 0x8010B880-CODE_RAM)
    if pointers != (0x8010B850, 0x8010B868):
        raise ValueError("Unexpected native composite reply tables")
    groups = tuple(struct.unpack_from(">6I", code, pointer-CODE_RAM) for pointer in pointers)
    if groups != ((32, 64, 0, 96, 128, 160), (224, 256, 192, 288, 320, 352)):
        raise ValueError("Unexpected native composite reply group starts")
    return groups


def audit(rom, directory):
    groups = reply_groups(rom)
    masks, hashes = {}, {}
    for name in CLASSIC+COMPOSITE:
        data_path = directory/(name+"_data.bin")
        table_path = directory/(name+"_data_table.bin")
        data, table = data_path.read_bytes(), table_path.read_bytes()
        entries = Bank(name, 0, 0, data, table).entries()
        expected = 982 if name in CLASSIC else 384
        if len(entries) != expected:
            raise ValueError("Unexpected English mail bank record count")
        masks[name] = [template_fields(entry) for entry in entries]
        hashes[name] = {"data_sha256": sha256(data), "table_sha256": sha256(table), "entries": len(entries)}
    classic = []
    for index in range(982):
        fields = frozenset().union(*(masks[name][index] for name in CLASSIC))
        size = snapshot_size(0, [FIELD_BYTES]*len(fields))
        classic.append({"id": index, "fields": sorted(fields), "max_snapshot_bytes": size,
                        "fits_at_max_field_width": size <= RECORD_BYTES,
                        "has_native_numeric_id": index < 544})
    composite = []
    for foreign, starts in enumerate(groups):
        for looks, start in enumerate(starts):
            states = reachable_fields([list(enumerate(masks[name][start:start+32], start)) for name in COMPOSITE])
            fields, witness = max(states.items(), key=lambda pair: (len(pair[0]), tuple(sorted(pair[0]))))
            size = snapshot_size(1, [FIELD_BYTES]*len(fields))
            composite.append({"foreign": foreign, "looks": looks, "start": start,
                "distinct_field_unions": len(states), "max_fields": len(fields),
                "max_snapshot_bytes": size, "fits_at_max_field_width": size <= RECORD_BYTES,
                "witness_templates": list(witness), "witness_fields": sorted(fields)})
    return {"source_sha256": sha256(rom), "reply_selection_sha256": REPLY_CODE_SHA256,
            "reference_banks": hashes, "record_capacity": RECORD_BYTES, "field_capacity": FIELD_BYTES,
            "classic": classic, "composite": composite,
            "summary": {"classic_records": len(classic),
                "classic_fit_at_max_field_width": sum(r["fits_at_max_field_width"] for r in classic),
                "native_numeric_records_fit_at_max_field_width": sum(r["has_native_numeric_id"] and r["fits_at_max_field_width"] for r in classic),
                "classic_require_actual_field_bounds": [r["id"] for r in classic if not r["fits_at_max_field_width"]],
                "composite_groups": len(composite),
                "all_composite_groups_fit": all(r["fits_at_max_field_width"] for r in composite),
                "max_composite_snapshot_bytes": max(r["max_snapshot_bytes"] for r in composite)},
            "status": "Storage feasibility only; no semantic matches, runtime readers, editor, or save integration approved"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-data", type=Path, default=Path("build/gamecube/files/forest_1st.arc.unpacked/data"))
    parser.add_argument("--output", type=Path, default=Path("build/audits/mail-templates.json"))
    args = parser.parse_args()
    report = audit(verified_rom(args.rom.read_bytes()), args.gc_data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
