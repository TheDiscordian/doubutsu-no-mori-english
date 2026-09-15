"""Build complete native tent-light callbacks and verify their instance contract."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_camping_actor_art import ACTORS, prepare

RAM, LIMIT, VTABLE = 0x80483400, 0x80483800, 0x80483700
ART = ROOT / 'build/v3-camping-actor-art-01'
ART_SHA = 'f94d22e36cf9b774ae892a9e3492e3bda44267c8e35d043f62d053157b92ece9'
ASSET_SHA = 'b56aeeb6e542e9742706ca510e054fdb81f87a82e91b9ff684ed669d32c14af7'
BASE = ROOT / 'build/v3-camping-runtime-01'
BASE_SHA = '3967dedabca6e65a97f57273028aaa19b0b24ed72b405f2498d5a4fce6a1cd29'
ENTRIES = tuple('af_v3_tent_model_' + name for name in ('ct', 'mv', 'dw', 'dt'))
ENGINE = {'_Matrix_to_Mtx': 0x800E139C, 'osWritebackDCache': 0x8002FE00}
BLOCKS = (
    ('constructor_rig_guard_and_callback', 0x80938124, 0xB8,
     '5b61ae6fa0d9d8dc3043670b5b863900a8ebfae0807b4c87a3376dd9941e5542'),
    ('move_rig_texture_guards_and_callback', 0x80944F18, 0xB8,
     'b76be79808f533225c58ced93c209126125b1dd60cf4d7695f566545074cf162'),
    ('draw_rig_guard', 0x80946E68, 0xD8,
     '0855843fa728d7efbb13bee407ba19e51f3cc6bb203367a133e4592716998295'),
    ('native_draw_callback', 0x80946F40, 0xE4,
     'ef2702cf6e4dfba3ad3e09cf2aa01ea5feaf4484e1b0dc32e47244214129698c'),
    ('switch_toggle', 0x80936E74, 0x24,
     '4dbc0892ba2cebfe2ee0a343779b9a56be3ea59035edac1eb33ee403d2b4061b'),
)
SOURCES = ('tools/v3_tent_model.py', 'overlays/v3/tent_model.c', 'overlays/v3/tent_model.ld')


def native_contract(original, current):
    verified_rom(original)
    if sha256(current) != BASE_SHA:
        raise ValueError('Tent callbacks require the current checked ABI 68 cartridge')
    old, new = by_vrom(original), by_vrom(current)
    room = old[0x82D7F0].extract(original)
    room_now = new[0x82D7F0].extract(current)
    if sha256(room) != '4c67db43a7cebe9a35119621a13bac2fe8cb977cd7ab894b6b5e6b08e1d296a0':
        raise ValueError('Changed complete original furniture owner')
    blocks = []
    for name, address, size, digest in BLOCKS:
        at = address - 0x80936710
        if sha256(room[at:at + size]) != digest or room_now[at:at + size] != room[at:at + size]:
            raise ValueError('Changed tent native instance contract: ' + name)
        blocks.append({'name': name, 'address': address, 'bytes': size, 'sha256': digest})
    code = old[CODE_VROM].extract(original)
    current_code = new[CODE_VROM].extract(current)
    at = ENGINE['_Matrix_to_Mtx'] - CODE_RAM
    if (sha256(code[at:at + 40]) != '890b20641a22da5dc2211251fb4c70f6144118f6f1c093ce1ce0f89af325120e'
            or current_code[at:at + 40] != code[at:at + 40]):
        raise ValueError('Changed native matrix conversion')
    # Boot also contains translated fault/startup changes. Pin the actual cache
    # function, not unrelated bytes in that owner.
    boot = old[0x1060].extract(original)
    boot_now = new[0x1060].extract(current)
    at = ENGINE['osWritebackDCache'] - 0x80025C60
    cache = boot[at:at + 116]
    if (sha256(cache) != '5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'
            or boot_now[at:at + 116] != cache):
        raise ValueError('Changed native cache-writeback function')
    return {'current_source_sha256': BASE_SHA, 'blocks': blocks,
        'actor_bytes': 0x740, 'switch_offset': 0x12C, 'private_fade_offset': 0x1A4,
        'private_fade_bytes': 4, 'requires_null_generic_rig': True,
        'requires_null_texture_animation': True, 'opaque_head_offset': 0x298,
        'opaque_tail_offset': 0x29C, 'matrix_and_palette_bytes': 96,
        'draw_command_bytes': 48, 'maximum_draw_allocation_bytes': 160,
        'palette_alignment': 32, 'palette_lifetime': 'submitted graphics frame',
        'heap_allocation_bytes': 0, 'shared_writable_state_bytes': 0,
        'cache_function_sha256': sha256(cache)}


def asset_contract(rel, symbols):
    raw = (ART / 'art.json').read_bytes()
    if sha256(raw) != ART_SHA:
        raise ValueError('Changed complete camping actor conversion')
    actor = ACTORS[2]
    prepared = prepare(rel, symbols, actor)
    body, resources, offsets, models, rig, details = prepared
    model = json.loads(raw)['objects'][2]
    asset = (ART / model['object_file']).read_bytes()
    if (actor.item != 0x336C or rig or len(asset) != 4288 or sha256(asset) != ASSET_SHA
            or asset[:len(body)] != body
            or model['donor_profile_scalar_hex'] != '417b33333c23d70a0400000000008000'
            or [(m['part'], m['native_offset']) for m in model['models']] !=
            [('green', 0xC50), ('body', 0xD18), ('detail', 0xE00), ('light', 0xFF0)]
            or [(r['symbol'], r['native_offset']) for r in resources if r['kind'] == 'rgba16'] !=
            [('int_tak_tent_pal', 0), ('int_tak_tent_on_pal', 32), ('int_tak_tent_off_pal', 64)]):
        raise ValueError('Changed tent parts, palette endpoints, or callback-owned profile')
    on, off = struct.unpack_from('>16H', asset, 32), struct.unpack_from('>16H', asset, 64)
    if [i for i in range(16) if on[i] != off[i]] != [7] or (on[7], off[7]) != (0xFFE5, 1):
        raise ValueError('Unreviewed tent light colour conversion')
    return asset, details


def profile(vrom, code, compiled):
    if (vrom & 0x1FFF or not 0x0244E000 <= vrom <= 0x025EE000
            or not code or len(code) > VTABLE - RAM or len(code) != compiled['bytes']
            or sha256(code) != compiled['sha256']):
        raise ValueError('Tent profile lacks a complete bounded native callback')
    entries = [compiled['symbols'][name] for name in ENTRIES]
    if entries[0] != RAM or any(a & 3 or not RAM <= a < RAM + len(code) for a in entries):
        raise ValueError('Tent callback table leaves checked code')
    table = struct.pack('>5I', *entries, 0)
    native = (struct.pack('>4I', vrom, vrom + 4288, 0x06000000, 0x060010C0)
              + bytes(32) + bytes.fromhex('417b33333c23d70a0400000000008000')
              + struct.pack('>I', VTABLE))
    if len(native) != 68 or native[0x28:0x30] != bytes(8):
        raise ValueError('Tent private state would collide with generic animation')
    return native, table


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    contract = native_contract((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes())
    asset, details = asset_contract((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    output.mkdir(parents=True)
    code, compiled = compile_part('tent_model', output / 'code')
    targets = {v: k for k, v in ENGINE.items()}
    calls = []
    for at in range(0, len(code), 4):
        word = struct.unpack_from('>I', code, at)[0]
        if word >> 26 in (2, 3):
            address = 0x80000000 | ((word & 0x3FFFFFF) << 2)
            if word >> 26 != 3 or address not in targets:
                raise ValueError('Unreviewed absolute tent callback dependency')
            calls.append({'offset': at, 'address': address, 'symbol': targets[address]})
    if {r['address'] for r in calls} != set(targets):
        raise ValueError('Incomplete tent matrix/cache dependencies')
    native, table = profile(0x0244E000, code, compiled)
    report = {'format': 'AFV3-TENT-MODEL-CALLBACKS-1', 'code': compiled,
        'native_contract': contract, 'source_metadata': details,
        'art_report_sha256': ART_SHA, 'object_sha256': sha256(asset),
        'external_calls': calls, 'profile_hex': native.hex(), 'vtable_hex': table.hex(),
        'vtable_ram': VTABLE, 'proposed_object_vrom': 0x0244E000,
        'runtime_installed': False, 'web_patcher_enabled': False,
        'saved_format_changed': False,
        'source_sha256': {p: sha256((ROOT / p).read_bytes()) for p in SOURCES}}
    write_new(output / 'callbacks.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({'bytes': result['code']['bytes'], 'sha256': result['code']['sha256'],
                      'runtime_installed': False}))
