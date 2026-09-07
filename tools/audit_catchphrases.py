#!/usr/bin/env python3
"""Inventory catchphrase references without widening shared or saved consumers."""

import argparse
import json
from pathlib import Path

from aflib import verified_rom
from audit_display_names import audit as reference_audit

TARGETS = {"copy_tail": 0x8009EDBC, "get_ending": 0x800A9E7C,
           "set_ending": 0x800A9E54, "reset_ending": 0x800A9EC8}


def audit(rom):
    result = reference_audit(rom, TARGETS, allow_empty=True)
    for report in result.values():
        report["status"] = "Only main-message call 800A114C is widened; shared getter, setter, resetter, and other callers remain native"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/catchphrases.json"))
    args = parser.parse_args()
    report = audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({name: {"calls": [r["call_ram"] for r in rows["callers"]],
                             "literal_pointers": rows["literal_pointers"]}
                      for name, rows in report.items()}, indent=2))


if __name__ == "__main__":
    main()
