"""Text bank layouts. Tables hold cumulative end offsets, terminated by zero."""

from dataclasses import dataclass
import struct

from aflib import by_vrom


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

    def rebuild(self, entries):
        old = self.entries()
        if len(entries) != len(old):
            raise ValueError(f"{self.name}: entry count change is not supported")
        if self.fixed_size:
            if any(len(e) != self.fixed_size for e in entries):
                raise ValueError(f"{self.name}: fixed entry size changed")
            return b"".join(entries), None
        data = b"".join(entries)
        if len(data) > len(self.data):
            raise ValueError(f"{self.name}: bank capacity exceeded ({len(data)} > {len(self.data)})")
        table = bytearray(self.table)
        offset = 0
        for index, entry in enumerate(entries):
            offset += len(entry)
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
    # The legacy file includes trailing alignment after 238 names.
    result.append(Bank("npc_names", vrom, None, file[8:8+238*width], None,
                       fixed_size=width, data_offset=8))
    return result
