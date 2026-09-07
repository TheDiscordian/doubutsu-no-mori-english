#!/usr/bin/env python3
"""Record all direct and literal references for the display-name consumer audit."""

import argparse
import json
from pathlib import Path
import struct

from aflib import dma_entries, sha256, verified_rom
from audit_string_callers import audit as audit_calls

TARGETS = {"world_name": 0x800ACDF8, "talk_name": 0x8009ED14,
           "nameplate_setup": 0x8009D308, "nameplate_draw": 0x800A2BB0}


def audit(rom):
    reports = {name: audit_calls(rom, target) for name, target in TARGETS.items()}
    for report in reports.values():
        report.pop("capacity_counts")
        report["literal_pointers"] = []
        report["status"] = "Native references; only separately guarded main-message/nameplate call sites are widened"
        for row in report["callers"]:
            row.pop("destination_length")
            row.pop("string_id")
    for entry in dma_entries(rom):
        if entry.pstart == 0xFFFFFFFF:
            continue
        data = entry.extract(rom)
        for offset in range(0, len(data)-3, 4):
            value = struct.unpack_from(">I", data, offset)[0]
            for name, target in TARGETS.items():
                if value == target:
                    reports[name]["literal_pointers"].append({"vrom": f"{entry.vstart:08X}",
                        "offset": f"{offset:06X}", "file_sha256": sha256(data)})
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/display-names.json"))
    args = parser.parse_args()
    report = audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({name: {"calls": len(r["callers"]), "literal_pointers": len(r["literal_pointers"])}
                      for name, r in report.items()}))


if __name__ == "__main__":
    main()
