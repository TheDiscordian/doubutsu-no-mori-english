"""Subset-aware native town selection, initially with import move-ins disabled."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256

ABI, CODE, LIMIT = 25, 0x3400, 0x4000
GROWTH, FLAGS, CANDIDATES, SHUFFLE = 0x1D80, 0x1E60, 0x4700, 0x4800
SOURCES = ('tools/v3_villager_selection.py', 'overlays/v3/villager_selection.c',
           'overlays/v3/villager_selection.ld', 'overlays/v3/villager_outfit.h')
ENTRIES = (
    (0x800AA3A4, 0x800AA438, 'af_v3_unseen_personality'),
    (0x800AA49C, 0x800AA4FC, 'af_v3_reset_appeared'),
    (0x800AA51C, 0x800AA790, 'af_v3_initial_population'),
    (0x800AD6D4, 0x800AD8C4, 'af_v3_grow_personality'),
)


def install(native, code, blob, helper, symbols, text_report, house_report):
    files = by_vrom(native)
    original = files[CODE_VROM].extract(native)
    growth = files[0xE0D000].extract(native)
    if len(growth) != 224 or sha256(growth) != 'a3936366a0229ecacd2eaeca7fa72b31ed1149394d7b5c93a031d19b57bb6eb6':
        raise ValueError('Changed native starting-population permissions')
    if len(blob) != 0xC000 or not 0 < len(helper) <= LIMIT-CODE:
        raise ValueError('Selection code does not fit the current resident reservation')
    for start, end in ((CODE, LIMIT), (GROWTH, FLAGS+20), (CANDIDATES, CANDIDATES+32),
                       (SHUFFLE, SHUFFLE+238*4)):
        if any(blob[start:end]):
            raise ValueError('Selection code/data overlaps another resident component')
    if not house_report or house_report['installed_villagers'] not in (['E0EA'], ['E0EA', 'E0ED']):
        raise ValueError('Selection integration requires complete Cheri house data')
    # Data readiness is separate from eligibility. No new identity reaches
    # ordinary gameplay until the remaining native readers/house checks close.
    capable = [row['actor_id'] for row in text_report['imports']
               if row['initial_defaults_applied'] and row['actor_id'] in house_report['installed_villagers']]
    if capable != house_report['installed_villagers']:
        raise ValueError('Changed reviewed ordinary-villager content dependencies')
    patches = []
    for start, end, name in ENTRIES:
        at, stop = start-CODE_RAM, end-CODE_RAM
        if bytes(code[at:stop]) != original[at:stop]:
            raise ValueError('Changed complete native selection function')
        target = symbols[name]
        if not 0x80460000+CODE <= target < 0x80460000+CODE+len(helper):
            raise ValueError('Selection function escapes its resident code')
        previous = bytes(code[at:at+8])
        struct.pack_into('>II', code, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        patches.append({'entry': f'{start:08X}', 'end': f'{end:08X}', 'symbol': name,
                        'before': previous.hex(), 'after': bytes(code[at:at+8]).hex(),
                        'native_function_sha256': sha256(original[at:stop])})
    blob[CODE:CODE+len(helper)] = helper
    blob[GROWTH:FLAGS] = growth
    return {'hooks': patches, 'compiled_bytes': len(helper), 'compiled_sha256': sha256(helper),
            'native_growth_sha256': sha256(growth), 'content_ready': capable,
            'move_in_enabled': [], 'flag_bytes': 20, 'candidate_bytes': 32,
            'shuffle_capacity': 238, 'saved_appearance_history_bytes': 32,
            'saved_layout_changed': False, 'native_execution': 'pending'}
