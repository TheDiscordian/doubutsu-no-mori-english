"""Route actual native item collection and player clearing to V3 ownership."""
import struct

from aflib import CODE_RAM, sha256
from v3_save_runtime import BLOB_SIZE

ABI, CODE, LIMIT, BRIDGE = 15, 0x99C0, 0xA200, 0xBA80
SOURCES = ('tools/v3_collection.py', 'overlays/v3/collection.c', 'overlays/v3/collection.ld')
ENTRIES = ((0x800B88EC, 412, 'af_v3_catalogue_record', (0x27BDFFE8, 0xAFA40018),
            'f545d3a285b2c1797a5a92cb8029ab62c3bce494d63496ec772dc34a5f07b676'),
           (0x800B7ADC, 176, 'af_v3_catalogue_clear', (0x27BDFFE0, 0xAFB00018),
            '0570f6d9241cae5740e981cf7e04218cc1b0ec1b0a2bc6c3c6f14679c3431609'))
POSSESSION_SHA = '381dedb15e54d276176dc4691c7ed020b484ca87aa3b2df5604ba47193afb32a'


def install(code, blob, helper, symbols, runtime, codec, furniture):
    imports = {'af_v3_require_save_state': (runtime, 'require_state', 0x804692F4),
               'af_v3_save_halt': (runtime, 'af_v3_save_halt', 0x80469270),
               'af_v3_save_collect': (codec, 'af_v3_save_collect', 0x8046B9C4),
               'af_v3_furniture_import_profile': (furniture, 'af_v3_furniture_import_profile', 0x80465000)}
    if (len(blob) != BLOB_SIZE or not helper or len(helper) > LIMIT - CODE
            or any(blob[CODE:LIMIT]) or any(blob[BRIDGE:BRIDGE + 32])
            or 0x9200 + runtime['bytes'] > CODE):
        raise ValueError('Collection code overlaps existing runtime data')
    for name, (owner, original_name, address) in imports.items():
        if owner['symbols'][original_name] != address or symbols[name] != address:
            raise ValueError('Changed collection dependency ABI: ' + name)
    if sha256(code[0x800B8B08 - CODE_RAM:0x800B8BE4 - CODE_RAM]) != POSSESSION_SHA:
        raise ValueError('Changed native pocket acquisition/condition path')
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    patches = []
    for i, (address, size, name, prologue, digest) in enumerate(ENTRIES):
        at, target = address - CODE_RAM, symbols[name]
        if (sha256(code[at:at + size]) != digest or struct.unpack_from('>II', code, at) != prologue
                or not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper) or target & 3):
            raise ValueError('Changed collection owner or helper entry')
        struct.pack_into('>4I', blob, BRIDGE + i * 16, *prologue, jump(address + 8), 0)
        struct.pack_into('>II', code, at, jump(target), 0)
        patches.append({'address': address, 'bytes': size, 'helper': name,
                        'source_sha256': digest, 'bridge': 0x80460000 + BRIDGE + i * 16})
    blob[CODE:CODE + len(helper)] = helper
    return {'patches': patches, 'active_private_pointer': 0x80136FD8,
            'resident_players': 0x80126EC0, 'private_stride': 0xBD0,
            'normal_collection_hook_enabled': True, 'player_clear_hook_enabled': True,
            'catalogue_menu_enabled': False, 'save_format_changed': False,
            'foreign_import_collection': 'stops before ownership is lost; Controller Pak transport pending',
            'ordinary_acquisition_tested': False}
