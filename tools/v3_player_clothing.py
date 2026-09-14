"""Connect native player startup/change-clothes resource readers."""
import struct

from aflib import CODE_RAM, sha256
from v3_npc_clothing import guard_incoming

ABI = 30
SOURCES = ('tools/v3_player_clothing.py', 'overlays/v3/player_clothing.c')
ENTRIES = (
    (0x800B1960, 0x800B19C4, 'af_v3_player_cloth_texture',
     '789eabdcbf87662385d063f85063cbe9d82aa5a44512ad58f458b88ed0c6f1fb'),
    (0x800B19C4, 0x800B1A28, 'af_v3_player_cloth_palette',
     'cf3c343a5aca576cfb75f291f9195c65a989fcd9659fbacb1acf00e0e78722e8'),
    (0x800B1BE8, 0x800B1C84, 'af_v3_player_change_cloth',
     'dea15c33cac54127e6fe12a754baa05269ffc479ab38039510f09e48c534f6fe'),
)


def install(code, symbols):
    before, hooks = bytes(code), []
    guard_incoming(before, len(before), CODE_RAM, [(entry-CODE_RAM, 8) for entry, *_ in ENTRIES])
    for entry, end, name, digest in ENTRIES:
        at, target = entry-CODE_RAM, symbols[name]
        if (sha256(before[at:end-CODE_RAM]) != digest
                or not 0x80460100 <= target < 0x80461000 or target % 4):
            raise ValueError('Changed native player clothing function or helper reservation')
        struct.pack_into('>2I', code, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        hooks.append({'entry': f'{entry:08X}', 'end': f'{end:08X}', 'helper': name,
            'native_function_sha256': digest, 'before': before[at:at+8].hex(),
            'after': code[at:at+8].hex()})
    return {'hooks': hooks, 'native_double_buffering_retained': True,
            'saved_clothing_fields_changed': False, 'ordinary_wearing_gameplay_tested': False,
            'item_acquisition_and_persistence_ready': False}
