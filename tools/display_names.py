#!/usr/bin/env python3
"""Build complete eight-byte display names from locally confirmed GC identities."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from gc_text import plain
from name_candidates import NPC_COUNT, npc_candidates
from textbanks import banks
from textcodec import LATIN, command_info, encode, tokenize

VROM, WIDTH, SPECIAL_COUNT = 0x02C00000, 8, 64
SPECIAL_RAM = 0x8010B510
SPECIAL_HASH = "7c64038afa6e02bc9baee32fe52d46c873c8de5ded7f01193cf6f7cfd96a5523"
HEADER = struct.pack(">8I", 0x41464E4E, 1, WIDTH, NPC_COUNT+SPECIAL_COUNT, NPC_COUNT, SPECIAL_COUNT, 0, 0)


def special_table(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    data = code[SPECIAL_RAM-CODE_RAM:SPECIAL_RAM-CODE_RAM+SPECIAL_COUNT*12]
    if sha256(data) != SPECIAL_HASH:
        raise ValueError("Unexpected native special-character table")
    records = list(struct.iter_unpack(">HHII", data))
    if len({r[0] for r in records}) != SPECIAL_COUNT:
        raise ValueError("Duplicate special actor identity")
    return records


def resource(rom, edits):
    source = {b.name: b for b in banks(rom)}
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    natives, strings = source["npc_names"].entries(), source["string"].entries()
    rows = [(f"npc_names:{i:04X}", natives[i], f"npc_names:{i:04X}") for i in range(NPC_COUNT)]
    rows += [(f"special_names:{actor:04X}", strings[index], f"string:{index:04X}")
             for actor, _, index, _ in special_table(rom)]
    selected = {}
    for edit in edits:
        if edit["id"] in selected:
            raise ValueError("Duplicate display-name ID")
        selected[edit["id"]] = edit
    output = bytearray(HEADER)
    for id, native, reference_id in rows:
        edit = selected.pop(id, None)
        if not edit or edit["source_sha256"] != sha256(native):
            raise ValueError("Missing or stale display-name source")
        name = encode(edit["translation"], info)
        if not 1 <= len(name) <= WIDTH or any(t.kind != "text" or t.data[0] not in LATIN
                                             for t in tokenize(name, info)):
            raise ValueError("Display name must fit eight plain Latin bytes")
        reference = name.ljust(WIDTH, b" ") if id.startswith("npc_names:") else name
        provenance = edit["provenance"]
        if provenance["reference_id"] != reference_id or provenance["reference_sha256"] != sha256(reference):
            raise ValueError("Display-name reference identity/hash mismatch")
        output.extend(name.ljust(WIDTH, b" "))
    if selected:
        raise ValueError("Unknown display-name IDs")
    return bytes(output)


def indexed(path):
    result = {}
    for row in map(json.loads, path.read_text().splitlines()):
        if row["id"] in result:
            raise ValueError("Duplicate display-name input ID")
        result[row["id"]] = row
    return result


def install(rom, additions, module_report, directory):
    from extended_items import VROM as ITEM_VROM
    from runtime_module import MODULE_RAM, MODULE_VROM
    report = json.loads((directory/"names.json").read_text())
    data = (directory/"names.bin").read_bytes()
    if (report["source_sha256"] != sha256(rom) or report["data_sha256"] != sha256(data)
            or report["special_table_sha256"] != SPECIAL_HASH or resource(rom, report["edits"]) != data):
        raise ValueError("Stale or invalid display-name resource")
    if not module_report or MODULE_VROM not in additions or "af_load_display_name" not in module_report["symbols"]:
        raise ValueError("Display names require the complete capable resident module")
    module = bytearray(additions[MODULE_VROM])
    # The independent item resource is installed first. Only its exact known
    # configuration word may differ from the source-verified module artifact.
    original = bytearray(module)
    item = struct.unpack_from(">I", original, 56)[0]
    if item:
        if item != ITEM_VROM or item not in additions:
            raise ValueError("Unverified item-resource module configuration")
        original[56:60] = bytes(4)
    if sha256(original) != module_report["module_sha256"]:
        raise ValueError("Display names require unchanged verified module bytes")
    if module[60:64] != bytes(4) or VROM in additions:
        raise ValueError("Duplicate display-name configuration")
    struct.pack_into(">I", module, 60, VROM)
    additions[MODULE_VROM], additions[VROM] = bytes(module), data
    return {"source_sha256": report["source_sha256"], "data_sha256": sha256(data),
            "vrom": f"{VROM:08X}", "width": WIDTH, "entries": NPC_COUNT+SPECIAL_COUNT,
            "bytes": len(data), "module_configuration_ram": f"{MODULE_RAM+60:08X}",
            "configured_module_sha256": sha256(module),
            "status": "experimental display-name API; native six-byte callers remain unchanged"}


def candidates(rom, inventory, gc_names, gc_text):
    source = {b.name: b for b in banks(rom)}
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    edits, _, remaining, _ = npc_candidates(source["npc_names"],
        list(indexed(inventory/"npc_names.jsonl").values()),
        list(indexed(gc_names/"npc_names.jsonl").values()), info, capacity=WIDTH)
    if remaining or len(edits) != NPC_COUNT:
        raise ValueError("Incomplete confirmed display-name identities")
    native, reference = indexed(inventory/"string.jsonl"), indexed(gc_text/"string.jsonl")
    strings = source["string"].entries()
    for actor, _, index, _ in special_table(rom):
        id = f"string:{index:04X}"
        row, ref = native[id], reference[id]
        if row["source_sha256"] != sha256(strings[index]) or plain(row.get("legacy", "")).strip() != ref["text"]:
            raise ValueError("Special-character name identity is not confirmed")
        edits.append({"id": f"special_names:{actor:04X}", "source_sha256": row["source_sha256"],
                      "translation": ref["text"], "status": "mechanically_validated_candidate_not_reviewed",
                      "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                          "reference_id": id, "reference_sha256": ref["sha256"],
                          "match_basis": "native_special_actor_table_and_same_id_name_confirmed_by_legacy"}})
    resource(rom, edits)
    return edits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--gc-names", type=Path, default=Path("build/gamecube/names"))
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--output", type=Path, default=Path("build/display-names"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    edits = candidates(rom, args.inventory, args.gc_names, args.gc_text)
    data = resource(rom, edits)
    report = {"source_sha256": sha256(rom), "data_sha256": sha256(data), "special_table_sha256": SPECIAL_HASH,
              "villager_names": NPC_COUNT, "special_actor_rows": SPECIAL_COUNT,
              "distinct_special_names": len({r[2] for r in special_table(rom)}), "edits": edits,
              "status": "local display-name candidates; no native saved-name expansion or review implied"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/"names.bin").write_bytes(data)
    (args.output/"names.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "edits"}, indent=2))


if __name__ == "__main__":
    main()
