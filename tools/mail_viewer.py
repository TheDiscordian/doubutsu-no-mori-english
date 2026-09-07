"""Verified native mail-viewer destinations; no wider viewer is installed here."""

import struct

from aflib import by_vrom, sha256

VROM = 0x007908A0
RAM = 0x80888E90
FILE_SHA256 = "abade0c99f31b39b2a2b0b80c3ad1557ba5d9aadf1b10b512a662a4b76b3cbad"
GUARDS = {
    0x80889B3C: 0x2455003C,  # body pointer: board + 3C
    0x80889B40: 0x90510006,  # body length: board + 06
    0x80889B70: 0x2A010010,  # sixteen characters per line
    0x80889C80: 0x24010006,  # six lines
    0x80889A74: 0x2445009C,  # footer pointer: board + 9C
    0x8088A300: 0x8E1006E4,  # board pointer: overlay + 106E4
    0x8088A334: 0xAE1900AC,  # persistent source/destination: board + AC
    0x8088A47C: 0x0C02719F,  # native mail copy on non-new entry
    0x8088A49C: 0x15380006,  # mode one selects the read-only branch
    0x8088A4A8: 0xAC790030,  # read mode selects wait state two
    0x8088A4F8: 0x2405000A,  # header length scan: ten
    0x8088A50C: 0x24050010,  # footer length scan: sixteen
    0x8088A520: 0x24050060,  # body length scan: 96
    0x8088A538: 0x2861000B,  # clamp header split values above ten
    0x8088A54C: 0xA20F002F,  # overwrite clamped split in local mail copy
}
FUNCTIONS = {"footer_draw": (0x808899E4, 0x80889A9C),
             "body_draw": (0x80889A9C, 0x80889CD8),
             "header_draw": (0x80889CD8, 0x80889FB0),
             "initialize": (0x8088A2D0, 0x8088A604)}


def evidence(rom):
    data = by_vrom(rom)[VROM].extract(rom)
    if sha256(data) != FILE_SHA256:
        raise ValueError("Unexpected native mail-viewer overlay")
    for address, word in GUARDS.items():
        if struct.unpack_from(">I", data, address-RAM)[0] != word:
            raise ValueError("Native mail-viewer instruction guard failed")
    return {"vrom": f"{VROM:08X}", "linked_ram": f"{RAM:08X}", "file_sha256": FILE_SHA256,
            "bytes": len(data), "board_pointer_offset_in_overlay": 0x106E4,
            "board_bytes": 0xC0, "embedded_mail_offset": 8,
            "length_offsets": {"header": 5, "body": 6, "footer": 7},
            "text_offsets": {"header": 0x32, "body": 0x3C, "footer": 0x9C},
            "persistent_mail_pointer_offset": 0xAC, "header_split_offset": 0x2F,
            "line_character_limit": 16, "body_lines": 6, "read_mode": 1,
            "instruction_guards": {f"{address:08X}": f"{word:08X}" for address, word in GUARDS.items()},
            "functions": {name: {"start": f"{start:08X}", "end": f"{end:08X}",
                                  "sha256": sha256(data[start-RAM:end-RAM])}
                          for name, (start, end) in FUNCTIONS.items()},
            "status": "Native viewer bounds only; wider text, opaque-record discrimination, and editor/exit paths require integration"}
