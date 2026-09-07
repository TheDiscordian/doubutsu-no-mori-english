"""Native mail has its own substitution table, not the main message dispatcher."""

import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

BANKS = frozenset(("super", "mail", "ps", "superz", "maila", "mailb", "mailc", "psz"))
NATIVE_CODES = frozenset(range(0x24, 0x2E)) | frozenset(range(0x36, 0x40))
TABLE_RAM = 0x80107020
TABLE_SHA256 = "5d956ef287b35240a4f6e09028618e43fe701b87ed8386b0b7f45cd35ba5700c"


def native_handlers(rom):
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    data = code[TABLE_RAM-CODE_RAM:TABLE_RAM-CODE_RAM+97*4]
    if sha256(data) != TABLE_SHA256:
        raise ValueError("Unexpected native mail substitution table")
    handlers = {i: value for i, (value,) in enumerate(struct.iter_unpack(">I", data)) if value}
    if handlers.keys() != NATIVE_CODES:
        raise ValueError("Native mail opcode inventory differs from the validator")
    return handlers


def validate_tokens(tokens):
    for token in tokens:
        if token.kind == "cmd" and token.data[1] not in NATIVE_CODES:
            raise ValueError("Unsupported native mail command; main-dialogue capability does not apply")
