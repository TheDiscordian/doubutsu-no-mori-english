#!/usr/bin/env python3
"""Inventory string-loader callers and conservative immediate argument evidence."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, verified_rom

TARGET = 0x800C3F70


def immediate_argument(words, call, register):
    """Return only an immediate in this straight-line suffix, never a proof.

    Branches and previous calls stop the search. Any other write to the target
    register makes its value unknown. The current call's delay slot runs first.
    """
    positions = [call+1]+list(range(call-1, max(-1, call-25), -1))
    for index in positions:
        if not 0 <= index < len(words):
            return None
        word = words[index]
        op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
        low = word & 0xFFFF
        if op in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23) or op == 0 and word & 63 in (8, 9):
            return None
        if op == 17 and rs == 8:
            return None
        if op in (8, 9, 13) and rt == register and rs == 0:
            value = low-(0x10000 if op in (8, 9) and low & 0x8000 else 0)
            return {"value": value, "instruction": f"{word:08X}", "word_offset": index}
        if op == 0 and rd == register and word & 63 not in (17, 19, 24, 25, 26, 27):
            return None
        if op in (8, 9, 10, 11, 12, 13, 14, 15, 24, 25, 26, 27,
                  32, 33, 34, 35, 36, 37, 38, 39, 48, 52, 55, 56, 60) and rt == register:
            return None
        if op in (16, 17, 18) and rs in (0, 1, 2) and rt == register:
            return None
        if op in (28, 31):  # SPECIAL2/3 are not decoded by this evidence helper.
            return None
    return None


def audit(rom, target=TARGET):
    files, records, definitions = by_vrom(rom), [], {}
    root = Path(__file__).resolve().parents[1]/"upstream/af/yamls/jp"
    for name in ("makerom.yaml", "boot.yaml", "code.yaml", "overlays.yaml"):
        data = (root/name).read_bytes()
        definitions[name] = sha256(data)
        for block in re.split(r"(?m)^  - name: ", data.decode())[1:]:
            if not re.search(r"(?m)^    type: code\s*$", block):
                continue
            start = re.search(r"(?m)^    start: (0x[0-9a-fA-F]+)\s*$", block)
            ram = re.search(r"(?m)^    vram: (0x[0-9a-fA-F]+)\s*$", block)
            if not start or not ram:
                raise ValueError("Unexpected executable segment definition")
            vrom, base = int(start[1], 16), int(ram[1], 16)
            entry = files.get(vrom)
            if not entry or entry.pstart == 0xFFFFFFFF:
                continue
            code = entry.extract(rom)
            words = [value for (value,) in struct.iter_unpack(">I", code[:len(code)//4*4])]
            for index, word in enumerate(words):
                if word not in (0x08000000 | (target & 0x0FFFFFFF) >> 2,
                                0x0C000000 | (target & 0x0FFFFFFF) >> 2):
                    continue
                records.append({"segment": block.splitlines()[0].strip(), "vrom": f"{vrom:08X}",
                                "linked_ram": f"{base:08X}", "file_sha256": sha256(code),
                                "offset": f"{index*4:06X}", "call_ram": f"{base+index*4:08X}",
                                "destination_length": immediate_argument(words, index, 5),
                                "string_id": immediate_argument(words, index, 6),
                                "context": [{"ram": f"{base+i*4:08X}", "word": f"{words[i]:08X}"}
                                            for i in range(max(0, index-16), min(len(words), index+3))]})
    if not records:
        raise ValueError("No string loader callers found")
    return {"source_sha256": sha256(rom), "target_ram": f"{target:08X}",
            "definition_sha256": definitions, "callers": records,
            "capacity_counts": dict(Counter(str(r["destination_length"]["value"])
                                    if r["destination_length"] else "unknown" for r in records)),
            "status": "Evidence inventory only; callers, indirect uses, destination storage, and display need review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/audits/string-callers.json"))
    args = parser.parse_args()
    report = audit(verified_rom(args.rom.read_bytes()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"callers": len(report["callers"]), "capacity_counts": report["capacity_counts"],
                      "output": str(args.output), "status": report["status"]}))


if __name__ == "__main__":
    main()
