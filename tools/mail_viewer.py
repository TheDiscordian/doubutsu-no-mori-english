"""Verified native mail-viewer destinations; no wider viewer is installed here."""

import struct

from aflib import by_vrom, sha256

VROM = 0x007908A0
RAM = 0x80888E90
FILE_SHA256 = "abade0c99f31b39b2a2b0b80c3ad1557ba5d9aadf1b10b512a662a4b76b3cbad"
STATE_TABLE_RAM = 0x8088ABA4
STATE_HANDLERS = (0x8088910C, 0x8088920C, 0x8088913C, 0x80889288, 0x808894E4)
GUARDS = {
    0x80889154: 0x304ED000,  # read wait: A/B/START trigger mask
    0x80889170: 0x8F3906B0,  # shared menu transition callback
    0x80889174: 0x24050004,  # move out through the top
    0x80889318: 0x26050008,  # edit acceptance source: embedded Mail_c
    0x80889324: 0x0C02719F,  # edit acceptance copies to persistent destination
    0x80889328: 0x8E0400AC,  # persistent destination pointer
    0x808893DC: 0x8FA20050,  # saved header preference pointer
    0x808893E0: 0x9219002F,  # copying the local header split into saved preferences
    0x808893EC: 0xA0590000,
    0x808894F8: 0x8F3906AC,  # shared end callback
    0x8088954C: 0x8CAE0004,  # board procedure-state index
    0x80889558: 0x8F39ABA4,  # state-handler table lookup
    0x8088A788: 0xAC2006E4,  # destructor clears only the board pointer
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
FUNCTIONS = {"read_wait": (0x8088913C, 0x80889198),
             "edit_acceptance": (0x80889288, 0x808894E4),
             "end_callback": (0x808894E4, 0x80889514),
             "state_dispatch": (0x80889514, 0x80889574),
             "destruct": (0x8088A77C, 0x8088A794),
             "footer_draw": (0x808899E4, 0x80889A9C),
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
    if struct.unpack_from('>5I', data, STATE_TABLE_RAM-RAM) != STATE_HANDLERS:
        raise ValueError('Native mail-viewer state table changed')
    return {"vrom": f"{VROM:08X}", "linked_ram": f"{RAM:08X}", "file_sha256": FILE_SHA256,
            "bytes": len(data), "board_pointer_offset_in_overlay": 0x106E4,
            "board_bytes": 0xC0, "embedded_mail_offset": 8,
            "length_offsets": {"header": 5, "body": 6, "footer": 7},
            "text_offsets": {"header": 0x32, "body": 0x3C, "footer": 0x9C},
            "persistent_mail_pointer_offset": 0xAC, "header_split_offset": 0x2F,
            "line_character_limit": 16, "body_lines": 6, "read_mode": 1,
            "state_table_ram": f"{STATE_TABLE_RAM:08X}",
            "state_handlers": {str(i): f"{address:08X}" for i, address in enumerate(STATE_HANDLERS)},
            "read_wait_state": 2, "edit_acceptance_state": 3,
            "read_close_trigger_mask": "D000",
            "shared_callback_offsets": {"transition": 0x106B0, "end": 0x106AC},
            "instruction_guards": {f"{address:08X}": f"{word:08X}" for address, word in GUARDS.items()},
            "functions": {name: {"start": f"{start:08X}", "end": f"{end:08X}",
                                  "sha256": sha256(data[start-RAM:end-RAM])}
                          for name, (start, end) in FUNCTIONS.items()},
            "status": "Native viewer bounds and local state paths only; shared callbacks, opening callers, wider readers, discrimination, editing, and persistence require integration/validation"}
