#!/usr/bin/env python3
"""Build experimental halfwidth ROMs from verified retail input."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, make_ups, n64_checksum, replace_dma, sha256, verified_rom
from font import ATLAS_OFFSET, ATLAS_SIZE, FONT_VROM, make_halfwidth, pixels, png_gray
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import validate_entry
from keyboard import make_english_keyboard
from english_runtime import make_english_runtime, verify_english_runtime

RELOCATED_BANKS = {
    "message": (0x02000000, 0x8009E474, "3C1800BD27184000", "3C18020027180000"),
    "select": (0x02400000, 0x80065614, "3C1800D027185000", "3C18024027180000"),
}


def apply_translations(rom, replacements, path, *, english_runtime=False):
    if english_runtime:
        verify_english_runtime(rom, replacements)
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    edits = json.loads(path.read_text()) if path else []
    grouped, seen = {}, set()
    for edit in edits:
        bank, index = edit["id"].split(":")
        if edit["id"] in seen:
            raise ValueError("Duplicate translation ID")
        seen.add(edit["id"])
        grouped.setdefault(bank, {})[int(index, 16)] = edit
    count = 0
    relocations = {}
    files = by_vrom(rom)
    for bank in banks(rom):
        if bank.name not in grouped:
            continue
        entries = bank.entries()
        for index, edit in grouped.pop(bank.name).items():
            if not 0 <= index < len(entries):
                raise ValueError(f"Unknown entry: {edit['id']}")
            original = entries[index]
            if sha256(original) != edit["source_sha256"]:
                raise ValueError(f"Stale translation: {edit['id']}")
            replacement = encode(edit["translation"], info)
            try:
                validate_entry(original, replacement, info, bank.name, edit.get("control_policy", "exact"),
                               choice_bytes=16 if english_runtime else 10)
            except ValueError as exc:
                raise ValueError(f"{edit['id']}: {exc}") from exc
            if bank.fixed_size:
                replacement = replacement.ljust(bank.fixed_size, b" ")
            entries[index] = replacement
            count += 1
        data, table = bank.rebuild(entries, allow_expand=(bank.name in RELOCATED_BANKS))
        if bank.name in RELOCATED_BANKS:
            new_vrom, address, expected, patched = RELOCATED_BANKS[bank.name]
            relocations[bank.data_vrom] = new_vrom
            data += bytes(-len(data) % 16)
            code = bytearray(replacements[CODE_VROM])
            offset = address-CODE_RAM
            if code[offset:offset+8] != bytes.fromhex(expected):
                raise ValueError(f"Retail {bank.name} loader address does not match")
            code[offset:offset+8] = bytes.fromhex(patched)
            replacements[CODE_VROM] = bytes(code)
        for vrom, offset, content in ((bank.data_vrom, bank.data_offset, data),
                                      (bank.table_vrom, bank.table_offset, table)):
            if vrom is None:
                continue
            whole = bytearray(replacements.get(vrom, files[vrom].extract(rom)))
            whole[offset:offset+len(content)] = content
            replacements[vrom] = bytes(whole)
    if grouped:
        raise ValueError(f"Unknown translation banks: {list(grouped)}")
    return count, relocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--translations", type=Path)
    parser.add_argument("--english-keyboard", action="store_true")
    parser.add_argument("--english-runtime", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("build/halfwidth"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    replacements, report = make_halfwidth(rom)
    if args.english_keyboard:
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        keyboard, report["keyboard"] = make_english_keyboard(rom, info, report["advance_by_glyph"])
        replacements.update(keyboard)
    if args.english_runtime:
        runtime, report["english_runtime"] = make_english_runtime(rom, replacements)
        replacements.update(runtime)
    report["translation_edits"], relocations = apply_translations(
        rom, replacements, args.translations, english_runtime=args.english_runtime)
    report["vrom_relocations"] = {f"{a:08X}": f"{b:08X}" for a, b in relocations.items()}
    output = replace_dma(rom, replacements, relocations)
    files = by_vrom(output)
    for vrom, data in replacements.items():
        if files[relocations.get(vrom, vrom)].extract(output) != data:
            raise ValueError("Reinserted file does not match replacement")
    if n64_checksum(output) != struct.unpack_from(">2I", output, 16):
        raise ValueError("Output checksum failure")
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "animal-forest-halfwidth.z64").write_bytes(output)
    patch = make_ups(rom, output)
    if apply_ups(rom, patch) != output:
        raise ValueError("Generated patch round trip failed")
    (args.output / "animal-forest-halfwidth.ups").write_bytes(patch)
    report.update(source_sha256=sha256(rom), output_sha256=sha256(output),
                  size=len(output), patch_sha256=sha256(patch),
                  replacement_files=[f"{v:08X}" for v in replacements],
                  release_status="experimental; original hardware untested")
    (args.output / "build.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, font in (("original", by_vrom(rom)[FONT_VROM].extract(rom)),
                       ("halfwidth", replacements[FONT_VROM])):
        atlas = pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        (args.output / f"font-{name}.png").write_bytes(png_gray(192, 256, [p*17 for p in atlas]))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
