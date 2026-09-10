"""Replace the beige grid panel with the supplied English GC keyboard frame."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from artwork_matches import data_pointers, converted
from keyboard_grid_labels import LABELS, encode_label
from letter_ui_fix import compile_part
from stall_model_source import packed
from title_start_fix import reconstruct
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '0032a12d0c84810b89e2186dab524130b7f09506c6ab163c27c357fddf1d8ae3'
DRAW_SHA = '9daf082114975529b21eb93a5bc4a9ce1aaf2840747cfa178ccc3d6092f7693d'
RAM = 0x80885140
SPEC = {'vrom': 0x3940000, 'reloc': 0x3948000, 'ram': RAM,
    'new_vrom': 0x3E70000, 'new_reloc': 0x3E80000, 'owner_at': 0x2B50,
    'sha': '231fc18359e3ae7c0031aa4571a436f7cdb18c0898a5adfbbbeac94c5149df9d',
    'reloc_sha': 'db23c6b194a7beef0221ab3c235b99fe14740311fa120ad9df6a35f471fe570a',
    'imports': {'af_grid_owned': RAM+24620, 'af_grid_apology': RAM+24744,
        'af_grid_context': RAM+28608, 'af_grid_keycap': RAM+28256,
        'af_grid_tables': RAM+27776, 'af_grid_key': RAM+23388,
        'af_hboard_code_width': 0x8009028C, 'af_hboard_font_line': 0x80090E98},
    'calls': {0x808882D8: ('af_bg_editor_draw', RAM+25748)}}
POOL_AT, POOL_BEFORE, POOL_EXTRA = 0x800C4B10, 0x25CE5620, 0x2000


def source_hashes():
    paths = [ROOT/'overlays/keyboard_background/panel.c', ROOT/'overlays/keyboard_grid/draw.c',
             ROOT/'overlays/keyboard_grid/editor.h', ROOT/'overlays/keyboard_grid/core.h',
             ROOT/'overlays/hboard/editor.h', ROOT/'runtime/hboard_editor.h']
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in paths}


def donor(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied keyboard background source')
    for name, at, size in (('kai_sousa_mojiban_tex', 0x4124C0, 0x400),
                          ('kai_sousa_mojiban2_tex', 0x4128C0, 0x400),
                          ('kai_sousa_mojibanT_model', 0x420730, 0x68)):
        if symbols.decode().count(f'{name} = .data:0x{at:08X}; // type:object size:0x{size:X} ') != 1:
            raise ValueError('Missing exact GC keyboard frame binding')
    model = rel[DATA_BASE+0x420730:DATA_BASE+0x420798]; pointers = data_pointers(rel)
    if sha256(model) != 'f2f1ab5699db39e69d88182a8224a27dcd3bf30851c37354636fdbd84ca54929':
        raise ValueError('Changed GC keyboard frame material')
    if {a: pointers[a] for a in (0x42074C, 0x42075C, 0x420774)} != {
            0x42074C: 0x4128C0, 0x42075C: 0x41FFF0, 0x420774: 0x4124C0}:
        raise ValueError('Changed GC frame textures or geometry')
    for at in (0x420748, 0x420770):
        if model_texture_shape(rel[DATA_BASE+at:DATA_BASE+at+8]) != (32, 32, 3, 1):
            raise ValueError('Changed GC frame pixel format')
    if packed(model[0x30:0x40], 16) != [(0,1,2),(3,0,2),(4,5,6),(7,4,6)] or \
       packed(model[0x50:0x60], 16) != [(8,9,10),(9,11,10),(12,13,14),(13,15,14)]:
        raise ValueError('Changed GC frame corner assignment')
    values = [converted(rel[DATA_BASE+a:DATA_BASE+a+1024], 32, 32, 'ia8', 8) for a in (0x4124C0, 0x4128C0)]
    return values, {'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'model_sha256': sha256(model), 'source_textures': ['004124C0', '004128C0'],
        'converted_sha256': [sha256(v) for v in values], 'format': 'linear N64 IA8',
        'native_panel_bounds': [42, 113, 278, 227], 'donor_bounds': [55, 129, 235, 202],
        'adaptation': 'Four GC corner textures/UV directions, enlarged around native control hints',
        'key_positions_and_input_unchanged': True}


def draw_source():
    data = (ROOT/'overlays/keyboard_grid/draw.c').read_text()
    if sha256(data.encode()) != DRAW_SHA: raise ValueError('Changed retained grid drawing source')
    start = data.index('static Gfx *rectangle('); end = data.index('void af_grid_editor_draw(', start)
    # Mechanical derivation retains key positions, input ownership, and font calls.
    data = data[:start]+data[end:]
    data = data.replace('void af_grid_editor_draw(', 'void af_bg_editor_draw(', 1)
    if data.count('g=rectangle(g,') != 1: raise ValueError('Missing unique beige panel call')
    data = data.replace('g=rectangle(g,', 'g=af_bg_panel(g,', 1)
    return ('#include "/source/overlays/keyboard_background/panel.c"\n'+data).encode()


def build(native, base, rel, symbols, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA: raise ValueError('Background requires the complete letter UI predecessor')
    before = source_hashes(); frames, profile = donor(rel, symbols)
    texture_source = '\n'.join('static const unsigned char af_bg_frame_'+name+
        '[1024] __attribute__((aligned(8))) = {'+','.join(f'0x{v:02X}' for v in data)+'};'
        for name, data in zip(('a', 'b'), frames)).encode()+b'\n'
    data, relocation, compiled = compile_part('background', base, out/'editor', spec=SPEC,
        source='/out/helper.c', generated={'helper.c': draw_source(), 'textures.inc': texture_source},
        flags=('-D_LANGUAGE_C', '-DF3DEX_GBI_2', '-I/source/upstream/af/lib/ultralib/include',
               '-I/source/overlays/keyboard_grid', '-I/out'))
    # Preserve the native encodings of the existing N64 control hints.
    data = bytearray(data); suffix = compiled['previous_resident_bytes']
    for _, label in LABELS:
        if data[suffix:].count(label+b'\0') != 1: raise ValueError('Changed native control hint')
        at = data.index(label+b'\0', suffix); data[at:at+len(label)] = encode_label(label)
    data = bytes(data); compiled['overlay_sha256'] = sha256(data)
    (out/'editor/image.bin').write_bytes(data)
    (out/'editor/image.json').write_text(json.dumps(compiled, indent=2)+'\n')
    growth = ((len(data)+63)&~63)-((suffix+63)&~63)
    if growth > POOL_EXTRA or len(data) > SPEC['new_reloc']-SPEC['new_vrom']:
        raise ValueError('Keyboard background exceeds its owned allocation')
    files = by_vrom(base); owner = bytearray(files[0x7749C0].extract(base)); code = bytearray(files[CODE_VROM].extract(base))
    if struct.unpack_from('>4I', owner, SPEC['owner_at']) != (SPEC['vrom'], SPEC['vrom']+suffix, RAM, RAM+suffix):
        raise ValueError('Changed preceding editor owner')
    if struct.unpack_from('>I', code, POOL_AT-CODE_RAM)[0] != POOL_BEFORE or (POOL_BEFORE & 0xFFFF)+POOL_EXTRA >= 0x8000:
        raise ValueError('Keyboard background pool word or signed immediate changed')
    struct.pack_into('>4I', owner, SPEC['owner_at'], SPEC['new_vrom'], SPEC['new_vrom']+len(data), RAM, RAM+len(data))
    struct.pack_into('>I', code, POOL_AT-CODE_RAM, POOL_BEFORE+POOL_EXTRA)
    changes = {SPEC['vrom']: data, SPEC['reloc']: relocation, 0x7749C0: bytes(owner), CODE_VROM: bytes(code)}
    moves = {SPEC['vrom']: SPEC['new_vrom'], SPEC['reloc']: SPEC['new_reloc']}
    image = reconstruct(native, base, changes, resized=(SPEC['vrom'], SPEC['reloc']), moves=moves)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image or before != source_hashes():
        raise ValueError('Keyboard background patch/source verification failed')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': before,
        'editor': compiled, 'artwork': profile, 'shared_growth_bytes': growth, 'extra_pool_bytes': POOL_EXTRA,
        'vrom_moves': {f'{v:08X}': f'{n:08X}' for v, n in moves.items()}, 'toolchain_image': IMAGE,
        'rom_bytes': len(image), 'required_ram_bytes': 0x800000, 'save_format_changed': False,
        'hardware_retest': 'pending', 'native_tests': 'pending', 'fixed_issues': ['V1-02 background']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1-letter-ui-fix-02')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-keyboard-background-fix-01'); args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (args.base/'animal-forest-title-preview.z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), args.output)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(data)
    print(json.dumps({k: report[k] for k in ('output_sha256', 'patch_sha256', 'shared_growth_bytes')}, indent=2))


if __name__ == '__main__': main()
