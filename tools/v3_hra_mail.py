"""Extend the complete English score-letter creator with additive theme names."""
import struct
import zlib
from types import SimpleNamespace

from aflib import sha256, u32
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_furniture_art import verify_sources

VROM, RAM, IMAGE, RELOC_BYTES = 0x03200000, 0x80B00000, 0xEF10, 0x3C0
TABLE, COUNT, WIDTH = 0x9860, 56, 26
SOURCE_SHA = 'f748367feae282b9959d4b27823b28945df9d9033cb30592cdae2e9c7e3207ac'
TABLE_SHA = 'be1258e1806e2a5e38a64cad52863c632d45b4610685ec9590dd264bb1569a38'
SOURCES = ('tools/v3_hra_mail.py',)
COUNTERS = {0x25F4: 0x240205A0, 0x2834: 0x24140037,
            0x2848: 0x240D0037, 0x2A10: 0x2E820037, 0x2B68: 0x2E820037}


def install(source, module, rel, symbols):
    verify_sources(rel, symbols)
    config = struct.unpack_from('>8I', module, 0x48)
    if (sha256(source) != SOURCE_SHA or len(source) != IMAGE+RELOC_BYTES
            or config != (VROM, len(source), IMAGE, RELOC_BYTES, 0xEBF0,
                          IMAGE, zlib.crc32(source), 0x41464E01)):
        raise ValueError('Changed complete V3 letter creator or its loader configuration')
    original_table = source[TABLE:TABLE+1440]
    if sha256(original_table) != TABLE_SHA:
        raise ValueError('Changed complete native-to-English theme-name table')
    donor = symbol_data(rel, symbols.decode(), 'mMkRm_series_name')
    name = donor[58*16:59*16]
    if name != b'boxing          ':
        raise ValueError('Changed complete donor boxing name')
    # Lookup-row identity is independent of the game's series index: preserve
    # all 55 original keys, then add the new series-58 key as lookup row 55.
    table = original_table[:55*WIDTH] + name[:10] + name
    if len(table) != COUNT*WIDTH or len(table) % 16:
        raise ValueError('Incomplete or unaligned expanded score-letter names')
    data = bytearray(source[:IMAGE]+table)
    relocation = bytearray(source[IMAGE:])
    sections = struct.unpack_from('>5I', relocation)
    if sections != (IMAGE, 0, 0, 0, 233) or len(data) > 0x10000:
        raise ValueError('Changed creator relocation or exceeded native loader capacity')
    patches = []

    def word(at, before, after):
        if u32(data, at) != before:
            raise ValueError(f'Changed score-letter instruction at {RAM+at:08X}')
        struct.pack_into('>I', data, at, after)
        patches.append({'offset': at, 'before': before, 'after': after})

    for at, before in COUNTERS.items():
        word(at, before, before & 0xFFFF0000 | (len(table) if at == 0x25F4 else COUNT))
    high, pointers = {}, []
    for (value,) in struct.iter_unpack('>I', relocation[20:20+233*4]):
        section, kind, at = value >> 30, value >> 24 & 63, value & 0xFFFFFF
        if section != 1:
            raise ValueError('Unexpected non-text creator relocation')
        instruction = u32(source, at)
        if kind == 5:
            high[instruction >> 16 & 31] = at, instruction
        elif kind == 6:
            upper_at, upper = high[instruction >> 21 & 31]
            target = (upper & 65535)*65536 + (instruction & 65535) - (65536 if instruction & 32768 else 0)
            if RAM+TABLE <= target < RAM+TABLE+1440:
                new = RAM+IMAGE+target-(RAM+TABLE)
                word(upper_at, upper, upper & 0xFFFF0000 | (new+0x8000) >> 16 & 65535)
                word(at, instruction, instruction & 0xFFFF0000 | new & 65535)
                pointers.append((at, target))
    if pointers != [(0x2600, RAM+TABLE), (0x2A28, RAM+TABLE+10)]:
        raise ValueError('Changed complete score-letter name-reference inventory')
    # 2A04 is template 37 (55), not a series bound. It must remain unchanged.
    if u32(data, 0x2A04) != 0x24020037:
        raise ValueError('Score-letter extension changed the item-recommendation template')
    struct.pack_into('>I', relocation, 0, len(data))
    allowed = {i for p in patches for i in range(p['offset'], p['offset']+4)}
    for loaded in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=IMAGE, sections=sections),
                                        source[:IMAGE], source[IMAGE:], loaded)
        after = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=len(data),
            sections=(len(data), 0, 0, 0, 233)), data, relocation, loaded)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Score-letter names alter unrelated relocated creator code/data')
    result = bytes(data+relocation)
    updated = (VROM, len(result), len(data), RELOC_BYTES, config[4], len(data),
               zlib.crc32(result), config[7])
    struct.pack_into('>8I', module, 0x48, *updated)
    return result, {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(result),
        'image_bytes': len(data), 'relocation_bytes': RELOC_BYTES, 'bytes': len(result),
        'native_name_rows': 55, 'name_rows': COUNT, 'name_table_address': RAM+IMAGE,
        'name_table_sha256': sha256(table), 'added_name': 'boxing', 'series': 58,
        'patches': patches, 'configuration': list(updated), 'save_format_changed': False,
        'native_letter_generation_tested': False}
