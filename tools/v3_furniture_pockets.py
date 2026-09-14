"""Selected furniture participates in complete native pocket-type searches."""
import struct

from aflib import CODE_RAM, sha256
from v3_furniture_room import BLOB_SIZE

ABI, CODE, BRIDGE = 12, 0xB200, 0xB100
SOURCES = ('tools/v3_furniture_pockets.py', 'overlays/v3/pockets.c', 'overlays/v3/pockets.ld')
ENTRIES = ((0x800B8128, 124, 'af_v3_pocket_index',
            '586984d65472a6844f26eba24cfdd1263a32e70f514aaad3ab21412ce997a367'),
           (0x800B8544, 424, 'af_v3_pocket_count',
            '7bb1e34399d09c8bcf0e80abde99aad5e5a17c8a3261c4e38ef1af7e9019f59b'))
PROLOGUE = (0x27BDFFF8, 0xAFB00004)


def install(code, blob, helper, symbols, room_symbols):
    if (len(blob) != BLOB_SIZE or any(blob[BRIDGE:-16]) or len(helper) > BLOB_SIZE - CODE - 16
            or room_symbols['af_v3_room_value'] != 0x80468000):
        raise ValueError('Pocket helper overlaps resident data or has a changed classification ABI')
    patches = []
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    for i, (address, size, name, digest) in enumerate(ENTRIES):
        at, target = address - CODE_RAM, symbols[name]
        if (sha256(code[at:at + size]) != digest or struct.unpack_from('>II', code, at) != PROLOGUE
                or not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper) or target & 3):
            raise ValueError('Changed complete native pocket query or helper target')
        bridge = BRIDGE + i * 16
        struct.pack_into('>4I', blob, bridge, *PROLOGUE, jump(address + 8), 0)
        struct.pack_into('>II', code, at, jump(target), 0)
        patches.append({'address': address, 'bytes': size, 'helper': name,
                        'source_sha256': digest, 'bridge': 0x80460000 + bridge})
    blob[CODE:CODE + len(helper)] = helper
    return {'patches': patches, 'pocket_count': 15, 'pockets_offset': 0x14,
            'conditions_offset': 0x34, 'saved_data_changed': False,
            'ordinary_inventory_tested': False}
