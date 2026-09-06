#!/usr/bin/env python3
"""Build experimental halfwidth ROMs from verified retail input."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, apply_ups, by_vrom, make_ups, n64_checksum, replace_dma, sha256, verified_rom
from font import ATLAS_OFFSET, ATLAS_SIZE, FONT_VROM, make_halfwidth, pixels, png_gray
from textbanks import banks
from textcodec import command_info, control_signature, encode


def apply_translations(rom, replacements, path):
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
            if control_signature(original, info) != control_signature(replacement, info):
                raise ValueError(f"Translation changes control flow or formatting commands: {edit['id']}")
            # Per-entry expansion is enabled separately after loader/buffer audit.
            if len(replacement) > len(original):
                raise ValueError(f"Translation exceeds current entry budget: {edit['id']}")
            if bank.fixed_size:
                replacement = replacement.ljust(bank.fixed_size, b" ")
            entries[index] = replacement
            count += 1
        data, table = bank.rebuild(entries)
        for vrom, offset, content in ((bank.data_vrom, bank.data_offset, data),
                                      (bank.table_vrom, bank.table_offset, table)):
            if vrom is None:
                continue
            whole = bytearray(replacements.get(vrom, files[vrom].extract(rom)))
            whole[offset:offset+len(content)] = content
            replacements[vrom] = bytes(whole)
    if grouped:
        raise ValueError(f"Unknown translation banks: {list(grouped)}")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--translations", type=Path)
    parser.add_argument("--output", type=Path, default=Path("build/halfwidth"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    replacements, report = make_halfwidth(rom)
    report["translation_edits"] = apply_translations(rom, replacements, args.translations)
    output = replace_dma(rom, replacements)
    files = by_vrom(output)
    for vrom, data in replacements.items():
        if files[vrom].extract(output) != data:
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
