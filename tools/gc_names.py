#!/usr/bin/env python3
"""Extract English item/NPC names from local GAFE01 resources and REL symbols."""

import argparse
import json
from pathlib import Path
import re

from aflib import sha256, u32
from gc_text import decode_gc, decoder_tables


def rel_sections(data):
    if len(data) < 0x48:
        raise ValueError("Truncated REL header")
    count, table = u32(data, 12), u32(data, 16)
    if not 1 <= count <= 32 or table+count*8 > len(data):
        raise ValueError("Invalid REL section table")
    result = []
    for i in range(count):
        offset, size = u32(data, table+i*8)&~3, u32(data, table+i*8+4)
        if offset and offset+size > len(data):
            raise ValueError("REL section exceeds file")
        result.append((offset, size))
    return result


def symbol_data(data, symbols, name):
    match = re.search(r"^"+re.escape(name)+r" = (\.\w+):0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+)",
                      symbols, re.MULTILINE)
    if not match:
        raise ValueError(f"Missing REL symbol: {name}")
    sections = {".text": 1, ".ctors": 2, ".dtors": 3, ".rodata": 4, ".data": 5, ".bss": 6}
    base, capacity = rel_sections(data)[sections[match[1]]]
    offset, size = int(match[2], 16), int(match[3], 16)
    if not base or offset+size > capacity:
        raise ValueError(f"REL symbol outside file-backed section: {name}")
    return data[base+offset:base+offset+size]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extracted", type=Path, default=Path("build/gamecube/files"))
    parser.add_argument("--decomp", type=Path, default=Path("local/ac-decomp"))
    parser.add_argument("--output", type=Path, default=Path("build/gamecube/names"))
    args = parser.parse_args()
    data = (args.extracted/"foresta.rel.szs.decoded").read_bytes()
    symbols = (args.decomp/"config/GAFE01_00/foresta/symbols.txt").read_text()
    tables = decoder_tables(args.decomp/"tools/msg_tool.py")
    names = ["paper", "money", "tool", "fish", "cloth", "etc", "carpet", "wall", "fruit", "plant",
             "minidisk", "dummy", "ticket", "insect", "hukubukuro", "kabu"]
    blocks = {f"item_{0x20+i:02X}": (symbol_data(data, symbols, "itemName_"+name), 16)
              for i, name in enumerate(names)}
    blocks["furniture"] = (symbol_data(data, symbols, "ftrName_table"), 16)
    blocks["furniture_gc_added"] = (symbol_data(data, symbols, "ftrName2_table"), 16)
    blocks["npc_names"] = ((args.extracted/"forest_2nd.arc.unpacked/data/npc_name_str_table.bin").read_bytes(), 8)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {}
    for name, (block, width) in blocks.items():
        if len(block) % width:
            raise ValueError(f"Partial GameCube name: {name}")
        rows = [{"id": f"{name}:{i//width:04X}", "text": decode_gc(block[i:i+width], tables).rstrip(" "),
                 "source_sha256": sha256(block[i:i+width]), "status": "reference_only_not_approved"}
                for i in range(0, len(block), width)]
        (args.output/(name+".jsonl")).write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows))
        report[name] = {"entries": len(rows), "fixed_width": width, "sha256": sha256(block)}
    (args.output/"summary.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
