#!/usr/bin/env python3
"""Inventory native name-loader calls before changing any destination width."""

import argparse
import json
from pathlib import Path

from aflib import verified_rom
from audit_string_callers import audit

TARGETS = {"item_name": 0x80096740, "villager_name": 0x800ACC38}


def name_audit(rom):
    report = {}
    for name, address in TARGETS.items():
        result = audit(rom, address)
        result.pop("capacity_counts")
        for row in result["callers"]:
            row["name_id_argument"] = row.pop("destination_length")
            row.pop("string_id")
        result["native_write_bytes"] = 10 if name == "item_name" else 6
        result["status"] = "Direct-call evidence only; destination lifetimes, indirect uses, readers, and display require review"
        report[name] = result
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/name-callers.json"))
    args = parser.parse_args()
    report = name_audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({name: {"callers": len(result["callers"]), "native_write_bytes": result["native_write_bytes"]}
                      for name, result in report.items()}))


if __name__ == "__main__":
    main()
