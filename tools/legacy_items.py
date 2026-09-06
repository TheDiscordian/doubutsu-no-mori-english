"""Recover the supplied legacy item-bank layout from its actual loader tables."""

import struct

from aflib import CODE_RAM, sha256, u32

LEGACY_CODE_SHA256 = "f5ec79a742ac3555b99c8c8588f950a4e98bb0e8f81b5382c73556d7f8bed742"
ITEM_VROM = 0x10F4000


def layout(code, data):
    if sha256(code) != LEGACY_CODE_SHA256:
        raise ValueError("Unknown legacy item-loader code")
    tables = [u32(code, 0x8009E418-CODE_RAM+n*4)-ITEM_VROM for n in range(16)]
    starts = [u32(code, 0x8009E468-CODE_RAM+n*4)-ITEM_VROM for n in range(16)]
    counts = list(code[0x8009E458-CODE_RAM:0x8009E468-CODE_RAM])
    def address(at):
        return ((u32(code, at-CODE_RAM) & 0xFFFF) << 16) | (u32(code, at+4-CODE_RAM) & 0xFFFF)
    tables.append(address(0x8009E3C0)-ITEM_VROM)
    starts.append(address(0x8009E3CC)-ITEM_VROM)
    counts.append(u32(code, 0x8009E3DC-CODE_RAM) & 0xFFFF)
    if len(set(starts)) != 17 or starts != sorted(starts):
        raise ValueError("Legacy item data banks overlap or are unordered")
    result = []
    for group, table, start, end, count in zip([*range(0x20, 0x30), 0x10], tables, starts,
                                               [*starts[1:], len(data)], counts):
        size = 4*(count+1)
        if not (count > 0 and 0 <= table < table+size <= starts[0] and 0 <= start < end <= len(data)):
            raise ValueError("Legacy item table or data bounds are invalid")
        offsets = [n[0] for n in struct.iter_unpack(">I", data[table:table+size])]
        if offsets[-1] or any(not 0 < n <= end-start for n in offsets[:-1]) or offsets[:-1] != sorted(offsets[:-1]):
            raise ValueError("Legacy item cumulative offsets are invalid")
        result.append((group, table, size, start, end, count))
    spans = sorted((table, table+size) for _, table, size, _, _, _ in result)
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("Legacy item tables overlap")
    return result
