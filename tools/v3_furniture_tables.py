"""Expand transient profile/bank tables without extending either native heap."""
import struct

from aflib import sha256, u32
from v3_furniture_runtime import RAM, SECTIONS

ABI, CODE, CAPACITY = 40, 0xA000, 2051
PROFILES, INDICES = 0x80470010, 0x80472040
START, END, EDGE = 0x80470000, 0x80472860, 0xAF46C0DE
SOURCES = ('tools/v3_furniture_tables.py', 'overlays/v3/furniture_tables.c',
           'overlays/v3/furniture_tables.h', 'overlays/v3/furniture_tables.ld',
           'overlays/v3/furniture_expanded.ld')
SOURCE_SHA = 'ce4e0ebfb38f5118bb94f9347ddc771e04331562ed9decd91482689751578b19'


def install_helper(blob, helper, compiled, previous):
    if (not helper or len(helper) != compiled['bytes'] or len(helper) > 0x800
            or any(blob[0x5800:0x5800+len(helper)])
            or compiled['symbols']['af_v3_furniture_import_profile'] != 0x80465800):
        raise ValueError('Expanded furniture code exceeds the retired native table prefix')
    entries = []
    for name, address in previous['symbols'].items():
        if not name.startswith('af_v3_furniture_'):
            continue
        target = compiled['symbols'].get(name)
        at = address-0x80460000
        if (not 0x5000 <= at <= 0x5400-8 or target is None
                or not 0x80465800 <= target <= 0x80465800+len(helper)-8):
            raise ValueError('Unbound furniture public entry')
        before = bytes(blob[at:at+8])
        after = struct.pack('>2I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        blob[at:at+8] = after
        entries.append({'name': name, 'entry': address, 'target': target,
                        'before': before.hex(), 'after': after.hex()})
    if len(entries) != 8:
        raise ValueError('Changed furniture public entry inventory')
    blob[0x5800:0x5800+len(helper)] = helper
    return entries


def install(data, relocation, blob, helper, compiled, seed_report):
    if (sha256(data) != SOURCE_SHA or sha256(relocation) != seed_report['room_relocation_sha256']
            or CAPACITY % 4 != 3 or PROFILES+CAPACITY*4 > INDICES
            or INDICES+CAPACITY > END-16 or START < 0x80470000 or END > 0x80800000):
        raise ValueError('Unexpected furniture owner, relocation, or expanded table bounds')
    if (compiled['symbols']['af_v3_furniture_tables_init'] != 0x80460000+CODE
            or len(helper) != compiled['bytes'] or not helper or len(helper) > 0x200
            or any(blob[CODE:CODE+0x200])):
        raise ValueError('Furniture table initializer collides with resident code')
    rows = seed_report['bindings']
    if len(rows) != 72:
        raise ValueError('Changed resolved furniture table reference inventory')
    data = bytearray(data)
    patches = {}

    def word(address, before, after):
        at = address-RAM
        if address in patches:
            if patches[address] != (before, after):
                raise ValueError('Shared table high instruction has incompatible targets')
            return
        if u32(data, at) != before:
            raise ValueError(f'Changed table instruction {address:08X}')
        struct.pack_into('>I', data, at, after)
        patches[address] = (before, after)

    for row in rows:
        old = row['target']
        if 0x80465800 <= old <= 0x80465800+947*4:
            new = PROFILES+old-0x80465800
        elif 0x80466C00 <= old <= 0x80466C00+1267:
            new = INDICES+(CAPACITY if old == 0x80466C00+1267 else old-0x80466C00)
        else:
            raise ValueError('Unbound furniture table target')
        hi, lo = row['high'], row['low']
        hi_word = patches[hi][0] if hi in patches else u32(data, hi-RAM)
        lo_word = u32(data, lo-RAM)
        if ((hi_word & 65535) != (old+0x8000) >> 16 or lo_word & 65535 != old & 65535):
            raise ValueError('Table source pointer differs from its recorded binding')
        word(hi, hi_word, hi_word & 0xFFFF0000 | (new+0x8000) >> 16)
        word(lo, lo_word, lo_word & 0xFFFF0000 | new & 65535)
    for address, prefix in ((0x80936F00, 0x28410000), (0x80937594, 0x24120000),
                            (0x8093BBD0, 0x24140000)):
        word(address, prefix | 1267, prefix | CAPACITY)
    relocations = set()
    for (row,) in struct.iter_unpack('>I', relocation[20:20+u32(relocation, 16)*4]):
        relocations.add(RAM+sum(SECTIONS[:(row >> 30)-1])+(row & 0xFFFFFF))
    if relocations & patches.keys():
        raise ValueError('A fixed expanded-table pointer still has a relocation')
    blob[CODE:CODE+len(helper)] = helper
    return bytes(data), {'capacity': CAPACITY, 'profile_table_ram': f'{PROFILES:08X}',
        'bank_index_ram': f'{INDICES:08X}', 'reservation_start': f'{START:08X}',
        'reservation_end': f'{END:08X}', 'reservation_bytes': END-START,
        'guard_word': f'{EDGE:08X}', 'initializer': compiled,
        'source_sha256': SOURCE_SHA, 'output_sha256': sha256(data),
        'retargeted_references': len(rows), 'native_heap_growth': 0,
        'patches': [{'address': address, 'before': before, 'after': after}
                    for address, (before, after) in sorted(patches.items())],
        'new_items_enabled': False, 'saved_formats_changed': False}
