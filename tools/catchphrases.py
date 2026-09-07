#!/usr/bin/env python3
"""Build full default catchphrase references without changing native saved text."""

import argparse
from collections import defaultdict
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from display_names import indexed
from gc_names import symbol_data
from gc_text import plain
from name_candidates import NPC_COUNT, npc_candidates
from textbanks import banks
from textcodec import LATIN, command_info, encode, tokenize

VROM, WIDTH, ROW_WIDTH = 0x02E00000, 10, 16
DEFAULT_VROM = 0x00E03000
NATIVE_TABLE_HASH = "a8d2574dfa74a4c585ab7d07be2a3ce974d27e81720011ce60d47cf6be1b7221"
GC_TABLE_HASH = "3ff2a752dd4bd0b1ed9f2e0b0de317790d65cb78f3c4e420ac392871a93857ca"
GC_REL_HASH = "29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837"
HEADER = struct.pack(">8I", 0x41464350, 1, WIDTH, NPC_COUNT, ROW_WIDTH, 4, 0, 0)


def native_table(rom):
    data = by_vrom(rom)[DEFAULT_VROM].extract(rom)
    if sha256(data) != NATIVE_TABLE_HASH:
        raise ValueError("Unexpected native catchphrase default table")
    return list(struct.iter_unpack(">HHbB", data[:NPC_COUNT*6]))


def resource(rom, edits):
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    strings = next(b for b in banks(rom) if b.name == "string").entries()
    selected, rows = {}, []
    for edit in edits:
        if edit["id"] in selected:
            raise ValueError("Duplicate catchphrase identity")
        selected[edit["id"]] = edit
    for index, (_, string_id, _, _) in enumerate(native_table(rom)):
        edit = selected.pop(f"catchphrases:{index:04X}", None)
        native = strings[string_id]
        if not edit or edit["source_sha256"] != sha256(native):
            raise ValueError("Missing or stale catchphrase source")
        if not 1 <= len(native) <= 4 or all(byte in LATIN for byte in native):
            raise ValueError("Native default is not an unambiguous non-Latin saved key")
        text = encode(edit["translation"], info)
        if not 1 <= len(text) <= WIDTH or any(t.kind != "text" or t.data[0] not in LATIN
                                            for t in tokenize(text, info)):
            raise ValueError("Catchphrase must fit ten plain Latin bytes")
        provenance = edit["provenance"]
        if (provenance["reference_id"] != f"string:{string_id:04X}"
                or provenance["reference_sha256"] != sha256(text)
                or provenance["default_table_sha256"] != GC_TABLE_HASH):
            raise ValueError("Catchphrase reference identity/hash mismatch")
        rows.append(native.ljust(4, b" ")+struct.pack(">H", 0xE000+index)+text.ljust(WIDTH, b" "))
    if selected:
        raise ValueError("Unknown catchphrase identities")
    return HEADER+b"".join(sorted(rows))


def candidates(rom, inventory, gc_names, gc_text, extracted, decomp):
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    names = next(b for b in banks(rom) if b.name == "npc_names")
    confirmed, _, remaining, _ = npc_candidates(names, list(indexed(inventory/"npc_names.jsonl").values()),
        list(indexed(gc_names/"npc_names.jsonl").values()), info, capacity=8)
    if remaining or len(confirmed) != NPC_COUNT:
        raise ValueError("Catchphrase villager identities are not all confirmed")
    rel = (extracted/"foresta.rel.szs.decoded").read_bytes()
    if sha256(rel) != GC_REL_HASH:
        raise ValueError("Unexpected GameCube executable reference")
    data = symbol_data(rel, (decomp/"config/GAFE01_00/foresta/symbols.txt").read_text(), "npc_def_list")
    if sha256(data) != GC_TABLE_HASH:
        raise ValueError("Unexpected GameCube catchphrase default table")
    reference_table = list(struct.iter_unpack(">HHbB", data))
    native, refs = indexed(inventory/"string.jsonl"), indexed(gc_text/"string.jsonl")
    edits = []
    for index, (_, source_id, _, _) in enumerate(native_table(rom)):
        reference_id = reference_table[index][1]
        if source_id != reference_id:
            raise ValueError("Catchphrase table identity differs; explicit matching required")
        id = f"string:{source_id:04X}"
        row, ref = native[id], refs[id]
        if plain(row.get("legacy", "")).strip() != ref["text"]:
            raise ValueError("Catchphrase reference is not confirmed by legacy text")
        edits.append({"id": f"catchphrases:{index:04X}", "source_sha256": row["source_sha256"],
            "translation": ref["text"], "status": "mechanically_validated_candidate_not_reviewed",
            "provenance": {"source": "user-supplied GAFE01 revision 0 disc",
                "reference_id": id, "reference_sha256": ref["sha256"], "default_table_sha256": GC_TABLE_HASH,
                "match_basis": "confirmed_villager_identity_native_and_gc_default_tables_and_legacy_text"}})
    resource(rom, edits)
    return edits


