"""Install a dedicated Expansion Pak pool for the native furniture-bank lifetime."""
import copy
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256, u32
from npc_mail_show import relocate_verified_data
from v3_furniture_runtime import VROM, RELOC, RAM, SIZE, RESIDENT

START, DATA, BYTES, COUNT = 0x80500000, 0x80500010, 0x2400, 100
GUARD, END, EDGE = DATA + COUNT * BYTES, DATA + COUNT * BYTES + 16, 0xAF42C0DE
SOURCES = ('tools/v3_furniture_banks.py', 'overlays/v3/furniture_banks.h',
           'overlays/v3/furniture.c', 'overlays/v3/furniture_expanded.ld')


def install(base, furniture, compiled):
    files = by_vrom(base)
    source, reloc = files[VROM].extract(base), files[RELOC].extract(base)
    previous = furniture['expanded_tables']
    if (len(source) != SIZE or sha256(source) != previous['output_sha256']
            or sha256(reloc) != furniture['owner']['output_relocation_sha256']
            or len(reloc) != 6208 or struct.unpack_from('>5I', reloc) != (69200, 23520, 480, 8944, 1401)
            or compiled['symbols'].get('af_v3_save_halt') != 0x80469270
            or 'AF_V3_EXPANDED_BANKS=1' not in ' '.join(compiled['flags'])
            or not 0x80465800 <= compiled['symbols']['af_v3_furniture_secure_banks'] < 0x80466000):
        raise ValueError('Changed native furniture pool dependencies')
    data = bytearray(source)
    begin, end = 0x80938E14, 0x80938E28
    before = struct.pack('>5I', 0x3C028095, 0x3C038095, 0x2463F608, 0x2442F478, 0x24420004)
    if data[begin - RAM:end - RAM] != before:
        raise ValueError('Changed complete native pool setup window')
    # The native prefix still reserves/loads the dummy keyframe. Replace only
    # bank allocation: use the existing saved room argument, then the original
    # epilogue. No fixed Expansion Pak pointer reaches native heap cleanup.
    after = struct.pack('>5I', 0x02202025,
        0x0C000000 | (compiled['symbols']['af_v3_furniture_secure_banks'] >> 2 & 0x3FFFFFF),
        0, 0x10000000 | ((0x80938ED8 - (begin + 12) - 4) // 4), 0)
    data[begin - RAM:end - RAM] = after
    sections = struct.unpack_from('>5I', reloc)
    rows = list(struct.unpack_from('>1401I', reloc, 20))
    removed, retained = [], []
    for row in rows:
        address = RAM + sum(sections[:(row >> 30) - 1]) + (row & 0xFFFFFF)
        (removed if begin <= address < end else retained).append(row)
    if sorted(removed) != sorted((0x45002704, 0x45002708, 0x4600270C, 0x46002710)):
        raise ValueError('Pool setup has changed relocation pairs')
    new_reloc = bytearray(reloc)
    struct.pack_into('>I', new_reloc, 16, len(retained))
    new_reloc[20:-4] = struct.pack('>' + str(len(retained)) + 'I', *retained) + bytes(len(reloc) - 24 - len(retained) * 4)
    # All count/cap/teardown instructions are retained. The adapter combines
    # bank_count0 + bank_count1, then sets bank_count1 to zero. The original
    # destructor consequently has no heap banks to free.
    for address, words in (
        (0x80938CE8, (0xAC800000, 0xACA00000, 0x8CC20000, 0x240F0023, 0x28410065)),
        (0x8093B710, (0x8E2204C4, 0x02209025, 0x50400011)),
        (0x8093B740, (0x0C027010, 0x8F040000))):
        if source[address - RAM:address - RAM + len(words) * 4] != struct.pack('>' + str(len(words)) + 'I', *words):
            raise ValueError('Changed native bank count or destruction contract')
    changed = set(range(begin - RAM, end - RAM))
    for address in (0x801A0010, 0x802F8010, 0x803D0010):
        spec = SimpleNamespace(ram=RAM, resident_bytes=RESIDENT, sections=sections)
        old = relocate_verified_data(spec, source, reloc, address)
        spec.sections = (*sections[:4], len(retained))
        new = relocate_verified_data(spec, data, new_reloc, address)
        if any(a != b and i not in changed for i, (a, b) in enumerate(zip(old, new, strict=True))):
            raise ValueError('Pool setup changes unrelated native relocated code')
    result = copy.deepcopy(furniture)
    result['expanded_tables']['output_sha256'] = sha256(data)
    result['owner'].update(output_sha256=sha256(data), output_relocation_sha256=sha256(new_reloc),
                           retained_relocations=len(retained))
    result['native_bank_bytes'] = BYTES
    result['bank_pool'] = {'start': START, 'data': DATA, 'guard': GUARD, 'end': END,
        'bank_bytes': BYTES, 'banks': COUNT, 'reservation_bytes': END - START, 'guard_word': EDGE,
        'source_owner_sha256': sha256(source), 'source_relocation_sha256': sha256(reloc),
        'output_owner_sha256': sha256(data), 'output_relocation_sha256': sha256(new_reloc),
        'hook': {'address': begin, 'before': before.hex(), 'after': after.hex()},
        'removed_relocations': removed, 'native_bank_cleanup_unchanged': True,
        'ordinary_heap_growth': 0, 'object_arena_growth': 0,
        'catalogue_preview_bytes': 0x2400, 'native_test': 'pending'}
    return {VROM: bytes(data), RELOC: bytes(new_reloc)}, result
