"""Resident-module contracts, watchdog relocation checks, and guarded bootstrap."""

import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, dma_entries, sha256
from english_runtime import GuardedCode, SOURCE_HASHES
from textcodec import command_info

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
COMMAND_HOOKS = {0x8009034C: "af_code_size", 0x800903CC: "af_code_attribute",
                 0x800A21C0: "af_dispatch_command", 0x800A054C: "af_cancel_order"}
HOOK_REGIONS = ((WATCHDOG_START, WATCHDOG_END), (0x8009034C, 0x800903A8),
                (0x800903CC, 0x800903E4), (0x800A21C0, 0x800A223C),
                (0x800A054C, 0x800A05A8), (0x800A22A4, 0x800A231C))


def module_command_info(rom):
    """Only implemented extension codes are tokenizable; gaps remain invalid."""
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    info += [(0, 0)]*(0x77-len(info))
    info[0x72] = info[0x73] = (2, 0)
    info[0x75] = (2, 0)
    info[0x76] = (2, 2)
    return info


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
    """Preserved entries must not have external callers bypassing their hooks.

    Literal aligned code pointers are checked in all files. J/JAL decoding is
    restricted to pinned code-segment definitions: audio and graphics data can
    contain words resembling instructions but are not executed by the CPU.
    """
    references = []
    executable, definitions = set(), {}
    root = Path(__file__).resolve().parents[1]/"upstream/af/yamls/jp"
    for name in ("makerom.yaml", "boot.yaml", "code.yaml", "overlays.yaml"):
        content = (root/name).read_text()
        definitions[name] = sha256(content.encode())
        for block in re.split(r"(?m)^  - name: ", content)[1:]:
            if re.search(r"(?m)^    type: code\s*$", block):
                match = re.search(r"(?m)^    start: (0x[0-9A-Fa-f]+)\s*$", block)
                if not match:
                    raise ValueError("Unexpected pinned executable-segment definition")
                executable.add(int(match[1], 16))
    if CODE_VROM not in executable or len(executable) < 100:
        raise ValueError("Incomplete pinned executable-segment inventory")
    for entry in dma_entries(rom):
        if entry.pstart == 0xFFFFFFFF:
            continue
        data = entry.extract(rom)
        for offset in range(0, len(data)-3, 4):
            pc = CODE_RAM+offset if entry.vstart == CODE_VROM else None
            if pc is not None and any(start <= pc < end for start, end in HOOK_REGIONS):
                continue
            word = struct.unpack_from(">I", data, offset)[0]
            op = word >> 26
            targets = [word] if word % 4 == 0 else []
            if entry.vstart in executable and op in (2, 3):
                targets.append(0x80000000 | ((word & 0x3FFFFFF) << 2))
            if pc is not None and (op in (1, 4, 5, 6, 7, 20, 21, 22, 23)
                                   or op == 17 and (word >> 21) & 31 == 8):
                immediate = (word & 0xFFFF) - (0x10000 if word & 0x8000 else 0)
                targets.append(pc+4+immediate*4)
            if any(start < target < end for target in targets for start, end in HOOK_REGIONS):
                references.append((entry.vstart, offset))
    if references:
        raise ValueError(f"External replaced-function-interior references: {references}")
    return {"watchdog_bytes": len(watchdog_bytes(rom)), "external_interior_references": [],
            "guarded_function_regions": [[f"{start:08X}", f"{end:08X}"] for start, end in HOOK_REGIONS],
            "executable_segments": len(executable), "definition_sha256": definitions}


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
    for address, symbol in COMMAND_HOOKS.items():
        target = int(report["symbols"][symbol], 16)
        if not MODULE_INIT <= target < MODULE_RAM+used or target % 4:
            raise ValueError("Invalid module command-handler address")
        code.write(address, struct.pack(">2I", 0x08000000 | ((target & 0x0FFFFFFF) >> 2), 0))
    def call(symbol):
        target = int(report["symbols"][symbol], 16)
        if not MODULE_INIT <= target < MODULE_RAM+used or target % 4:
            raise ValueError("Invalid module pacing-helper address")
        return 0x0C000000 | ((target & 0x0FFFFFFF) >> 2)
    code.instruction(0x800A2274, 0x0C01E36B, call("af_fast_button"))
    code.instruction(0x800A2278, 0x24044000, 0x02002025)  # a0 = window, not BUTTON_B
    timer = struct.pack(">7I", call("af_cursor_timer"), 0x02002025,
                        0x26110294, 0x24120001, 0x240D0003, 0x080288C7, 0)
    code.write(0x800A22A4, timer.ljust(0x78, b"\0"))
    code.instruction(0x800A0720, 0, 0x240A0100)
    code.instruction(0x800A0730, 0x31090100, 0x31094100)
    code.instruction(0x800A0734, 0x11200006, 0x152A0006)
    code.immediate(0x8009E8A4, 0xFF3F, 0xBF3F)
    replacements[CODE_VROM] = bytes(code.data)
    report["date_scope"] = "Seven message substitutions; other UI formatter callers remain native"
    report["code_changes"] = code.changes
    return {MODULE_VROM: data}, report


def verify_runtime_module(rom, replacements, additions, directory):
    """Text extensions require every module patch and the exact added DMA data."""
    expected_code = {}
    expected_data, report = add_runtime_module(rom, expected_code, directory)
    if additions != expected_data or CODE_VROM not in replacements:
        raise ValueError("English text extensions require the complete resident module")
    current = replacements[CODE_VROM]
    for change in report["code_changes"]:
        offset = int(change["ram"], 16)-CODE_RAM
        end = offset+change["bytes"]
        if current[offset:end] != expected_code[CODE_VROM][offset:end]:
            raise ValueError(f"Missing resident module patch at {change['ram']}")