def validate_saved_defaults(rom, replacements, edits):
    """A default loader may retain Japanese or a complete short English phrase."""
    bank = next(b for b in banks(rom) if b.name == "string")
    entries = replace(bank, data=replacements.get(bank.data_vrom, bank.data),
                      table=replacements.get(bank.table_vrom, bank.table)).entries()
    originals = bank.entries()
    if len(entries) != len(originals):
        raise ValueError("Changed catchphrase source-bank entry count")
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    selected = {e["id"]: e for e in edits}
    for index, (_, source_id, _, _) in enumerate(native_table(rom)):
        english = encode(selected[f"catchphrases:{index:04X}"]["translation"], info)
        entry = entries[source_id]
        if entry != originals[source_id] and (len(entry) > 4 or entry.rstrip(b" ") != english.rstrip(b" ")):
            raise ValueError("Native catchphrase edit loses its complete verified default")


def install(rom, additions, module_report, directory, replacements=None):
    from runtime_module import MODULE_RAM, MODULE_VROM
    report = json.loads((directory/"catchphrases.json").read_text())
    data = (directory/"catchphrases.bin").read_bytes()
    if (report["source_sha256"] != sha256(rom) or report["data_sha256"] != sha256(data)
            or resource(rom, report["edits"]) != data):
        raise ValueError("Stale or invalid catchphrase resource")
    validate_saved_defaults(rom, replacements or {}, report["edits"])
    if not module_report or MODULE_VROM not in additions or "af_copy_catchphrase" not in module_report["symbols"]:
        raise ValueError("Catchphrases require the complete capable resident module")
    module = bytearray(additions[MODULE_VROM])
    original = bytearray(module)
    for offset, expected in ((56, 0x02A00000), (60, 0x02C00000)):
        value = struct.unpack_from(">I", original, offset)[0]
        if value and (value != expected or value not in additions):
            raise ValueError("Unverified preceding module resource configuration")
        original[offset:offset+4] = bytes(4)
    if sha256(original) != module_report["module_sha256"]:
        raise ValueError("Catchphrases require unchanged verified module bytes")
    if module[64:68] != bytes(4) or VROM in additions:
        raise ValueError("Duplicate catchphrase configuration")
    struct.pack_into(">I", module, 64, VROM)
    additions[MODULE_VROM], additions[VROM] = bytes(module), data
    return {"source_sha256": report["source_sha256"], "data_sha256": sha256(data),
            "vrom": f"{VROM:08X}", "width": WIDTH, "rows": NPC_COUNT, "bytes": len(data),
            "module_configuration_ram": f"{MODULE_RAM+64:08X}", "configured_module_sha256": sha256(module),
            "status": "experimental default main-message display; custom editing and saved fields remain native"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=Path("build/inventory"))
    parser.add_argument("--gc-names", type=Path, default=Path("build/gamecube/names"))
    parser.add_argument("--gc-text", type=Path, default=Path("build/gamecube/text"))
    parser.add_argument("--extracted", type=Path, default=Path("build/gamecube/files"))
    parser.add_argument("--decomp", type=Path, default=Path("local/ac-decomp"))
    parser.add_argument("--output", type=Path, default=Path("build/catchphrases"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    edits = candidates(rom, args.inventory, args.gc_names, args.gc_text, args.extracted, args.decomp)
    data = resource(rom, edits)
    groups = defaultdict(list)
    for offset in range(32, len(data), ROW_WIDTH):
        row = data[offset:offset+ROW_WIDTH]
        groups[row[:4].hex()].append(row)
    report = {"source_sha256": sha256(rom), "data_sha256": sha256(data), "bytes": len(data),
        "native_default_table_sha256": NATIVE_TABLE_HASH, "reference_default_table_sha256": GC_TABLE_HASH,
        "reference_executable_sha256": GC_REL_HASH, "villagers": len(edits), "distinct_saved_keys": len(groups),
        "ambiguous_borrowed_keys": [{"key": key, "villagers": [f"{int.from_bytes(r[4:6], 'big'):04X}" for r in rows]}
            for key, rows in groups.items() if len({r[6:] for r in rows}) > 1],
        "edits": edits, "status": "local default-reference candidates; no custom-editing or save expansion"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/"catchphrases.bin").write_bytes(data)
    (args.output/"catchphrases.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "edits"}, indent=2))


if __name__ == "__main__":
    main()
