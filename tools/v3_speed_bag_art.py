"""Convert the supplied speed bag's complete model and native-compatible rig."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from apply_translation import write_new
from gc_names import rel_sections
from map_artwork import compile_commands
from title_assets import pack4, untile
from toolchain import IMAGE
from v3_furniture_art import SEGMENT, command_source, parse_model, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags, symbol_span

ITEM = 0x3350
STEM = 'int_ike_prores_punch01'
PROFILE = 'iam_ike_prores_punch01'
TEXTURES = (('pole3', 16, 8), ('base2', 16, 32), ('pole2', 32, 8),
            ('pole1', 32, 8), ('base3', 32, 8), ('base1', 32, 32),
            ('pole4', 16, 8), ('punch1', 16, 16))
RIG = {'flags': ('cKF_ckcb_r_'+STEM+'_tbl', 2),
       'counts': ('cKF_kn_'+STEM+'_tbl', 6),
       'constants': ('cKF_c_'+STEM+'_tbl', 12),
       'keys': ('cKF_ds_'+STEM+'_tbl', 144),
       'animation': ('cKF_ba_r_'+STEM, 20),
       'joints': ('cKF_je_r_'+STEM+'_tbl', 24),
       'skeleton': ('cKF_bs_r_'+STEM, 8)}
MODEL_SYMBOLS = {'base': ('int_ike_prores_punch_base_model', 320),
                 'ball': ('int_ike_prores_punch_ball_model', 128)}


def validate_animation(flags, counts, constants, keys):
    """Check native keyframe traversal sizes and every track's frame bounds."""
    if flags != bytes((0, 7)) or len(counts) != 6 or len(constants) != 12 or len(keys) != 144:
        raise ValueError('Changed speed-bag animation channels')
    lengths = struct.unpack('>3h', counts)
    if lengths != (2, 11, 11):
        raise ValueError('Changed speed-bag animation key counts')
    tracks, start = [], 0
    for length in lengths:
        values = list(struct.iter_unpack('>3h', keys[start:start+length*6]))
        frames = [row[0] for row in values]
        if frames[0] != 1 or frames[-1] != 69 or any(a >= b for a, b in zip(frames, frames[1:])):
            raise ValueError('Speed-bag keyframes escape their ordered duration')
        tracks.append({'keys': length, 'first_frame': frames[0], 'last_frame': frames[-1]})
        start += length*6
    if start != len(keys):
        raise ValueError('Unaccounted speed-bag animation keys')
    return tracks


