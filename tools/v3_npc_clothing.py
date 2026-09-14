"""Bind both complete native NPC clothing paths to the additive resource reader."""
import struct

from aflib import by_vrom, sha256
from v3_npc_draw import OWNERS, relocation_offsets

ABI = 29
SOURCES = ('tools/v3_npc_clothing.py', 'overlays/v3/npc_clothing.c')
BOUNDS = (0, 0xBC, 0x178, 0x26C, 0x2C0, 0x314, 0x3F0)
DIGESTS = {
    0x8681F0: (
        '1d96d3ab430799b9ad755e621e3a851141b0f24b20d0231590483f3c2def6f03',
        '52b85f686007bf438c1373d9dc5a8928bdc8a2027b706134205e59cc9d0f04bd',
        'a9ba6f1a3c69e35def8dd12cbbed61c1dac33a77ef3e57a4d1d6f984c0e3f3a5',
        '3f3739c65c94a773b02849182af77561f21a3619c9d385800f843692b50bc762',
        'a5855501c4605ad36b644c57206456a8a5eb6686a69915c647bebeaf2f8316b2',
        '63b8f360d7b760b0cf1b41170648bdc1449f5d8d0134f38b91e1f48bac94bc1c'),
    0x8798C0: (
        '476f29d48d484bd59828fc4cd61c3ea9362d3f607d83f10c012d31fa309652e9',
        'cf37d78b786517d5b0cf8c7e01a1cd4b34d604f3ccf3fea481feb3463ae327f5',
        '9ec07311a6b71d810a83a36bed73f124cd61b0fa6082f63a27b8c69d72a7f394',
        'c1e4cba258356ff34e1bb3f1481acc19faa9d0e56498cfb293cf59cde1b381d6',
        '2d29ca1b3a199fc4ca35422180fb29e9dee218b1ec3f797e05a5dd36dc4a6c19',
        '678cc380c7981773a638a19e992c149c653a0db03e59c4998e4cc9d0c27ac44f'),
}
ENTRIES = ((0, 'af_v3_npc_cloth_texture'), (0xBC, 'af_v3_npc_cloth_palette'),
           (0x26C, 'af_v3_npc_cloth_texture_sync'), (0x2C0, 'af_v3_npc_cloth_palette_sync'))
WINDOWS = ((0x1E0, '16b8000430590f000019420352c800042451dc00a617000432e2ffff2451dc00'),
           (0x380, '1698000430590f000019420352a800042451dc00a616000432c2ffff2451dc00'))


def guard_incoming(data, text_size, ram, windows):
    """Reject outside branches/jumps or embedded pointers into a rewritten interior."""
    for at in range(0, len(data)-3, 4):
        word = struct.unpack_from('>I', data, at)[0]
        targets = [word-ram]
        if at < text_size:
            op = word >> 26
            if op in (2, 3): targets.append(((ram+at+4) & 0xF0000000 | (word & 0x3FFFFFF)*4)-ram)
            if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
                delta = word & 0xFFFF
                targets.append(at+4+(delta if delta < 0x8000 else delta-0x10000)*4)
        for start, length in windows:
            if not start <= at < start+length and any(start < t < start+length for t in targets):
                raise ValueError('Native control flow enters a replaced clothing window')


def patch_owners(native, changes, symbols):
    files, result, report = by_vrom(native), dict(changes), []
    for vrom, reloc, ram, *_ in OWNERS:
        before = result[vrom]
        data, relocation = bytearray(before), files[reloc].extract(native)
        for start, end, digest in zip(BOUNDS, BOUNDS[1:], DIGESTS[vrom]):
            if sha256(data[start:end]) != digest:
                raise ValueError('Changed complete native NPC clothing function')
        ranges = [(at, 8) for at, _ in ENTRIES] + [(at, 32) for at, _ in WINDOWS]
        guard_incoming(data, struct.unpack_from('>I', relocation)[0], ram, ranges)
        slots = relocation_offsets(relocation, len(data))
        if any(set(range(at, at+size, 4)) & slots for at, size in ranges):
            raise ValueError('NPC clothing patch overlaps a native relocation')
        hooks = []
        for at, name in ENTRIES:
            target = symbols[name]
            if not 0x80460100 <= target < 0x80461000 or target % 4:
                raise ValueError('NPC clothing helper exceeds its reservation')
            struct.pack_into('>2I', data, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
            hooks.append({'address': f'{ram+at:08X}', 'helper': name,
                          'before': before[at:at+8].hex(), 'after': data[at:at+8].hex()})
        target = symbols['af_v3_clothing_checked_index']
        if not 0x80460100 <= target < 0x80461000 or target % 4:
            raise ValueError('NPC clothing index helper exceeds its reservation')
        for at, expected in WINDOWS:
            if data[at:at+32].hex() != expected:
                raise ValueError('Changed native clothing category decision')
            struct.pack_into('>8I', data, at, 0x26040004,
                0x0C000000 | (target >> 2 & 0x3FFFFFF), 0, 0x00408825, 0x02002025, 0, 0, 0)
            hooks.append({'address': f'{ram+at:08X}', 'helper': 'af_v3_clothing_checked_index',
                          'before': expected, 'after': data[at:at+32].hex()})
        result[vrom] = bytes(data)
        report.append({'vrom': f'{vrom:08X}', 'link_address': f'{ram:08X}',
            'source_sha256': sha256(before), 'patched_sha256': sha256(data),
            'native_function_sha256': list(DIGESTS[vrom]), 'hooks': hooks,
            'relocation_sha256': sha256(relocation), 'relocations_unchanged': True,
            'slot_offset': 0x174, 'slot_stride': 0xB0, 'slots': 10})
    return result, report
