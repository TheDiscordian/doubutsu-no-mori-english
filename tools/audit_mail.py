#!/usr/bin/env python3
"""Inventory native mail capacities, executable references, and local text sizes."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from audit_display_names import audit as reference_audit
from textbanks import banks
from mail_controls import TABLE_RAM, TABLE_SHA256, native_handlers
from mail_viewer import evidence as viewer_evidence

TARGETS = {"load_letter": 0x80093F04, "load_letter_sized_edges": 0x80093F54,
           "load_header": 0x80093B28, "load_footer": 0x80093C98, "load_body": 0x80093DA8,
           "set_free_string": 0x80092D10, "load_composite_letter": 0x800944B8,
           "set_message_mail": 0x8009DA94, "clear_mail": 0x8009C384, "copy_mail": 0x8009C67C}
CAPACITY_GUARDS = {0x80093F1C: 0x2405000A, 0x80093F2C: 0x24050010,
                   0x80093E5C: 0x24060060, 0x80093EC4: 0x28810060,
                   0x8009C398: 0x240500A4, 0x8009C3A8: 0x2405007A,
                   0x8009C3B4: 0x2484002A, 0x8009C688: 0x240600A4}
MAIL_BANKS = {"super": 10, "mail": 96, "ps": 16,
              "superz": None, "maila": None, "mailb": None, "mailc": None, "psz": None}


def capacity_evidence(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    for address, expected in CAPACITY_GUARDS.items():
        if struct.unpack_from(">I", code, address-CODE_RAM)[0] != expected:
            raise ValueError("Native mail capacity instruction guard failed")
    return {"source_code_sha256": sha256(code), "record_bytes": 164,
            "text_start": 42, "header_bytes": 10, "body_bytes": 96, "footer_bytes": 16,
            "body_offset": 52, "footer_offset": 148,
            "instruction_guards": {f"{address:08X}": f"{word:08X}" for address, word in CAPACITY_GUARDS.items()}}


def text_sizes(rom, reference_directory):
    result = {}
    for bank in banks(rom):
        if bank.name not in MAIL_BANKS:
            continue
        entries = bank.entries()
        refs = list(map(json.loads, (reference_directory/(bank.name+".jsonl")).read_text().splitlines()))
        if len({r["id"] for r in refs}) != len(refs):
            raise ValueError("Duplicate mail reference ID")
        if any(type(r["bytes"]) is not int or r["bytes"] < 0 for r in refs):
            raise ValueError("Invalid mail reference byte count")
        if any(not r["id"].startswith(bank.name+":") for r in refs):
            raise ValueError("Wrong reference bank in mail size inventory")
        same_id = [r for r in refs if 0 <= int(r["id"].split(":")[1], 16) < len(entries)]
        limit = MAIL_BANKS[bank.name]
        result[bank.name] = {"native_records": len(entries), "native_data_sha256": sha256(bank.data),
            "reference_records": len(refs), "native_max_stored_bytes": max(map(len, entries)),
            "reference_max_raw_bytes": max(r["bytes"] for r in refs), "native_destination_bytes": limit,
            "reference_raw_records_exceeding_destination": sum(r["bytes"] > limit for r in refs) if limit else None,
            "reference_records_with_native_numeric_id": len(same_id),
            "same_numeric_id_raw_records_exceeding_destination": sum(r["bytes"] > limit for r in same_id) if limit else None,
            "status": "Encoded source sizes only; dynamic expansion, identity matching, assembly, and destination consumers remain unapproved"}
    return result


def audit(rom, reference_directory):
    result = {"source_sha256": sha256(rom), "layout": capacity_evidence(rom),
              "banks": text_sizes(rom, reference_directory), "references": reference_audit(rom, TARGETS, allow_empty=True)}
    result["controls"] = {"table_ram": f"{TABLE_RAM:08X}", "table_sha256": TABLE_SHA256,
                          "handlers": {f"{opcode:02X}": f"{address:08X}" for opcode, address in native_handlers(rom).items()},
                          "unsupported_code_behaviour": "No replacement and no cursor advance; the native assembly loop can stall"}
    result["viewer"] = viewer_evidence(rom)
    for report in result["references"].values():
        report["status"] = "Native mail references; no destination or save expansion is approved by this inventory"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--output", type=Path, default=Path("build/audits/mail.json"))
    args = parser.parse_args()
    report = audit(verified_rom(args.rom.read_bytes()), args.gc_text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"layout": report["layout"], "banks": report["banks"],
        "controls": report["controls"], "viewer": report["viewer"],
        "calls": {name: len(r["callers"]) for name, r in report["references"].items()},
        "literal_pointers": {name: len(r["literal_pointers"]) for name, r in report["references"].items()}}, indent=2))


if __name__ == "__main__":
    main()
