"""Install source-sized English Nookington lettering in native fixed-size slots."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from building_artwork import OBJECT, donor_texture_pointers, palette_equivalent
from map_artwork import Donor, compile_commands
from texture_preview import native_range, decode, png_rgba
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, untile, pack4, model_texture_shape

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = 'e5f2a22f50f89fdf7e0e9743368abf9a2f4d261e303dc0339f5cbbc4a0ad48f7'
NEW_OBJECT = 0x03D00000
STRUCTURE, STRUCTURE_RAM, DEPART, TABLE = 0x8CB690, 0x809E7ED0, 0x8D0D20, 0xDF4000
OLD_SIZE, NEW_SIZE, SLOT_SIZE = 0x25D0, 0x2C80, 0x2E00
SEASONS = (('summer', 0x659A0, 0x95480, 0x34, 0xEC),
           ('winter', 0x67F80, 0x98100, 0x1A4, 0x25C))
SOURCE_HASHES = {
    STRUCTURE: '47d03c6fd4526d45a8685747a90253fb0daa102f0a4831a59a9fe472fab62987',
    0x8CD350: 'c5cf7bb03c93a15c7ec5287062fe0f191583e587cfabddd9865abe761118263c',
    DEPART: '8568c07b55b5dbbbdc66145a5d71ca037f35962563382ad0562d1af953e62df3',
    0x8D1DD0: '55f4e5a8f54f2f67b517389ba6a2a86d7844e1da1c2edae6517b921a7b65ed7f',
    TABLE: '5de512903c80e182c1e1300668082a0c74088f56ef60a6a27a8d3d5fe6a5c445',
}
SLICE_HASHES = ('54a1009c177298814c7eb38b1999b72ae533f00a0709b9dd1146c765d9699f2e',
                '78129f2deeb585f48b8f316fa985543eaab47daaa2be61216844228d8ef63c5d')
# Explicit display-list, skeleton, and animation pointers; never scan/modify pixel words.
POINTERS = ((0x784, 0x1BD8), (0x7C4, 0x6D0), (0x844, 0xBD8), (0x884, 0x5F0),
    (0x91C, 0x13D8), (0x95C, 0x280), (0x9C4, 0x480), (0xA24, 0x1C58),
    (0xA54, 0x1C78), (0xAAC, 0x40), (0xB04, 0x240), (0xB7C, 0xBD8), (0xBC4, 0),
    (0x2484, 0x9F8), (0x249C, 0xB18), (0x24B4, 0x8B8), (0x24C0, 0x7E0),
    (0x24CC, 0x750), (0x24DC, 0x2478), (0x25B8, 0x24E0), (0x25BC, 0x2520),
    (0x25C0, 0x24E8), (0x25C4, 0x2500))
ACTOR_POINTERS = ((0xEB0, 0x24D8), (0x103C, 0x25B8), (0x1084, 0x750))
DONORS = (Donor(0x58B140, 0x58C4E8, 0x98), Donor(0x58D7C0, 0x58EAE8, 0x98))


def commands(out):
    return compile_commands(out, ROOT/'overlays/nookington/sign.c', (('summer', 176), ('winter', 176)))


def expected_commands(base):
    words = (0xE7000000, 0, 0xFD500000, base+0x25D0, 0xF5500000, 0x07054200,
        0xE6000000, 0, 0xF3000000, 0x072FF156, 0xE7000000, 0,
        0xF5400C00, 0x00F54200, 0xF2000000, 0x0017C07C,
        0xF5400C00, 0x01F54200, 0xF2000000, 0x0117C07C,
        0x060E1012, 0x00101412, 0xE7000000, 0,
        0xFD500000, base+0x1C78, 0xF5500000, 0x07054170,
        0xE6000000, 0, 0xF3000000, 0x073FF100, 0xE7000000, 0,
        0xF5401000, 0x00F54170, 0xF2000000, 0x001FC07C,
        0xF5401000, 0x01F54170, 0xF2000000, 0x011FC07C, 0xDF000000, 0)
    return struct.pack('>44I', *words)


def source_sign(native, rel, symbols):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected Nookington English source')
    pointers = donor_texture_pointers(rel, DONORS)
    samples = []
    for donor in DONORS:
        model = rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+donor.model_bytes]
        if model_texture_shape(model) != (128, 32, 2, 0):
            raise ValueError('Nookington source texture shape changed')
        pixels = untile(rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+2048], 128, 32, 4)
        samples.append(bytes(pixels[y*128+x] for y in range(32) for x in range(32, 128)))
    # The sign itself, including its filtered boundary, is identical in both seasons.
    if any(samples[0][y*96:y*96+81] != samples[1][y*96:y*96+81] for y in range(32)):
        raise ValueError('Seasonal donor sign pixels differ')
    for old in (0x659A0, 0x67F80):
        palette_equivalent(native_range(native, OBJECT+old+0x1C58, 32),
            rel[DATA_BASE+0x58C7A0:DATA_BASE+0x58C7C0], set(samples[1]))
    for vertices in (0x58BA40, 0x58E040):
        quad = list(struct.iter_unpack('>3hH2h4B', rel[DATA_BASE+vertices+78*16:DATA_BASE+vertices+82*16]))
        if [v[4:6] for v in quad] != [(1055, -1024), (1055, 0), (3552, 0), (3552, -1024)]:
            raise ValueError('Source sign sampling coordinates changed')
    return pack4(samples[1]), pointers


def patch_assets(native, base, rel, symbols, compiled):
    sign, donor_pointers = source_sign(native, rel, symbols)
    files = by_vrom(base)
    for vrom, digest in SOURCE_HASHES.items():
        if sha256(files[vrom].extract(base)) != digest:
            raise ValueError(f'Unexpected Nookington native owner {vrom:08X}')
    prior = files[OBJECT].extract(base)
    if len(prior) != 0x95480 or set(compiled) != {'summer', 'winter'}:
        raise ValueError('Changed building object size or command ownership')
    expanded = bytearray(prior)
    table, depart = bytearray(files[TABLE].extract(base)), bytearray(files[DEPART].extract(base))
    rows = []
    for season_index, ((name, old, new, start_at, end_at), digest) in enumerate(zip(SEASONS, SLICE_HASHES)):
        original = prior[old:old+OLD_SIZE]
        if sha256(original) != digest or len(expanded) != new:
            raise ValueError('Changed native Nookington slice or append alignment')
        expected = expected_commands(0x06000000+new)
        if compiled[name] != expected:
            raise ValueError('Compiled sign commands differ from fixed native specification')
        changed = bytearray(original)
        actual = {(i*4, v-0x06000000-old) for i, (v,) in enumerate(struct.iter_unpack('>I', original))
                  if 0x06000000+old <= v < 0x06000000+old+OLD_SIZE}
        if actual != set(POINTERS):
            raise ValueError('Nookington internal pointer inventory changed')
        for at, target in POINTERS:
            struct.pack_into('>I', changed, at, 0x06000000+new+target)
        if original[0xAC8:0xAD0] != bytes.fromhex('060E101200101412'):
            raise ValueError('Native sign triangles changed')
        struct.pack_into('>2I', changed, 0xAC8, 0xDE000000, 0x06000000+new+0x2BD0)
        old_uv = ((1024, 1024), (1024, 0), (3072, 1024), (3072, 0))
        for i, uv in enumerate(old_uv):
            at = 0xB0+i*16+8
            if struct.unpack_from('>2h', original, at) != uv:
                raise ValueError('Native sign UV inventory changed')
            struct.pack_into('>h', changed, at, 31 if i < 2 else 2528)
        changed.extend(sign)
        changed.extend(compiled[name])
        if len(changed) != NEW_SIZE or (len(changed)+15)&~15 > SLOT_SIZE:
            raise ValueError('English sign exceeds the native building slot')
        expanded.extend(changed)
        if u32(table, start_at) != 0x06000000+old-8 or u32(table, end_at) != 0x06000000+old+OLD_SIZE:
            raise ValueError('Native Nookington range table changed')
        struct.pack_into('>I', table, start_at, 0x06000000+new-8)
        struct.pack_into('>I', table, end_at, 0x06000000+new+NEW_SIZE)
        for at, target in ACTOR_POINTERS:
            position = at+season_index*4
            if u32(depart, position) != 0x06000000+old+target:
                raise ValueError('Native Nookington actor pointer changed')
            struct.pack_into('>I', depart, position, 0x06000000+new+target)
        rows.append({'season': name, 'source_object_offset': f'{old:06X}', 'object_offset': f'{new:06X}',
            'bytes': len(changed), 'slot_headroom_bytes': SLOT_SIZE-len(changed),
            'sha256': sha256(changed), 'rebased_internal_pointers': len(POINTERS)})
    structure = bytearray(files[STRUCTURE].extract(base))
    at = 0x809E8198-STRUCTURE_RAM
    if structure[at:at+8] != bytes.fromhex('3C0E00D625CEE000'):
        raise ValueError('Native building DMA source constant changed')
    structure[at:at+8] = bytes.fromhex('3C0E03D025CE0000')
    # Validate every current building's actual stream, including earlier English shops.
    old_table = files[TABLE].extract(base)
    checked = 0
    for starts, ends in ((8, 0xC0), (0x178, 0x230)):
        for kind in range(46):
            old_start, old_end = u32(old_table, starts+kind*4), u32(old_table, ends+kind*4)
            new_start, new_end = u32(table, starts+kind*4), u32(table, ends+kind*4)
            if kind == 11:
                size = (new_end-new_start-8+15)&~15
                if size != NEW_SIZE or size > SLOT_SIZE:
                    raise ValueError('New building range exceeds its slot')
            else:
                if (old_start, old_end) != (new_start, new_end):
                    raise ValueError('Unrelated building range changed')
                offset, size = old_start-0x06000000+8, (old_end-old_start-8+15)&~15
                if old_start == old_end == 0: continue
                if offset < 0 or offset+size > len(prior) or size > SLOT_SIZE:
                    raise ValueError('Unrelated building range is outside its native slot')
                if expanded[offset:offset+size] != prior[offset:offset+size]:
                    raise ValueError('English sign changes an unrelated streamed building')
            checked += 1
    changed = {STRUCTURE: bytes(structure), DEPART: bytes(depart), TABLE: bytes(table)}
    return changed, bytes(expanded), {'version': 1, 'source_rel_sha256': REL_SHA256,
        'source_symbols_sha256': SYMBOLS_SHA256, 'object_vrom': f'{NEW_OBJECT:08X}',
        'original_object_sha256': sha256(prior), 'object_sha256': sha256(expanded),
        'object_bytes': len(expanded), 'sign_sha256': sha256(sign), 'sign_dimensions': [96, 32],
        'donor_texture_pointers': {f'{k:08X}': f'{v:08X}' for k, v in donor_pointers.items()},
        'seasons': rows, 'building_ranges_checked': checked,
        'changed_files': {f'{v:08X}': sha256(data) for v, data in changed.items()},
        'command_source_sha256': sha256((ROOT/'overlays/nookington/sign.c').read_bytes()),
        'allocation_changed': False, 'geometry_changed': False, 'save_layout_changed': False,
        'status': 'Main English sign installed; other decorative marks and ordinary visual checks pending'}


def build(native, base, report, rel, symbols, compiled):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Nookington sign requires the complete English keyboard-grid baseline')
    changed, expanded, profile = patch_assets(native, base, rel, symbols, compiled)
    files = by_vrom(base)
    if any(v < NEW_OBJECT+len(expanded) and e.vend > NEW_OBJECT for v, e in files.items()):
        raise ValueError('Expanded building object overlaps an existing resource')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if any(v in moved or v in additions for v in changed):
        raise ValueError('Nookington owner identity changed')
    replacements.update(changed)
    additions[NEW_OBJECT] = expanded
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files)|{NEW_OBJECT} or len(image) != len(base):
        raise ValueError('English sign changes unrelated cartridge/resource sizes')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changed.get(vrom, entry.extract(base))
        if vrom == 0x19D40: actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index or installed[vrom].size != entry.size:
            raise ValueError(f'English sign loses previous resource {vrom:08X}')
    if installed[NEW_OBJECT].extract(image) != expanded:
        raise ValueError('English sign expanded object was not installed')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('English sign UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups), nookington_sign=profile,
        replacement_files=[f'{v:08X}' for v in sorted(replacements)],
        added_files=[f'{v:08X}' for v in sorted(additions)],
        release_status='English Nookington main sign/grid candidate; ordinary visual/hardware checks pending')
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/nookington-sign-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = ROOT/'build/keyboard-grid-01'
    native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    image, ups, report = build(native, (baseline/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((baseline/'build.json').read_text()), rel, symbols, commands(args.output/'gbi'))
    sign, _ = source_sign(native, rel, symbols)
    outputs = {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode(),
        'sign.png': png_rgba(96, 32, decode(sign, 96, 32, 'ci4', native_range(native, 0xDC55F8, 32)), 4)}
    for name, value in outputs.items():
        with (args.output/name).open('xb') as target: target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
        'patch_sha256': report['patch_sha256'], 'seasons': report['nookington_sign']['seasons']}))


if __name__ == '__main__':
    main()
