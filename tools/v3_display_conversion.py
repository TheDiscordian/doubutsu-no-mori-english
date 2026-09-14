"""Bind shared pocket/mannequin conversions without replacing native bodies."""
import struct

from aflib import CODE_RAM, sha256
from v3_npc_clothing import guard_incoming

ABI, CODE, BRIDGES, END = 43, 0x6270, 0x65E0, 0x6600
SOURCES = ('tools/v3_display_conversion.py', 'overlays/v3/display_conversion.c',
           'overlays/v3/display_conversion.ld')
ENTRIES = (
    (0x800BEFCC, 0x800BF10C, 'display', 'afa400003084ffff',
     'cc2f486a63f4266eb6249f27362d1365ba116b56e14891a8447d0a157b7ac8bb'),
    (0x800BF10C, 0x800BF230, 'pocket', '27bdffe8afa40018',
     'f022be17120922ce15db644ff63308dff25e150537320bed7659bbc3ac6602e5'),
)


def install(code, blob, helper, compiled, display, readers):
    symbols = compiled['symbols']
    if (len(blob) != 0xC000 or any(blob[CODE:END]) or not helper
            or len(helper) > BRIDGES-CODE or len(helper) != compiled['bytes']
            or sha256(helper) != compiled['sha256']
            or display['code']['bytes'] != 112
            or sha256(blob[0x6200:CODE]) != display['code']['sha256']
            or sha256(blob[0x6C00:0x6C00+readers['code']['bytes']]) != readers['code']['sha256']
            or symbols['af_v3_display_pocket_item'] != readers['code']['symbols']['af_v3_display_pocket_item']
            or symbols['af_v3_furniture_import_profile'] != 0x80465000
            or symbols['af_v3_room_display_item'] != 0x80460000+CODE):
        raise ValueError('Conversion reservation or selected display dependencies changed')
    guard_incoming(code, len(code), CODE_RAM,
                   [(entry-CODE_RAM, 8) for entry, *_ in ENTRIES])
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    hooks = []
    for i, (entry, end, kind, prefix, digest) in enumerate(ENTRIES):
        at, bridge = entry-CODE_RAM, 0x80460000+BRIDGES+i*16
        before, target = bytes(code[at:at+8]), symbols['af_v3_room_'+kind+'_item']
        if (sha256(code[at:end-CODE_RAM]) != digest or before.hex() != prefix
                or symbols['af_v3_prior_'+kind+'_item'] != bridge
                or not 0x80460000+CODE <= target < 0x80460000+CODE+len(helper)
                or target & 3):
            raise ValueError('Changed complete native conversion or compiled bridge')
        stub = before+struct.pack('>2I', jump(entry+8), 0)
        after = struct.pack('>2I', jump(target), 0)
        blob[BRIDGES+i*16:BRIDGES+(i+1)*16] = stub
        code[at:at+8] = after
        hooks.append({'entry': entry, 'end': end, 'kind': kind, 'target': target,
            'bridge': bridge, 'before': before.hex(), 'after': after.hex(),
            'bridge_bytes': stub.hex(), 'native_function_sha256': digest})
    blob[CODE:CODE+len(helper)] = helper
    return {'code': compiled, 'hooks': hooks, 'pocket_item_id': '34BF',
        'display_item_id': '3AFC', 'selected_profile_required': True,
        'native_conversion_bodies_retained': True, 'global_conversion_enabled': True,
        'ordinary_placement_pickup_tested': False, 'placed_save_reload_tested': False,
        'saved_formats_and_profile_changed': False}
