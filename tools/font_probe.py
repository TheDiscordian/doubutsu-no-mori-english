#!/usr/bin/env python3
"""Build local-only glyph comparison ROMs, never production translations."""

import argparse
import json
from pathlib import Path

from aflib import CODE_VROM, by_vrom, replace_dma, sha256, verified_rom
from build import apply_translations
from font import ATLAS_OFFSET, ATLAS_SIZE, FONT_VROM, make_halfwidth, pixels, png_gray
from textbanks import banks
from textcodec import command_info, decode, encode, tokenize

PROBE = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
         "abcdefghijklmnopqrstuvwxyz\n"
         "0123456789 .,!?'+-()\n"
         "I i l ' I i l ' PPP QQQ WWW")


def probe_entry(original, info):
    first_wait = next(t.offset for t in tokenize(original, info) if t.data == b"\x7f\x04")
    controls = b"".join(t.data for t in tokenize(original[:first_wait], info) if t.kind != "text")
    return encode(PROBE, info)+controls+original[first_wait:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a fresh directory")
    rom = verified_rom(args.rom.read_bytes())
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    original = next(b for b in banks(rom) if b.name == "message").entries()[0x9C7]
    edit = {"id": "message:09C7", "source_sha256": sha256(original),
            "translation": decode(probe_entry(original, info), info),
            "status": "diagnostic-only", "provenance": "Original renderer test text"}
    args.output.mkdir(parents=True)
    edits = args.output/"probe.json"
    edits.write_text(json.dumps([edit], indent=2, ensure_ascii=False)+"\n")
    reports = []
    for padding in (0, 1):
        replacements, report = make_halfwidth(rom, left_padding=padding)
        _, relocations = apply_translations(rom, replacements, edits)
        output = replace_dma(rom, replacements, relocations)
        target = args.output/f"padding-{padding}.z64"
        target.write_bytes(output)
        atlas = pixels(replacements[FONT_VROM][ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        (args.output/f"padding-{padding}.png").write_bytes(png_gray(192, 256, [p*17 for p in atlas]))
        report.update(rom=target.name, output_sha256=sha256(output), diagnostic_only=True)
        reports.append(report)
    (args.output/"report.json").write_text(json.dumps(reports, indent=2)+"\n")
    print(json.dumps({"output": str(args.output), "variants": len(reports)}))


if __name__ == "__main__":
    main()
