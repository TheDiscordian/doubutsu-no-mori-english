"""Resident-module contracts, watchdog relocation checks, and guarded bootstrap."""

import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, dma_entries, sha256
from english_runtime import GuardedCode, SOURCE_HASHES

MODULE_RAM = 0x801948E0
MODULE_VROM = 0x02800000
RESERVATION = 0x4000
WATCHDOG_START, WATCHDOG_END = 0x800D64E0, 0x800D66D0
BOOTSTRAP_RAM = WATCHDOG_START+16
WATCHDOG_COPY = MODULE_RAM+0x100
MODULE_INIT = MODULE_RAM+0x300
DATE_CALLS = (
    (0x8009EEA4, 0x800C4084, "af_format_year"),
    (0x8009EF2C, 0x800C40F8, "af_format_month"),
    (0x8009EFB4, 0x800C4168, "af_format_weekday"),
    (0x8009F03C, 0x800C41B8, "af_format_day"),
    (0x8009F0C4, 0x800C4228, "af_format_hour"),
    (0x8009F14C, 0x800C42E8, "af_format_minute"),
    (0x8009F1D4, 0x800C4350, "af_format_second"),
)


def watchdog_bytes(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    if sha256(code) != SOURCE_HASHES[CODE_VROM]:
        raise ValueError("Unexpected main code for watchdog relocation")
    data = code[WATCHDOG_START-CODE_RAM:WATCHDOG_END-CODE_RAM]
    for offset in range(0, len(data), 4):
        word = struct.unpack_from(">I", data, offset)[0]
        op = word >> 26
        if op in (2, 3):
            target = 0x80000000 | ((word & 0x3FFFFFF) << 2)
            if WATCHDOG_START <= target < WATCHDOG_END:
                raise ValueError("Watchdog has an unsupported internal absolute jump")
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23):
            immediate = (word & 0xFFFF) - (0x10000 if word & 0x8000 else 0)
            target = WATCHDOG_START+offset+4+immediate*4
            if not WATCHDOG_START <= target < WATCHDOG_END:
                raise ValueError("Watchdog has an unsupported external relative branch")
    return data


def audit_watchdog_references(rom):
    """The native entry remains; no external reference may enter its old body."""
    references = []
    for entry in dma_entries(rom):
        if entry.pstart == 0xFFFFFFFF:
            continue
        data = entry.extract(rom)
        for offset in range(0, len(data)-3, 4):
            pc = CODE_RAM+offset if entry.vstart == CODE_VROM else None
            if pc is not None and WATCHDOG_START <= pc < WATCHDOG_END:
                continue
            word = struct.unpack_from(">I", data, offset)[0]
            op = word >> 26
            targets = [word]
            if op in (2, 3):
                targets.append(0x80000000 | ((word & 0x3FFFFFF) << 2))
            if pc is not None and op in (1, 4, 5, 6, 7, 20, 21, 22, 23):
                immediate = (word & 0xFFFF) - (0x10000 if word & 0x8000 else 0)
                targets.append(pc+4+immediate*4)
            if any(WATCHDOG_START < target < WATCHDOG_END for target in targets):
                references.append((entry.vstart, offset))
    if references:
        raise ValueError(f"External watchdog-interior references: {references}")
    return {"watchdog_bytes": len(watchdog_bytes(rom)), "external_interior_references": []}


def add_runtime_module(rom, replacements, directory):
    report = json.loads((directory/"module.json").read_text())
    data = (directory/"module.bin").read_bytes()
    bootstrap = (directory/"bootstrap.bin").read_bytes()
    if (report["source_sha256"] != sha256(rom) or report["module_sha256"] != sha256(data)
            or report["bootstrap_sha256"] != sha256(bootstrap)):
        raise ValueError("Stale or corrupt resident-module artifacts")
    source = Path(__file__).resolve().parents[1]/"runtime"
    if set(report["runtime_sources"]) != {p.name for p in source.iterdir() if p.is_file()}:
        raise ValueError("Runtime module source inventory changed; rebuild the module")
    for name, digest in report["runtime_sources"].items():
        if Path(name).name != name or sha256((source/name).read_bytes()) != digest:
            raise ValueError("Runtime module sources changed; rebuild the module")
    if len(data) != RESERVATION or not 0 < len(bootstrap) <= WATCHDOG_END-BOOTSTRAP_RAM:
        raise ValueError("Resident module/bootstrap exceeds its reserved region")
    magic, abi, reserved, used = struct.unpack_from(">4I", data)
    if (magic, abi, reserved) != (0x41465254, 1, RESERVATION) or not 0x300 <= used <= RESERVATION-16:
        raise ValueError("Invalid resident-module header")
    if used != report["linked_bytes"] or data[used:] != bytes(RESERVATION-used):
        raise ValueError("Invalid resident-module linked size or zero padding")
    if data[0x100:0x2F0] != watchdog_bytes(rom):
        raise ValueError("Resident module does not preserve the watchdog")
    original = by_vrom(rom)[CODE_VROM].extract(rom)
    code = GuardedCode(original, replacements.get(CODE_VROM, original), CODE_RAM, SOURCE_HASHES[CODE_VROM])
    jump = struct.pack(">4I", 0x08000000 | ((WATCHDOG_COPY & 0x0FFFFFFF) >> 2), 0, 0, 0)
    patch = (jump+bootstrap).ljust(WATCHDOG_END-WATCHDOG_START, b"\0")
    code.write(WATCHDOG_START, patch)
    code.instruction(0x800D6720, 0x0C00AFDE, 0x0C000000 | ((BOOTSTRAP_RAM & 0x0FFFFFFF) >> 2))
    for address, original_target, symbol in DATE_CALLS:
        target = int(report["symbols"][symbol], 16)
        if not MODULE_INIT <= target < MODULE_RAM+used or target % 4:
            raise ValueError("Invalid module date-formatter address")
        code.instruction(address, 0x0C000000 | ((original_target & 0x0FFFFFFF) >> 2),
                         0x0C000000 | ((target & 0x0FFFFFFF) >> 2))
    # Both native locals have eight bytes before a command-length temporary.
    # English month/weekday names require nine. Move that temporary and incoming
    # arguments up eight bytes; saved registers and the array itself stay put.
    code.grow_stack(0x8009EF00, 0x8009EF88, 56, 0x34, growth=8)
    code.grow_stack(0x8009EF88, 0x8009F010, 56, 0x34, growth=8)
    replacements[CODE_VROM] = bytes(code.data)
    report["date_scope"] = "Seven message substitutions; other UI formatter callers remain native"
    report["code_changes"] = code.changes
    return {MODULE_VROM: data}, report
