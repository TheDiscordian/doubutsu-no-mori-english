#!/usr/bin/env python3
"""Inventory embedded N64 keyboard text and graphic labels without exporting assets."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from keyboard import LABELS, LABELS_VROM, LEDIT_RAM, LEDIT_VROM, TITLES, validate_label_layout
from textcodec import command_info, decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/inventory/keyboard-ui.json"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    files = by_vrom(rom)
    info = command_info(files[CODE_VROM].extract(rom))
    window = files[LEDIT_VROM].extract(rom)
    graphics = files[LABELS_VROM].extract(rom)
    validate_label_layout(graphics)
    rows = []
    for index, title in enumerate(TITLES):
        pointer, length, maximum = struct.unpack_from(">3I", window, 0xA28+index*40)
        offset = pointer-LEDIT_RAM
        source = window[offset:offset+length]
        rows.append({"id": f"ui_name_entry:{index:04X}", "vrom": f"{LEDIT_VROM:08X}",
                     "offset": f"{offset:04X}", "source_sha256": sha256(source),
                     "source": decode(source, info), "translation": title,
                     "input_limit": maximum, "kind": "embedded_text"})
    rows.append({"id": "ui_name_entry:0005", "vrom": f"{LEDIT_VROM:08X}",
                 "offset": "0AF4", "source_sha256": sha256(window[0xAF4:0xAF7]),
                 "source": decode(window[0xAF4:0xAF7], info), "translation": "town",
                 "kind": "embedded_text"})
    for index, (offset, width, height, fmt, label) in enumerate(LABELS):
        size = width*height//2 if fmt == "I4" else width*height
        rows.append({"id": f"ui_keyboard_label:{index:04X}", "vrom": f"{LABELS_VROM:08X}",
                     "offset": f"{offset:05X}", "source_sha256": sha256(graphics[offset:offset+size]),
                     "translation": label, "size": [width, height], "format": fmt,
                     "kind": "texture_text"})
    report = {"scope": "name-entry prompts, destination suffix, and keyboard labels only",
              "implementation": "tools/keyboard.py", "entries": rows,
              "review": "Implemented; runtime coverage is recorded separately in docs/VALIDATION.md"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(f"Inventoried {len(rows)} keyboard UI entries: {args.output}")


if __name__ == "__main__":
    main()
