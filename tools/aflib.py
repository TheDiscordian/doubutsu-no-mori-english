"""Strict binary primitives for the Japanese N64 release (standard library only)."""

from dataclasses import dataclass
import hashlib
import struct
import zlib

ROM_SHA256 = "d9417be056534fcc0bdff2e6cd5f1135511be7c0a4dace04a96a2649596ce908"
DMA_START = 0x19D50
DMA_END = 0x27130
CODE_VROM = 0x675720
CODE_RAM = 0x80051A80
MAX_ROM = 64 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def u32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]


def normalise_rom(data):
    if len(data) < 64 or len(data) % 4:
        raise ValueError("ROM must contain a header and complete 32-bit words")
    if data[:4] == bytes.fromhex("37804012"):
        out = bytearray(len(data))
        out[::2], out[1::2] = data[1::2], data[::2]
        data = bytes(out)
    elif data[:4] == bytes.fromhex("40123780"):
        out = bytearray(len(data))
        for i in range(4):
            out[i::4] = data[3-i::4]
        data = bytes(out)
    elif data[:4] != bytes.fromhex("80371240"):
        raise ValueError("Unknown ROM byte order")
    return data


def verified_rom(data):
    data = normalise_rom(data)
    if sha256(data) != ROM_SHA256:
        raise ValueError("Unsupported source ROM: SHA-256 does not match Japanese retail")
    return data


def yaz0_decode(data):
    if len(data) < 16 or data[:4] != b"Yaz0":
        raise ValueError("Invalid Yaz0 header")
    size = u32(data, 4)
    if size > MAX_ROM:
        raise ValueError("Unreasonable Yaz0 output size")
    out, pos = bytearray(), 16
    while len(out) < size:
        if pos >= len(data):
            raise ValueError("Truncated Yaz0 control byte")
        control = data[pos]
        pos += 1
        for bit in range(7, -1, -1):
            if len(out) == size:
                break
            if control & (1 << bit):
                if pos >= len(data):
                    raise ValueError("Truncated Yaz0 literal")
                out.append(data[pos])
                pos += 1
            else:
                if pos + 2 > len(data):
                    raise ValueError("Truncated Yaz0 back-reference")
                first, second = data[pos:pos+2]
                pos += 2
                distance = ((first & 15) << 8 | second) + 1
                length = first >> 4
                if length == 0:
                    if pos >= len(data):
                        raise ValueError("Truncated Yaz0 extended length")
                    length = data[pos] + 0x12
                    pos += 1
                else:
                    length += 2
                if distance > len(out) or len(out) + length > size:
                    raise ValueError("Invalid Yaz0 copy bounds")
                for _ in range(length):
                    out.append(out[-distance])
    return bytes(out)


@dataclass(frozen=True)
class DmaEntry:
    index: int
    vstart: int
    vend: int
    pstart: int
    pend: int

    @property
    def size(self):
        return self.vend - self.vstart

    def extract(self, rom):
        if self.pstart == 0xFFFFFFFF:
            raise ValueError("Cannot extract a RAM-only DMA entry")
        end = self.pend or (self.pstart + self.size)
        if not 0 <= self.pstart <= end <= len(rom):
            raise ValueError(f"DMA {self.index} exceeds ROM bounds")
        data = rom[self.pstart:end]
        data = yaz0_decode(data) if self.pend else data
        if len(data) != self.size:
            raise ValueError(f"DMA {self.index} decompressed size mismatch")
        return data


