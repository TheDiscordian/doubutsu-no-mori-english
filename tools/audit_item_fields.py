#!/usr/bin/env python3
"""Record item-field setter, getter, insertion, and wrapper references."""

import argparse
import json
from pathlib import Path
import struct

from aflib import dma_entries, sha256, verified_rom
from audit_string_callers import audit

TARGETS = {"set_item": 0x8009D88C, "get_item": 0x8009DA1C, "copy_item": 0x8009F5B4,
           "quest_item": 0x800BB6A0}


def field_audit(rom):
    reports = {name: audit(rom, address, allow_empty=True) for name, address in TARGETS.items()}
    for report in reports.values():
        report.pop("capacity_counts")
        report["literal_pointers"] = []
        for row in report["callers"]:
            row.pop("destination_length")
            row.pop("string_id")
    for entry in dma_entries(rom):
        if entry.pstart == 0xFFFFFFFF:
            continue
        data = entry.extract(rom)
        for offset in range(0, len(data)-3, 4):
            value = struct.unpack_from(">I", data, offset)[0]
            for name, address in TARGETS.items():
                if value == address:
                    reports[name]["literal_pointers"].append({"vrom": f"{entry.vstart:08X}",
                        "offset": f"{offset:06X}", "file_sha256": sha256(data)})
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/item-fields.json"))
    args = parser.parse_args()
    report = field_audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({name: {"direct_calls": len(r["callers"]), "literal_pointers": len(r["literal_pointers"])}
                      for name, r in report.items()}))


if __name__ == "__main__":
    main()
