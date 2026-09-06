"""Text bank layouts. Tables hold cumulative end offsets, terminated by zero."""

from dataclasses import dataclass
import struct

from aflib import CODE_VROM, by_vrom
from legacy_items import layout as legacy_item_layout


@dataclass
class Bank:
    name: str
    data_vrom: int
    table_vrom: int | None
    data: bytes
    table: bytes | None
    fixed_size: int = 0
    data_offset: int = 0
    table_offset: int = 0

    def entries(self):
        if self.fixed_size:
            if len(self.data) % self.fixed_size:
                raise ValueError(f"{self.name}: partial fixed-size entry")
            return [self.data[i:i+self.fixed_size]
                    for i in range(0, len(self.data), self.fixed_size)]
        result, start = [], 0
        if self.table is None:
            raise ValueError("Missing text table")
        for (end,) in struct.iter_unpack(">I", self.table[:len(self.table)//4*4]):
            if end == 0:
                return result
            if not start <= end <= len(self.data):
                raise ValueError(f"{self.name}: invalid end offset {end:#x}, after {start:#x}")
            result.append(self.data[start:end])
            start = end
        return result

    def rebuild(self, entries, allow_expand=False):
        old = self.entries()
        if len(entries) != len(old):
            raise ValueError(f"{self.name}: entry count change is not supported")
        if self.fixed_size:
            if any(len(e) != self.fixed_size for e in entries):
                raise ValueError(f"{self.name}: fixed entry size changed")
            return b"".join(entries), None
        data = b"".join(entries)
        if len(data) > len(self.data) and not allow_expand:
            raise ValueError(f"{self.name}: bank capacity exceeded ({len(data)} > {len(self.data)})")
        table = bytearray(self.table)
        offset = 0
        for index, entry in enumerate(entries):
            offset += len(entry)
            if offset == 0:
                raise ValueError(f"{self.name}: empty leading entry would become a bank terminator")
            struct.pack_into(">I", table, index*4, offset)
        # Preserve original unused bytes for exact no-change round trips.
        return data + self.data[len(data):], bytes(table)


def banks(rom, legacy=False):
    files = by_vrom(rom)
    def extract(vrom):
        return files[vrom].extract(rom)
    specs = [
        ("message", 0xBD4000, 0xCF9000, 0x1914000, 0xCF9000),
        ("select", 0xD05000, 0xD06000, 0x1BA5000, 0xD09000),
        ("mail", 0xD07000, 0xD10000, 0x1BA7000, 0xD10000),
        ("super", 0xD11000, 0xD12000, 0x1BC7000, 0xD12000),
        ("ps", 0xD13000, 0xD15000, 0x1BCA000, 0xD15000),
        ("string", 0xD16000, 0xD18000, 0x1BCE000, 0xD18000),
    ]
    result = []
    for name, dv, tv, ldv, ltv in specs:
        if legacy:
            dv, tv = ldv, ltv
        result.append(Bank(name, dv, tv, extract(dv), extract(tv)))
    # NPC letter components share one DMA file.
    if legacy:
        vrom = 0x1BD3000
        bounds = [0, 0x5000, 0xC000, 0xF000, 0x10000, 0x11000]
        table_start = 0x11000
    else:
        vrom = 0xD1A000
        bounds = [0, 0x26F0, 0x63E0, 0x7860, 0x80D0, 0x8B20]
        table_start = 0x8B20
    file = extract(vrom)
    for i, name in enumerate(("maila", "mailb", "mailc", "psz", "superz")):
        ts = table_start + i*0x610
        result.append(Bank(name, vrom, vrom, file[bounds[i]:bounds[i+1]],
                           file[ts:ts+0x610], data_offset=bounds[i], table_offset=ts))
    vrom, width = (0x1BE6000, 8) if legacy else (0xE04000, 6)
    file = extract(vrom)
    # Retain every complete storage slot, including reserved/alignment slots.
    # This is not a count of villagers: the retail actor table has 216 NPCs.
    end = 8 + (len(file)-8)//width*width
    result.append(Bank("npc_names", vrom, None, file[8:end], None,
                       fixed_size=width, data_offset=8))
    vrom = 0x10F4000
    file = extract(vrom)
    if legacy:
        # The shipped loader is the authority; archived offset notes are stale.
        # Furniture has one record per four native rotation IDs.
        for group, ts, size, start, end, _ in legacy_item_layout(extract(CODE_VROM), file):
            result.append(Bank(f"item_{group:02X}", vrom, vrom,
                               file[start:end], file[ts:ts+size],
                               data_offset=start, table_offset=ts))
    else:
        ranges = [(8, 0x288), (0x288, 0x2B0), (0x2B0, 0x418), (0x418, 0x558),
                  (0x558, 0xF50), (0xF50, 0x107C), (0x107C, 0x12FC),
                  (0x12FC, 0x157C), (0x157C, 0x15C2), (0x15C4, 0x1628),
                  (0x1628, 0x1850), (0x1850, 0x185A), (0x185C, 0x1C1C),
                  (0x1C1C, 0x1D5C), (0x1D5C, 0x1D70), (0x1D70, 0x1D98),
                  (0x1D98, 0x1D98+(len(file)-0x1D98)//10*10)]
        for group, (start, end) in zip([*range(0x20, 0x30), 0x10], ranges):
            # Sub-banks have 0–3 alignment bytes before the next group.
            end = start+(end-start)//10*10
            result.append(Bank(f"item_{group:02X}", vrom, None, file[start:end], None,
                               fixed_size=10, data_offset=start))
    return result
