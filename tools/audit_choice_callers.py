#!/usr/bin/env python3
"""Verify the complete retail DMA scan for choice loader/setter callers."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, dma_entries, verified_rom
from english_runtime import CHOICE_ROWS, CHOICE_SELECTED

EXPECTED = {
    0x80065D90: {(0x675720, 0x4F484), (0x849B50, 0xB30),
                 (0x8A1F10, 0xAF4), (0x8A1F10, 0xB0C), (0x8A1F10, 0xC18)},
    0x80065278: {(0x675720, 0x4F504), (0x849B50, 0xB8C),
                 (0x8A1F10, 0xCA8), (0x8A1F10, 0xD84), (0x932B60, 0x6A8)},
    0x800651A4: {(0x675720, 0x13838), (0x675720, 0x13860),
                 (0x675720, 0x13888), (0x675720, 0x138B0)},
}


def audit(rom):
    found = {target: set() for target in EXPECTED}
    reclaimed_references = []
    entries = 0
    for entry in dma_entries(rom):
        if entry.pstart == 0xFFFFFFFF:
            continue
        entries += 1
        data = entry.extract(rom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from(">I", data, offset)[0]
            op = word >> 26
            if op in (2, 3):
                target = 0x80000000 | ((word & 0x3FFFFFF) << 2)
                if target in found:
                    found[target].add((entry.vstart, offset))
                if CHOICE_ROWS <= target < CHOICE_SELECTED+16:
                    reclaimed_references.append((entry.vstart, offset, target, "jump"))
            if CHOICE_ROWS <= word < CHOICE_SELECTED+16:
                reclaimed_references.append((entry.vstart, offset, word, "pointer"))
            # Only main-code PC-relative branches can reach this main-code
            # region. The removed suffix block itself contains no branches.
            if entry.vstart == CODE_VROM and op in (1, 4, 5, 6, 7, 20, 21, 22, 23):
                immediate = (word & 0xFFFF) - (0x10000 if word & 0x8000 else 0)
                target = CODE_RAM+offset+4+immediate*4
                if CHOICE_ROWS <= target < CHOICE_SELECTED+16:
                    reclaimed_references.append((entry.vstart, offset, target, "branch"))
    if found != EXPECTED:
        raise ValueError(f"Unexpected choice callers: {found}")
    if reclaimed_references:
        raise ValueError(f"Reclaimed choice RAM has retail references: {reclaimed_references}")
    return {"decoded_files_scanned": entries, "reclaimed_code_references": [],
            "direct_callers": {f"{target:08X}": [{"vrom": f"{vrom:08X}", "offset": f"{off:06X}"}
                               for vrom, off in sorted(callers)] for target, callers in found.items()},
            "scope": "aligned J/JAL, literal pointers, and main-code branches; interpreted with pinned source/disassembly"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/choice-callers.json"))
    args = parser.parse_args()
    result = audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