def dma_entries(rom):
    entries = []
    for offset in range(DMA_START, min(DMA_END, len(rom)), 16):
        row = struct.unpack_from(">4I", rom, offset)
        if row == (0, 0, 0, 0):
            break
        entry = DmaEntry((offset-DMA_START)//16, *row)
        if entry.vend < entry.vstart:
            raise ValueError(f"Invalid DMA range at {offset:#x}")
        entries.append(entry)
    if not entries:
        raise ValueError("Missing DMA table")
    return entries


def by_vrom(rom):
    return {e.vstart: e for e in dma_entries(rom)}


def read_varint(data, pos, end):
    value, shift = 0, 1
    for _ in range(10):
        if pos >= end:
            raise ValueError("Truncated patch integer")
        x = data[pos]
        pos += 1
        value += (x & 127) * shift
        if x & 128:
            return value, pos
        shift <<= 7
        value += shift
    raise ValueError("Oversized patch integer")


def varint(value):
    if value < 0:
        raise ValueError("Negative patch integer")
    out = bytearray()
    while True:
        x = value & 127
        value >>= 7
        if not value:
            return bytes(out + bytes([x | 128]))
        out.append(x)
        value -= 1


def apply_ups(source, patch):
    if len(patch) < 18 or patch[:4] != b"UPS1":
        raise ValueError("Invalid UPS header")
    src_crc, dst_crc, patch_crc = struct.unpack_from("<3I", patch, len(patch)-12)
    if zlib.crc32(patch[:-4]) != patch_crc:
        raise ValueError("UPS patch CRC mismatch")
    src_size, pos = read_varint(patch, 4, len(patch)-12)
    dst_size, pos = read_varint(patch, pos, len(patch)-12)
    if len(source) != src_size or zlib.crc32(source) != src_crc:
        raise ValueError("UPS source size or CRC mismatch")
    if max(src_size, dst_size) > MAX_ROM:
        raise ValueError("UPS output exceeds project ROM limit")
    out = bytearray(source.ljust(max(src_size, dst_size), b"\0"))
    address = 0
    while pos < len(patch)-12:
        delta, pos = read_varint(patch, pos, len(patch)-12)
        address += delta
        while True:
            if pos >= len(patch)-12:
                raise ValueError("Unterminated UPS XOR run")
            x = patch[pos]
            pos += 1
            if x == 0:
                address += 1
                break
            if address >= len(out):
                raise ValueError("UPS XOR outside output")
            out[address] ^= x
            address += 1
    result = bytes(out[:dst_size])
    if zlib.crc32(result) != dst_crc:
        raise ValueError("UPS output CRC mismatch")
    return result


def make_ups(source, target):
    """Make an ordinary reversible UPS patch with CRCs for both ROMs."""
    if max(len(source), len(target)) > MAX_ROM:
        raise ValueError("UPS inputs exceed project ROM limit")
    size = max(len(source), len(target))
    a, b = source.ljust(size, b"\0"), target.ljust(size, b"\0")
    out = bytearray(b"UPS1" + varint(len(source)) + varint(len(target)))
    pos, previous = 0, 0
    while pos < size:
        if a[pos] == b[pos]:
            pos += 1
            continue
        out.extend(varint(pos-previous))
        while pos < size and a[pos] != b[pos]:
            out.append(a[pos] ^ b[pos])
            pos += 1
        out.append(0)
        pos += 1
        previous = pos
    out.extend(struct.pack("<2I", zlib.crc32(source), zlib.crc32(target)))
    out.extend(struct.pack("<I", zlib.crc32(out)))
    return bytes(out)


def n64_checksum(rom):
    """CIC 6102/7101 checksum, verified against this game's retail IPL3."""
    if len(rom) < 0x101000:
        raise ValueError("ROM too short for CIC checksum")
    mask = 0xFFFFFFFF
    t1 = t2 = t3 = t4 = t5 = t6 = 0xF8CA4DDC
    for offset in range(0x1000, 0x101000, 4):
        d = u32(rom, offset)
        total = (t6 + d) & mask
        if total < t6:
            t4 = (t4 + 1) & mask
        t6 = total
        t3 ^= d
        shift = d & 31
        r = ((d << shift) | (d >> ((32-shift) & 31))) & mask
        t5 = (t5 + r) & mask
        t2 ^= r if t2 > d else t6 ^ d
        t1 = (t1 + (t5 ^ d)) & mask
    return (t6 ^ t4 ^ t3, t5 ^ t2 ^ t1)


def fix_checksum(rom):
    struct.pack_into(">2I", rom, 0x10, *n64_checksum(rom))


def replace_dma(rom, replacements, relocations=None, additions=None):
    """Append replacement files; keep VROM identity and all original file ranges."""
    entries = by_vrom(rom)
    relocations = relocations or {}
    additions = additions or {}
    out = bytearray(rom)
    for vrom, data in sorted(replacements.items()):
        entry = entries[vrom]
        if len(data) != entry.size and vrom not in relocations:
            raise ValueError(f"DMA size change requires a separate VROM relocation: {vrom:#x}")
        out.extend(b"\0" * (-len(out) % 16))
        start = len(out)
        out.extend(data)
        struct.pack_into(">2I", out, DMA_START + entry.index*16 + 8, start, 0)
        if vrom in relocations:
            new_vrom = relocations[vrom]
            struct.pack_into(">2I", out, DMA_START+entry.index*16, new_vrom, new_vrom+len(data))
    next_index = len(entries)
    for vrom, data in sorted(additions.items()):
        row = DMA_START+next_index*16
        if (vrom in entries or not data or vrom % 16 or len(data) % 16
                or vrom < 0 or vrom+len(data) > MAX_ROM):
            raise ValueError("Invalid new DMA file")
        if row+32 > DMA_END or out[row:row+32] != bytes(32):
            raise ValueError("No unused DMA row and terminator available")
        out.extend(bytes(-len(out) % 16))
        start = len(out)
        out.extend(data)
        struct.pack_into(">4I", out, row, vrom, vrom+len(data), start, 0)
        next_index += 1
    intervals = sorted((e.vstart, e.vend) for e in dma_entries(out) if e.pstart != 0xFFFFFFFF)
    if any(right[0] < left[1] for left, right in zip(intervals, intervals[1:])):
        raise ValueError("Relocated virtual DMA ranges overlap")
    target_size = 1 << (len(out)-1).bit_length()
    if target_size > MAX_ROM:
        raise ValueError("ROM exceeds 64 MiB")
    out.extend(b"\0" * (target_size-len(out)))
    fix_checksum(out)
    return bytes(out)
