"""Bind the shared item readers to real selected clothing metadata."""
import struct

from aflib import sha256
from v3_furniture_items import ENTRIES
from v3_save_clothing import RAM

ABI = 32
SOURCES = ('tools/v3_clothing_items.py', 'overlays/v3/clothing.h')
DEFINES = tuple('af_v3_item_'+name+'=af_v3_item_'+name+'_extended'
                for name in ('name', 'type', 'size', 'place', 'price'))


def install(blob, extended, original, asset):
    size = original['bytes']
    if (len(blob) != 0xC000 or sha256(blob[0x7300:0x7300+size]) != original['sha256']
            or extended['symbols']['af_v3_clothing_source'] != asset['symbols']['af_v3_clothing_source']
            or asset['symbols']['af_v3_clothing_source'] != 0x804608F0):
        raise ValueError('Changed complete shared item code or clothing source dependency')
    hooks = []
    for _, _, name, _, _ in ENTRIES:
        entry, target = original['symbols'][name], extended['symbols'][name+'_extended']
        at = entry-0x80460000
        if not 0x7300 <= at <= 0x7300+size-8 or not RAM <= target < RAM+extended['bytes'] or (entry | target) & 3:
            raise ValueError('Invalid shared clothing item entry')
        before = bytes(blob[at:at+8])
        struct.pack_into('>2I', blob, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        hooks.append({'entry': f'{entry:08X}', 'target': f'{target:08X}', 'helper': name,
                      'before': before.hex(), 'after': blob[at:at+8].hex()})
    return {'hooks': hooks, 'name': 'cherry shirt', 'item_id': '34BF', 'native_category': 12,
            'price': 380, 'selected_profile_required': True,
            'footprint': 'native non-furniture rejection with cleared cells',
            'ordinary_menus_acquisition_and_wearing_ready': False}
