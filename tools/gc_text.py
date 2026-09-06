#!/usr/bin/env python3
"""Extract local English references and measure conservative N64 matches."""

import argparse
import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

from aflib import sha256
from textbanks import Bank


def decoder_tables(path):
    # Read literal format tables from the pinned CC0 decompilation tool without
    # executing third-party Python. Preserve its upstream attribution locally.
    values = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ("CHAR_MAP", "CONT_SIZES", "COMMANDS"):
                values[target.id] = ast.literal_eval(node.value)
    if len(values.get("CHAR_MAP", [])) != 256 or len(values.get("CONT_SIZES", [])) != 123:
        raise ValueError("Unexpected GameCube decoder tables")
    return values


def decode_gc(data, tables):
    pos, result = 0, []
    while pos < len(data):
        byte = data[pos]
        if byte == 0x7F:
            if pos+1 >= len(data) or data[pos+1] >= len(tables["CONT_SIZES"]):
                raise ValueError(f"Unknown/truncated GameCube command at {pos:#x}")
            size = tables["CONT_SIZES"][data[pos+1]]
            if pos+size > len(data):
                raise ValueError("Truncated GameCube command arguments")
            result.append("{cmd:"+data[pos:pos+size].hex().upper()+"}")
            pos += size
        else:
            result.append(tables["CHAR_MAP"][byte])
            pos += 1
    return "".join(result)


def plain(text):
    return re.sub(r"\s+", " ", re.sub(r"\{(?:cmd|raw|glyph):[0-9A-Fa-f]+\}", "", text)).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extracted", type=Path, default=Path("build/gamecube/files"))
    parser.add_argument("--decoder", type=Path, default=Path("local/ac-decomp/tools/msg_tool.py"))
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--output", type=Path, default=Path("build/gamecube/text"))
    args = parser.parse_args()
    tables = decoder_tables(args.decoder)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {}
    for path in sorted(args.extracted.rglob("*_data_table.bin")):
        name = path.name.removesuffix("_data_table.bin")
        data_path = path.with_name(name+"_data.bin")
        bank = Bank(name, 0, 0, data_path.read_bytes(), path.read_bytes())
        rows, exact = [], defaultdict(list)
        for index, data in enumerate(bank.entries()):
            row = {"id": f"{name}:{index:04X}", "sha256": sha256(data), "bytes": len(data)}
            try:
                row["text"] = decode_gc(data, tables)
                if plain(row["text"]):
                    exact[plain(row["text"])].append(index)
            except ValueError as exc:
                row["error"] = str(exc)
            rows.append(row)
        (args.output/(name+".jsonl")).write_text("".join(json.dumps(row, ensure_ascii=False)+"\n" for row in rows))
        counts = Counter(entries=len(rows), decode_errors=sum("error" in r for r in rows))
        inventory_path = args.inventory/(name+".jsonl")
        matches = []
        if inventory_path.exists():
            for line in inventory_path.read_text().splitlines():
                source = json.loads(line)
                key = plain(source.get("legacy", ""))
                candidates = exact.get(key, [])
                row = {"n64_id": source["id"], "source_sha256": source["source_sha256"],
                       "gc_candidates": [rows[i]["id"] for i in candidates],
                       "method": "legacy_visible_text_exact" if candidates else "unmatched",
                       "status": "reference_only_not_approved"}
                counts["unique_legacy_match" if len(candidates) == 1 else
                       "ambiguous_legacy_match" if candidates else "unmatched"] += 1
                same = int(source["id"].split(":")[1], 16)
                if same in candidates:
                    counts["same_id_visible_text_match"] += 1
                matches.append(row)
            (args.output/(name+"-matches.jsonl")).write_text("".join(json.dumps(r)+"\n" for r in matches))
        report[name] = dict(counts)
    (args.output/"summary.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
