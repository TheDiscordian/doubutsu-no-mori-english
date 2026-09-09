#!/usr/bin/env python3
"""Build a separately gated sixteen-byte item-name resource from local inputs."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from item_candidates import item_candidates
from item_matches import load_matches, validate_candidate, reference_rows
from native_item_names import load_names as load_native_names
from item_aliases import confirmed_aliases, update_alias_reports
from textbanks import banks
from textcodec import LATIN, command_info, encode, tokenize

VROM = 0x02A00000
WIDTH = 16
COUNTS = (64, 4, 36, 32, 255, 30, 64, 64, 7, 10, 55, 1, 96, 32, 2, 4, 3788)
HEADER = struct.pack(">8I", 0x4146494E, 1, WIDTH, sum(COUNTS), 0, 0, 0, 0)


def resource(rom, edits):
    selected = [b for b in banks(rom) if b.name.startswith("item_")]
    if [b.name for b in selected] != [f"item_{g:02X}" for g in [*range(0x20, 0x30), 0x10]]:
        raise ValueError("Unexpected extended item-bank order")
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    matches = load_matches()
    originals = load_native_names()
    source_banks = {bank.name: bank.entries() for bank in selected}
    grouped = {}
    for edit in edits:
        validate_candidate(edit, source_banks, info, matches, originals=originals)
        if edit["id"] in grouped:
            raise ValueError("Duplicate extended item-name ID")
        grouped[edit["id"]] = edit
    output = bytearray(HEADER)
    for bank, count in zip(selected, COUNTS):
        entries = bank.entries()
        if len(entries) != count+(bank.name == "item_10"):
            raise ValueError("Unexpected extended item-name count")
        for index, native in enumerate(entries[:count]):
            edit = grouped.pop(f"{bank.name}:{index:04X}", None)
            name = native
            if edit is not None:
                if edit["source_sha256"] != sha256(native):
                    raise ValueError("Stale extended item-name source")
                name = encode(edit["translation"], info)
                if (not name or len(name) > WIDTH or
                        any(t.kind != "text" or t.data[0] not in LATIN for t in tokenize(name, info))):
                    raise ValueError("Extended item name exceeds capacity or contains nonplain text")
                if sha256(name.ljust(WIDTH, b" ")) != edit["provenance"]["reference_sha256"]:
                    raise ValueError("Extended item-name reference hash mismatch")
            output.extend(name.ljust(WIDTH, b" "))
    if grouped:
        raise ValueError("Unknown extended item-name IDs")
    return bytes(output)


def install(rom, additions, module_report, directory):
    from runtime_module import MODULE_RAM, MODULE_VROM
    report = json.loads((directory/"names.json").read_text())
    data = (directory/"names.bin").read_bytes()
    if (report["source_sha256"] != sha256(rom) or report["data_sha256"] != sha256(data) or
            data[:32] != HEADER or len(data) != len(HEADER)+sum(COUNTS)*WIDTH or
            resource(rom, report["edits"]) != data):
        raise ValueError("Stale or invalid extended item-name resource")
    if not module_report or MODULE_VROM not in additions or "af_load_item_name" not in module_report["symbols"]:
        raise ValueError("Extended item names require the complete capable resident module")
    if VROM in additions:
        raise ValueError("Duplicate extended item-name DMA entry")
    module = bytearray(additions[MODULE_VROM])
    if sha256(module) != module_report["module_sha256"]:
        raise ValueError("Extended item names require unchanged verified module bytes")
    if module[56:60] != bytes(4):
        raise ValueError("Unexpected resident item-resource configuration")
    struct.pack_into(">I", module, 56, VROM)
    additions[MODULE_VROM] = bytes(module)
    additions[VROM] = data
    return {"source_sha256": report["source_sha256"], "data_sha256": sha256(data),
            "vrom": f"{VROM:08X}", "width": WIDTH, "entries": sum(COUNTS),
            "candidate_slots": len(report["edits"]), "bytes": len(data),
            "module_configuration_ram": f"{MODULE_RAM+56:08X}",
            "configured_module_sha256": sha256(module),
            "status": "experimental item resource; only independently verified caller hooks may use sixteen bytes"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--gc-names", type=Path, default=Path("build/gamecube/names"))
    parser.add_argument("--output", type=Path, default=Path("build/extended-items"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    edits, reports, remaining_by_bank = [], {}, {}
    source_banks = {bank.name: bank for bank in banks(rom)}
    matches = load_matches()
    originals = load_native_names()
    args.output.mkdir(parents=True, exist_ok=True)
    for bank in source_banks.values():
        if not bank.name.startswith("item_"):
            continue
        rows = list(map(json.loads, (args.inventory/(bank.name+".jsonl")).read_text().splitlines()))
        refs = reference_rows(args.gc_names, bank.name, matches)
        candidates, _, remaining, report = item_candidates(bank, rows, refs, info, capacity=WIDTH, matches=matches, originals=originals)
        edits.extend(candidates)
        reports[bank.name] = report
        remaining_by_bank[bank.name] = remaining
    aliases = confirmed_aliases(source_banks, edits, info, capacity=WIDTH)
    update_alias_reports(edits, aliases, remaining_by_bank, reports)
    edits.extend(aliases)
    for name, remaining in remaining_by_bank.items():
        (args.output/(name+"-remaining.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in remaining))
    data = resource(rom, edits)
    report = {"source_sha256": sha256(rom), "data_sha256": sha256(data), "banks": reports, "edits": edits,
              "status": "local candidates; no native caller expansion or translation review implied"}
    (args.output/"names.bin").write_bytes(data)
    (args.output/"names.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"bytes": len(data), "candidate_slots": len(edits), "banks": reports}, indent=2))


if __name__ == "__main__":
    main()