def prepare(rel, symbol_bytes):
    verify_sources(rel, symbol_bytes)
    symbols = symbol_bytes.decode()
    sections = rel_sections(rel)
    base = sections[5][0]

    def source(name, expected):
        at, size = symbol_span(symbols, name)
        if size != expected:
            raise ValueError('Changed speed-bag source size: '+name)
        return at, rel[base+at:base+at+size]

    profile_at, raw_profile = source(PROFILE, 52)
    table_at, raw_table = source('fIPPnch_func', 20)
    if (raw_profile != bytes(32)+struct.pack('>ff6BH', 40, 0.01, 4, 0, 0, 1, 0, 0, 0)+bytes(4) or
            raw_table != bytes(20) or data_pointers(rel, profile_at, 52) != {profile_at+48: table_at}):
        raise ValueError('Changed speed-bag profile or callback table')
    callbacks, targets = [], {}
    for slot, name in enumerate(('fIPPnch_ct', 'fIPPnch_mv', 'fIPPnch_dw')):
        rows = re.findall(r'^'+name+r' = \.text:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M)
        if len(rows) != 1:
            raise ValueError('Missing speed-bag callback symbol')
        at, size = (int(n, 16) for n in rows[0])
        if at % 4 or not size or size % 4 or at+size > sections[1][1]:
            raise ValueError('Speed-bag callback escapes donor code')
        targets[table_at+slot*4] = at
        callbacks.append({'symbol': name, 'text_offset': at, 'bytes': size,
                          'source_sha256': sha256(rel[sections[1][0]+at:sections[1][0]+at+size])})
    if data_pointers(rel, table_at, 20, expected_section=1) != targets:
        raise ValueError('Speed-bag callbacks do not resolve to the actual donor functions')
    qualities = re.findall(r'^furniture_quality = \.data:0x([0-9A-F]+);[^\n]* size:0x13C8 ', symbols, re.M)
    if sorted(int(n, 16) for n in qualities) != [0x39FB4, 0x7B5B0]:
        raise ValueError('Changed donor furniture-quality tables')
    for table in qualities:
        entry = int(table, 16)+(1024+(ITEM-0x3000)//4)*4
        if data_pointers(rel, entry, 4) != {entry: profile_at}:
            raise ValueError('Speed-bag donor identity/profile mismatch')
    _, names = source('ftrName2_table', 242*16)
    if names[(ITEM-0x3000)//4*16:((ITEM-0x3000)//4+1)*16] != b'speed bag       ':
        raise ValueError('Speed-bag donor name mismatch')

    body, resources, offsets = bytearray(), [], {}

    def append(name, size, convert, alignment=32):
        at, raw = source(name, size)
        if data_pointers(rel, at, size):
            raise ValueError('Unexpected pointer in speed-bag raw arrays')
        converted = convert(raw)
        if len(converted) != size:
            raise ValueError('Speed-bag conversion changes an array size')
        body.extend(bytes(-len(body) % alignment))
        offset = len(body)
        offsets[at] = offset
        body.extend(converted)
        resources.append({'symbol': name, 'donor_offset': at, 'native_offset': offset,
                          'bytes': size, 'source_sha256': sha256(raw),
                          'output_sha256': sha256(converted)})
        return at

    palette = append(STEM+'_pal', 32, native_palette)
    ball_palette = append(STEM+'_punch1_tex_pic_ci4_pal', 32, native_palette)
    textures = {}
    for suffix, width, height in TEXTURES:
        at = append(STEM+'_'+suffix+'_tex_txt', width*height//2,
                    lambda raw, w=width, h=height: pack4(untile(raw, w, h, 4)))
        textures[at] = (width, height)
    vertex = append(STEM+'_v', 62*16, lambda raw: normalise_vertex_flags(raw)[0])
    rig = {label: source(*spec) for label, spec in RIG.items()}
    tracks = validate_animation(*(rig[label][1] for label in ('flags', 'counts', 'constants', 'keys')))
    for label in ('flags', 'counts', 'constants', 'keys'):
        append(*RIG[label], lambda raw: raw, alignment=4)
    models = {}
    for label, (name, size) in MODEL_SYMBOLS.items():
        at, raw = source(name, size)
        models[label] = {'symbol': name, 'donor_offset': at, 'source_sha256': sha256(raw),
                        'rows': parse_model(raw, at, data_pointers(rel, at, size),
                            ball_palette if label == 'ball' else palette, textures,
                            vertex, 62*16, speed_bag=True)}
    animation_at, animation = rig['animation']
    expected = {animation_at+n*4: rig[label][0]
                for n, label in enumerate(('flags', 'keys', 'counts', 'constants'))}
    if animation != bytes(16)+struct.pack('>hh', -1, 69) or data_pointers(rel, animation_at, 20) != expected:
        raise ValueError('Changed speed-bag animation header or dependencies')
    joints_at, joints = rig['joints']
    if (joints != struct.pack('>IBB3hIBB3h', 0, 1, 0, 800, 6508, 800, 0, 0, 0, 0, 0, 0) or
            data_pointers(rel, joints_at, 24) != {
                joints_at: models['base']['donor_offset'], joints_at+12: models['ball']['donor_offset']}):
        raise ValueError('Changed speed-bag joint topology, translation, or models')
    skeleton_at, skeleton = rig['skeleton']
    if skeleton != bytes.fromhex('0202000000000000') or data_pointers(rel, skeleton_at, 8) != {skeleton_at+4: joints_at}:
        raise ValueError('Changed speed-bag skeleton')
    return bytes(body), resources, offsets, models, rig, {
        'callbacks': callbacks, 'profile_source_sha256': sha256(raw_profile),
        'animation_tracks': tracks, 'frame_count': 69, 'joints': 2, 'displayed_joints': 2,
        'donor_profile_scalar_hex': raw_profile[32:48].hex(),
        'behaviour_installed': False}


def finish(body, offsets, models, rig, compiled):
    """Bind every model/rig pointer to the native object's segment-six offsets."""
    if set(compiled) != set(MODEL_SYMBOLS):
        raise ValueError('Missing speed-bag compiled model')
    asset, mapped, records = bytearray(body), dict(offsets), []
    for label, model in models.items():
        code = compiled[label]
        if not code or len(code) % 8 or code[-8:] != struct.pack('>II', 0xDF000000, 0):
            raise ValueError('Invalid speed-bag compiled model')
        asset.extend(bytes(-len(asset) % 8))
        at = len(asset)
        mapped[model['donor_offset']] = at
        asset.extend(code)
        records.append({'part': label, 'symbol': model['symbol'], 'native_offset': at,
                        'bytes': len(code), 'source_sha256': model['source_sha256'],
                        'output_sha256': sha256(code),
                        'triangles': sum(len(row.get('triangles', ())) for row in model['rows'])})
    headers, relocations = {}, []
    for label in ('animation', 'joints', 'skeleton'):
        source_at, raw = rig[label]
        if label == 'animation':
            references = {n*4: rig[key][0] for n, key in enumerate(('flags', 'keys', 'counts', 'constants'))}
        elif label == 'joints':
            references = {0: models['base']['donor_offset'], 12: models['ball']['donor_offset']}
        else:
            references = {4: rig['joints'][0]}
        fixed = bytearray(raw)
        asset.extend(bytes(-len(asset) % 4))
        at = len(asset)
        for offset, target in references.items():
            if target not in mapped or not 0 <= mapped[target] < at or fixed[offset:offset+4] != bytes(4):
                raise ValueError('Unbound speed-bag native pointer')
            struct.pack_into('>I', fixed, offset, SEGMENT+mapped[target])
            relocations.append({'offset': at+offset, 'target_offset': mapped[target]})
        mapped[source_at] = at
        asset.extend(fixed)
        headers[label] = {'native_offset': at, 'bytes': len(fixed),
                          'source_sha256': sha256(raw), 'output_sha256': sha256(fixed)}
    asset.extend(bytes(-len(asset) % 16))
    if len(asset) > 0x1400:
        raise ValueError('Complete animated speed bag exceeds a native furniture bank')
    return bytes(asset), records, headers, relocations


def build(rel, symbols, out):
    body, resources, offsets, models, rig, details = prepare(rel, symbols)
    out.mkdir(parents=True, exist_ok=False)
    source, sections = command_source(models, offsets)
    source_file = out/'commands.c'
    write_new(source_file, source.encode())
    compiled = compile_commands(out/'gbi', source_file, sections)
    asset, model_report, headers, pointers = finish(body, offsets, models, rig, compiled)
    write_new(out/'speed-bag.n64obj.bin', asset)
    report = {'format': 'AFV3-SPEED-BAG-ART-1', 'converter_version': 1,
        'id': f'{DONOR}/item/{ITEM:04X}', 'name': 'speed bag', 'donor': DONOR,
        'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA, 'compiler_image': IMAGE,
        'target_item_id': None, 'runtime_installed': False, 'selectable': False,
        'object_file': 'speed-bag.n64obj.bin', 'object_bytes': len(asset), 'object_sha256': sha256(asset),
        'resources': resources, 'models': model_report, 'headers': headers, 'pointers': pointers,
        'segment': f'{SEGMENT:08X}', 'bank_capacity': 0x1400,
        'command_source_sha256': sha256(source.encode()), **details}
    write_new(out/'art.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh output directory; existing artifacts are preserved')
    report = build(read_donor(args.disc)['rel'], args.symbols.read_bytes(), args.output.resolve())
    print(json.dumps({'output': str(args.output), 'bytes': report['object_bytes'],
                      'sha256': report['object_sha256'], 'runtime_installed': False}, indent=2))


if __name__ == '__main__':
    main()
