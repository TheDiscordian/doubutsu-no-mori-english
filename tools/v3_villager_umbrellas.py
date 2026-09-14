"""Verify installed donor umbrella defaults and complete native asset correspondence."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, verified_rom
from apply_translation import write_new
from gc_names import rel_sections, symbol_data
from stall_model_source import packed
from title_assets import pack4, untile
from v3_furniture_art import verify_sources
from v3_npc_draw import DRAW_OFFSET, STRIDE
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags

# Tool number, native asset, donor asset span, native palette, texture layouts,
# native canopy/handle display lists. GC local names are duplicated in shop art.
ASSETS = (
    (3, 0x110A000, 0x5CC920, 0x5CD1C0, 0x580,
     (('kasa1', 0x5A0, 16, 32), ('kasa2', 0x6A0, 16, 32), ('tuka', 0x7A0, 32, 32)),
     ((0x380, 0x4C0), (0x4C0, 0x580)),
     '598fb02e50fb593443cebe7848d13c27ac3b77e08258255060432fc8af0adc03'),
    (13, 0x1114000, 0x5D2820, 0x5D30A8, 0x508,
     (('kasa', 0x528, 32, 32), ('tuka', 0x728, 32, 32)),
     ((0x380, 0x448), (0x448, 0x508)),
     'da493638eeca27ee2874066aa2e00f95f7f90f9901a016c79c62219d1e13de95'),
)


def canonical(triangle):
    t = tuple(triangle)
    return min(t, t[1:]+t[:1], t[2:]+t[:2])


def triangles(raw, *, pointers=None, start=0, vertex=0, materials=None):
    """Compare material-bound geometry while retaining triangle winding."""
    result, at, first, loaded, material = Counter(), 0, 0, 0, None
    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op = a >> 24
        if op == 0xFD:
            if pointers is not None:
                material = materials[pointers[start+at+4]]
            elif a >> 16 & 255 == 0x50:
                material = b & 0xFFFFFF
        elif op == 0x01:
            target = pointers[start+at+4] if pointers is not None else b & 0xFFFFFF
            first, loaded = (target-vertex)//16, a >> 12 & 255
            if target < vertex or (target-vertex) % 16 or not 1 <= loaded <= 32 or first+loaded > 56:
                raise ValueError('Umbrella vertices escape the verified array')
        elif op in (0x05, 0x06, 0x0A):
            if not loaded or material is None:
                raise ValueError('Umbrella triangles lack vertices or texture')
            if op == 0x0A:
                count = (a >> 17 & 127)+1
                size = (1+(max(0, count-3)+3)//4)*8
                cells = packed(raw[at:at+size], loaded)
                at += size-8
            else:
                cells = [tuple((word >> shift & 255)//2 for shift in (16, 8, 0))
                         for word in ((a, b) if op == 0x06 else (a,))]
                if any(v >= loaded for cell in cells for v in cell):
                    raise ValueError('Native umbrella triangle exceeds loaded vertices')
            for cell in cells:
                result[material, canonical(first+v for v in cell)] += 1
        elif op == 0xDF:
            if a != 0xDF000000 or b or at+8 != len(raw):
                raise ValueError('Changed umbrella model termination')
        elif op not in (0xD7, 0xE2, 0xFC, 0xF0, 0xD2, 0xFA, 0xD9, 0xE7, 0xE8, 0xF5, 0xE6, 0xF3, 0xF2):
            raise ValueError('Unsupported umbrella model command')
        at += 8
    if not result or raw[-8:] != bytes.fromhex('df00000000000000'):
        raise ValueError('Incomplete umbrella model')
    return result


def verify_art(native, rel, symbols):
    verify_sources(rel, symbols)
    files, source = by_vrom(native), symbols.decode()
    section = rel_sections(rel)[5][0]
    rows = []
    for number, vrom, begin, end, palette_offset, textures, models, digest in ASSETS:
        asset = files[vrom].extract(native)
        if sha256(asset) != digest:
            raise ValueError('Changed native umbrella asset')

        def span(name):
            found = [(int(a, 16), int(n, 16)) for a, n in re.findall(
                '^'+re.escape(name)+r' = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', source, re.M)]
            found = [(a, n) for a, n in found if begin <= a < a+n <= end]
            if len(found) != 1:
                raise ValueError('Missing or ambiguous held-umbrella asset symbol')
            at, size = found[0]
            return at, rel[section+at:section+at+size]

        stem = f'tol_umb_{number+1:02}'
        _, palette = span(stem+'_pal')
        if native_palette(palette) != asset[palette_offset:palette_offset+32]:
            raise ValueError('Donor umbrella palette differs from native')
        materials, pixels = {}, 0
        for key, offset, width, height in textures:
            at, raw = span(stem+'_'+key+'_tex_txt')
            converted = pack4(untile(raw, width, height, 4))
            if converted != asset[offset:offset+len(converted)]:
                raise ValueError('Donor umbrella texture differs from native')
            materials[at] = offset
            pixels += width*height
        vertex, vertices = span(stem+'_v')
        normalised, flags = normalise_vertex_flags(vertices)
        if len(vertices) != 56*16 or normalised != asset[:len(vertices)]:
            raise ValueError('Donor umbrella geometry, UVs, or colours differ from native')
        counts = []
        for kind, (offset, stop) in zip(('kasa', 'e'), models):
            at, model = span(f'{kind}_umb{number+1:02}_model')
            donor = triangles(model, pointers=data_pointers(rel, at, len(model)), start=at,
                              vertex=vertex, materials=materials)
            original = triangles(asset[offset:stop])
            if donor != original:
                raise ValueError('Donor umbrella triangles or material assignments differ')
            counts.append(sum(donor.values()))
        rows.append({'tool_number': number, 'object_vrom': f'{vrom:08X}',
                     'native_asset_sha256': digest, 'donor_asset_sha256': sha256(rel[section+begin:section+end]),
                     'compared_pixels': pixels, 'compared_vertices': 56, 'matrix_flags_removed': flags,
                     'canopy_handle_triangles': counts})
    return rows


def verify(native, rom, rel, symbols, report):
    verified_rom(native)
    if sha256(rom) != report['output_sha256']:
        raise ValueError('Umbrella review requires the report\'s exact cartridge')
    draw_report, text_report = report['npc_draw'], report['villager_text']
    installed = by_vrom(rom)
    blob = installed[0x3F00000].extract(rom)[:report['resident_blob_bytes']]
    art = verify_art(native, rel, symbols)
    files = by_vrom(native)
    # Both native constructors copy draw+5D into the actor's existing umbrella
    # field; unlike GC they do not read a saved Animal umbrella byte.
    consumers = []
    for vrom, base, at, words in ((0x8681F0, 0x809735B0, 0x8097F588, '93a800b5a208085f'),
                                 (0x8798C0, 0x80995BF0, 0x8099F9CC, '93a800ada208085f')):
        code = installed[vrom].extract(rom)
        if code[at-base:at-base+8].hex() != words:
            raise ValueError('Changed native draw-to-umbrella constructor field')
        consumers.append({'owner': f'{vrom:08X}', 'entry': f'{at:08X}', 'words': words})
    defaults = symbol_data(rel, symbols.decode(), 'npc_def_list')
    checked = []
    for donor, actor, wanted in ((232, 0xE0EA, 3), (235, 0xE0ED, 13)):
        row = next(r for r in draw_report['imports'] if r['actor_id'] == f'{actor:04X}')
        text = next(r for r in text_report['imports'] if r['actor_id'] == row['actor_id'])
        at = DRAW_OFFSET+(actor-0xE0DA)*STRIDE+4
        if (defaults[donor*6+4] != wanted or text['donor_umbrella'] != wanted
                or sha256(blob[at:at+100]) != row['record_sha256'] or blob[at+0x5D] != wanted):
            raise ValueError('Changed imported umbrella default or original draw record')
        checked.append({'actor_id': row['actor_id'], 'offset': at+0x5D, 'installed_umbrella': wanted})
    for _, vrom, *_ in ASSETS:
        if installed[vrom].extract(rom) != files[vrom].extract(native):
            raise ValueError('Installed umbrella asset differs from verified native asset')
    return {'artwork': art, 'consumers': consumers, 'verified_defaults': checked,
            'rom_sha256': sha256(rom), 'rom_changes_needed': False,
            'saved_layout_changed': False, 'ordinary_rain_tested': False}


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify((root/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), args.rom.read_bytes(),
                    (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
                    json.loads((args.rom.parent/'build.json').read_text()))
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output/'report.json', (json.dumps(result, indent=2)+'\n').encode())
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
