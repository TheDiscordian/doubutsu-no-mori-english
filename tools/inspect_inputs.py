#!/usr/bin/env python3
"""Verify source input, recover the legacy UPS, and inspect actual DMA files."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_VROM, apply_ups, by_vrom, dma_entries, n64_checksum,
                   read_varint, sha256, verified_rom, yaz0_decode)


def inspect(rom, dest):
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for entry in dma_entries(rom):
        row = asdict(entry)
        if entry.pstart != 0xFFFFFFFF:
            try:
                data = entry.extract(rom)
                row["sha256"] = sha256(data)
            except ValueError as exc:
                row["error"] = str(exc)
                if entry.pend:
                    row["yaz0_size"] = len(yaz0_decode(rom[entry.pstart:entry.pend]))
        rows.append(row)
    entry = by_vrom(rom)[CODE_VROM]
    code = (yaz0_decode(rom[entry.pstart:entry.pend]) if entry.pend
            else entry.extract(rom))
    (dest / "code.bin").write_bytes(code)
    (dest / "dma.json").write_text(json.dumps(rows, indent=2) + "\n")
    return {"sha256": sha256(rom), "size": len(rom), "dma_entries": len(rows),
            "dma_errors": [r for r in rows if "error" in r],
            "code_size": len(code), "header_crc": list(struct.unpack_from(">2I", rom, 16)),
            "calculated_crc": list(n64_checksum(rom))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--legacy-ups", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/inspect"))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    patch = args.legacy_ups.read_bytes()
    size, _ = read_varint(patch, 4, len(patch)-12)
    if size != 0x2000000:
        raise ValueError("Unexpected legacy UPS source size")
    legacy = apply_ups(rom.ljust(size, b"\0"), patch)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "legacy.z64").write_bytes(legacy)
    report = {"original": inspect(rom, args.output / "original"),
              "legacy": inspect(legacy, args.output / "legacy"),
              "ups_sha256": sha256(patch), "ups_crc32": f"{zlib.crc32(patch):08x}"}
    (args.output / "inputs.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
