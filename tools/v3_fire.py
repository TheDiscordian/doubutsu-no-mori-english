"""Build complete native fire callbacks against the installed fire-audio source."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_camping_actor_art import ACTORS, prepare
from v3_tent_model import ART, ART_SHA

BASE = ROOT / 'build/v3-fire-sound-runtime-01'
BASE_SHA = 'f3d055a74c2172029755b6be39e84b29658a17e83ef599a4f2fe6453570cb48f'
RAM, VTABLE, LIMIT = 0x80483800, 0x80483FC0, 0x80483FF0
ENTRIES = tuple('af_v3_' + name + '_' + kind for name in ('campfire', 'bonfire') for kind in ('ct', 'mv', 'dw'))
ENGINE = (
    ('cKF_SkeletonInfo_R_ct', 0x80052228, 0x64, '89b02c686de585e969871790903fbd01eca99e3b2f8a6ac99b5317987b839601'),
    ('cKF_SkeletonInfo_R_init_standard_repeat', 0x80052408, 0x7C, 'de4e2b34e720a6f78e66f5b0651e8d174335fb74f06bd440627a1f6c126c1441'),
    ('cKF_SkeletonInfo_R_play', 0x800528D4, 0x44C, 'd61ab4c7ec8317bd17cbd40bcaff2c6caba26664d2148d7cddb4001d0c75efbf'),
    ('cKF_Si3_draw_R_SV', 0x800530D8, 0x98, 'dd1a961d11ab54f90768fb216515f2ba0cc573fed812cda327cb00c4eaa5491b'),
    ('Lib_SegmentedToVirtual', 0x8009ADA8, 0x38, '02719768276bd0e3d67427f499e82894544c7242161fb2c8e9c24e25e5d103cf'),
    ('sAdo_OngenPos', 0x800D1D08, 0x50, '78323a51c1aef53c0fe0f9d1c5a890e800ee8eb0fc95ce0f4e38236aefab65c8'),
    ('Matrix_Position_Zero', 0x800E14D4, 0x28, '842a9b3c60654095b12638c2b62a7dcd3eee6cbce7dbf01adf6b4b9f5e18dfd1'),
    ('Matrix_push', 0x800E020C, 0x38, '14ae3afe88afa8ed8059cf26d63c4547c88eb12dd487136a34f97464d755c140'),
    ('Matrix_pull', 0x800E0244, 0x1C, 'f2af6285ca1826af36f4e9c74c7321cc031b05561ba358ff34cbe152036bddb2'),
    ('Matrix_translate', 0x800E0314, 0x108, '767212be165dde7a9be2467ffb03b98a80af114e9ad9d352e21998c6f9981ca2'),
    ('Matrix_mult', 0x800E02BC, 0x58, '92aba93795d819578778bd24a1119015dcbd067bcf08f639677f2e1155e3f11d'),
    ('Matrix_RotateY', 0x800E0698, 0x19C, '6b345ca225909a847e54ff3157e1a980fc98e823e4e8c873aeedca0dfef5cd2e'),
    ('Matrix_scale', 0x800E041C, 0xE4, '27f376ad3dc5687beaa39c0135d9bf172a320fed03d06bd42f973914ecf71a19'),
    ('_Matrix_to_Mtx', 0x800E139C, 0x28, '890b20641a22da5dc2211251fb4c70f6144118f6f1c093ce1ce0f89af325120e'),
    ('osWritebackDCache', 0x8002FE00, 0x74, '5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'),
)
SOURCES = ('tools/v3_fire.py', 'overlays/v3/fire.c', 'overlays/v3/fire.ld')


def native_contract(original, current):
    verified_rom(original)
    if sha256(current) != BASE_SHA:
        raise ValueError('Fire callbacks require the complete installed fire audio')
    old, new = by_vrom(original), by_vrom(current)
    result = []
    for name, address, size, digest in ENGINE:
        vrom, ram = (0x1060, 0x80025C60) if name == 'osWritebackDCache' else (CODE_VROM, CODE_RAM)
        at = address - ram
        raw = old[vrom].extract(original)[at:at + size]
        if sha256(raw) != digest or new[vrom].extract(current)[at:at + size] != raw:
            raise ValueError('Changed complete native fire dependency: ' + name)
        result.append({'name': name, 'address': address, 'bytes': size, 'sha256': digest})
    contexts = (
        ('catalogue_draw_null_room', 0x7A28F0, 0x3970000, 0x808A6100, 0x808A7814, 0xD0,
         'aa1cd409237c29058fb12a0b15225172d7e25c3cbde53509bf87231fa3a790c1'),
        ('room_draw_owner_argument', 0x82D7F0, 0x82D7F0, 0x80936710, 0x80946F40, 0xE4,
         'ef2702cf6e4dfba3ad3e09cf2aa01ea5feaf4484e1b0dc32e47244214129698c'),
        ('native_actor_scale', 0x82D7F0, 0x82D7F0, 0x80936710, 0x80937BE4, 0x98,
         '7c2a1ab89336db5b89df3c5c60f766698562b8635cff2ce1bd31dbc4c5822702'),
    )
    for name, before, after, ram, address, size, digest in contexts:
        at = address - ram
        raw = old[before].extract(original)[at:at + size]
        if sha256(raw) != digest or new[after].extract(current)[at:at + size] != raw:
            raise ValueError('Changed fire caller/actor contract: ' + name)
        result.append({'name': name, 'address': address, 'bytes': size, 'sha256': digest})
    return {'source_sha256': BASE_SHA, 'blocks': result,
        'actor_bytes': 0x740, 'keyframe_offset': 0x134, 'scale_offset': 0x714,
        'catalogue_context': 'null room callback argument',
        'room_frame_offset': 0x1EA0, 'catalogue_frame_offset': 0xA0,
        'billboard_offset': 0x1E5C, 'frame_allocation_bytes': 176,
        'maximum_alignment_padding_bytes': 15,
        'opaque_command_bytes': 40, 'translucent_command_bytes': 40,
        'joint_matrix_bytes': 128, 'ordinary_heap_bytes': 0, 'shared_writable_bytes': 0,
        'bonfire_odd_frame_quantisation_texels': 0.125, 'scroll_drift_texels': 0}


def asset_contract(rel, symbols):
    raw = (ART / 'art.json').read_bytes()
    if sha256(raw) != ART_SHA:
        raise ValueError('Changed complete camping actor conversion')
    objects = json.loads(raw)['objects'][:2]
    assets, metadata = [], []
    for actor, row, offsets, size in zip(ACTORS, objects,
            ((0x1360, 0x1E20, 0x1F00, 0x1F14, 0x1F38), (0x1070, 0x1660, 0x1748, 0x175C, 0x1780)),
            (8000, 6032)):
        body, resources, _, models, rig, details = prepare(rel, symbols, actor)
        asset = (ART / row['object_file']).read_bytes()
        actual = tuple(m['native_offset'] for m in row['models']) + tuple(
            row['headers'][name]['native_offset'] for name in ('animation', 'joints', 'skeleton'))
        if (len(asset) != size or sha256(asset) != row['object_sha256']
                or asset[:len(body)] != body or actual != offsets
                or not rig or any(row[k] != v for k, v in details.items())
                or row['joints'] != 3 or row['displayed_joints'] != 2
                or row['frame_count'] != 101 or row['keyframe_tracks'] != 0
                or row['billboard_joint'] != 2):
            raise ValueError('Changed full fire model, rig, or source behaviour')
        assets.append(asset); metadata.append(details)
    return assets, metadata


def profiles(vroms, code, compiled):
    if len(vroms) != 2 or not code or len(code) > VTABLE - RAM or len(code) != compiled['bytes'] or sha256(code) != compiled['sha256']:
        raise ValueError('Fire profiles lack complete bounded callbacks')
    entries = [compiled['symbols'][name] for name in ENTRIES]
    if entries[0] != RAM or any(a & 3 or not RAM <= a < RAM + len(code) for a in entries):
        raise ValueError('Fire entry leaves the complete compiled code')
    result = []
    for i, (vrom, size) in enumerate(zip(vroms, (8000, 6032))):
        if vrom & 0x1FFF or not 0x2460000 <= vrom <= 0x25EE000:
            raise ValueError('Invalid fire object reservation')
        table = struct.pack('>5I', *entries[i * 3:i * 3 + 3], 0, 0)
        native = (struct.pack('>4I', vrom, vrom + size, 0x06000000, 0x06000000 + size)
                  + bytes(32) + bytes.fromhex(ACTORS[i].scalar_hex) + struct.pack('>I', VTABLE + i * 24))
        result.append((native, table))
    if abs(vroms[0] - vroms[1]) < 0x2000:
        raise ValueError('Fire object reservations overlap')
    return result


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    contract = native_contract((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes())
    assets, metadata = asset_contract((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    output.mkdir(parents=True)
    code, compiled = compile_part('fire', output / 'code')
    engine = {a: n for n, a, _, _ in ENGINE}
    targets = {**engine, **{a: n for n, a in compiled['symbols'].items() if RAM <= a < RAM + len(code)}}
    calls = []
    for at in range(0, len(code), 4):
        word = struct.unpack_from('>I', code, at)[0]
        if word >> 26 in (2, 3):
            address = 0x80000000 | ((word & 0x3FFFFFF) << 2)
            if address not in targets:
                raise ValueError('Unreviewed absolute fire callback dependency')
            calls.append({'offset': at, 'address': address, 'symbol': targets[address]})
    if not set(engine).issubset({r['address'] for r in calls}):
        raise ValueError('Missing fire animation, matrix, or audio dependency')
    native = profiles((0x2468000, 0x246A000), code, compiled)
    report = {'format': 'AFV3-FIRE-CALLBACKS-1', 'code': compiled,
        'native_contract': contract, 'source_metadata': metadata,
        'art_report_sha256': ART_SHA, 'object_sha256': [sha256(a) for a in assets],
        'calls': calls, 'profiles_hex': [n.hex() for n, _ in native],
        'vtables_hex': [t.hex() for _, t in native], 'vtables_ram': [VTABLE, VTABLE + 24],
        'proposed_objects_vrom': [0x2468000, 0x246A000],
        'runtime_installed': False, 'web_patcher_enabled': False, 'saved_format_changed': False,
        'source_sha256': {p: sha256((ROOT / p).read_bytes()) for p in SOURCES}}
    write_new(output / 'callbacks.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({'bytes': result['code']['bytes'], 'sha256': result['code']['sha256']}))
