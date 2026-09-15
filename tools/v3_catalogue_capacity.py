"""Expand the actual catalogue state while retaining native owner lifetimes."""
import struct

from aflib import sha256, u32
from catalogue_names import PREFIX, START, RAM

# A 1,584-byte page has 753 IDs, seven original ten-byte compatibility names,
# and the original eight-byte header. It covers the donor's 742-row furniture
# catalogue and keeps each page 16-byte aligned without growing either preview.
CAPACITY, PAGE_BYTES, NAME_OFFSET = 753, 1584, 1514
STATE_BYTES, GROWTH, TAIL_GROWTH, POOL_EXTRA = 18144, 5568, 5560, 6144
MULTIPLIERS = (
    (5, 9, (0x808A6AAC, 0x808A6AB8, 0x808A6ABC, 0x808A6AC4,
            0x808A6AC8, 0x808A6ACC, 0x808A6AD0)),
    (24, 15, (0x808A7060, 0x808A7064, 0x808A7070, 0x808A7074,
              0x808A7078, 0x808A7080, 0x808A7084)),
    (13, 15, (0x808A86F4, 0x808A86F8, 0x808A86FC, 0x808A8700,
              0x808A8704, 0x808A8708, 0x808A870C)),
    (13, 15, (0x808A8978, 0x808A897C, 0x808A8980, 0x808A8984,
              0x808A898C, 0x808A8990, 0x808A8994)),
)
NAMES = {0x808A6C08: 0x24510380, 0x808A89A4: 0x24450380, 0x808A9610: 0x26B00380}
STRIDES = {at: 0x26B503C6 for at in (0x808A94CC, 0x808A95E0, 0x808A9660)}
TAIL = {
    0x808A6F94: 0x24C23110, 0x808A6FBC: 0xA0C73110, 0x808A6FD8: 0xA0C73110,
    0x808A704C: 0x90CB3119, 0x808A7058: 0x90D83110, 0x808A7090: 0x90C53110,
    0x808A70A4: 0xA0C03119, 0x808A7180: 0x9078311A, 0x808A71C4: 0xA069311A,
    0x808A7208: 0xA06B311B, 0x808A723C: 0xA06E311B, 0x808A800C: 0x250530C0,
    0x808A87E4: 0x918D311B, 0x808A91CC: 0x26503118, 0x808A9608: 0xA2F33110,
    0x808A971C: 0x248430C0, 0x808A9744: 0x248430C0,
}


def shifted(address):
    return address + GROWTH if address >= RAM + START else address


def multiply_words(source, destination, expanded=False):
    def shift(src, amount): return src << 16 | destination << 11 | amount << 6
    def add(sub=False): return destination << 21 | source << 16 | destination << 11 | (35 if sub else 33)
    # Preserve every intermediate instruction's destination and all unrelated
    # interleaved loads. No additional register, HI/LO, branch, or delay slot.
    return (shift(source, 1), add(), shift(destination, 4), add(),
            shift(destination, 1), add(), shift(destination, 4)) if expanded else (
            shift(source, 4), add(True), shift(destination, 3), add(),
            shift(destination, 2), add(True), shift(destination, 1))


def expand(data, rows):
    """Caller binds the complete installed image; bind every changed word too."""
    source = bytes(data)
    if any(source[PREFIX:START]) or len(source) + GROWTH > 0x10000:
        raise ValueError('Catalogue state is not clear or overlaps its next VROM')
    expected = set(NAMES) | set(STRIDES) | set(TAIL)
    # Independently scan the complete native executable for the reviewed layout
    # immediates, excluding no instructions on the basis of a guessed function.
    found = {RAM + at for at in range(0, 14048, 4)
             if u32(source, at) >> 26 in (9, 32, 33, 35, 36, 37, 40, 41, 43)
             and (u32(source, at) & 65535 in (896, 966)
                  or 0x30C0 <= u32(source, at) & 65535 < 0x3120)}
    if found != expected:
        raise ValueError('Unreviewed native catalogue layout consumer')
    result = bytearray(source[:START] + bytes(GROWTH) + source[START:])
    patches = {}

    def put(old_at, before, after, reason):
        at = shifted(RAM + old_at) - RAM
        if u32(source, old_at) != before:
            raise ValueError(f'Changed catalogue capacity instruction {RAM + old_at:08X}')
        previous = patches.get(old_at)
        if previous and previous['after'] != after:
            raise ValueError('Shared catalogue HI16 needs incompatible rewritten targets')
        struct.pack_into('>I', result, at, after)
        if before != after:
            patches[old_at] = {'address': RAM + old_at, 'installed_address': RAM + at,
                              'before': before, 'after': after, 'reason': reason}

    for src, dst, addresses in MULTIPLIERS:
        for address, before, after in zip(addresses, multiply_words(src, dst), multiply_words(src, dst, True)):
            put(address - RAM, before, after, 'category stride multiplication')
    for values, delta, reason in ((NAMES, NAME_OFFSET - 896, 'compatibility name fields'),
                                  (STRIDES, PAGE_BYTES - 966, 'category initializer stride'),
                                  (TAIL, TAIL_GROWTH, 'aligned frame and navigation tail')):
        for address, before in values.items():
            put(address - RAM, before, before + delta, reason)

    high, moved_rows = {}, []

    def target(value):
        if not RAM <= value < RAM + len(source):
            raise ValueError('Catalogue relocation target escaped the complete image')
        return shifted(value)

    for row in rows:
        at, kind = row & 0xFFFFFF, row >> 24 & 63
        if row >> 30 != 1 or at & 3 or at > len(source) - 4 or PREFIX <= at < START:
            raise ValueError('Unsupported catalogue capacity relocation location')
        word = u32(source, at)
        moved_rows.append((row & 0xFF000000) | (shifted(RAM + at) - RAM))
        if kind == 2:
            if not word & 0x0F000000: put(at, word, target(word), 'shifted data pointer')
        elif kind == 4:
            if word >> 26 not in (2, 3): raise ValueError('Invalid catalogue jump relocation')
            value = target(0x80000000 | (word & 0x3FFFFFF) << 2)
            put(at, word, word & 0xFC000000 | (value >> 2 & 0x3FFFFFF), 'shifted call target')
        elif kind == 5:
            if word >> 26 != 15: raise ValueError('Invalid catalogue HI16')
            high[word >> 16 & 31] = at, word
        elif kind == 6:
            if word >> 21 & 31 not in high: raise ValueError('Unpaired catalogue LO16')
            hi_at, hi_word = high[word >> 21 & 31]
            value = ((hi_word & 65535) << 16) + (word & 65535) - (65536 if word & 32768 else 0)
            if not value & 0x0F000000:
                value = target(value)
                put(hi_at, hi_word, hi_word & 0xFFFF0000 | ((value + 32768) >> 16 & 65535), 'shifted high pointer')
                put(at, word, word & 0xFFFF0000 | value & 65535, 'shifted low pointer')
        else:
            raise ValueError('Unsupported catalogue capacity relocation kind')
    return result, moved_rows, {
        'capacity': CAPACITY, 'page_bytes': PAGE_BYTES, 'name_offset': NAME_OFFSET,
        'state_offset': PREFIX, 'state_bytes': STATE_BYTES, 'insert_at': START,
        'insert_bytes': GROWTH, 'tail_growth': TAIL_GROWTH,
        'frame_offset': 0x30C0 + TAIL_GROWTH, 'page_order_offset': 0x3110 + TAIL_GROWTH,
        'additional_pool_allocation': POOL_EXTRA, 'linked_image_sha256': sha256(source),
        'patches': list(patches.values()),
    }
