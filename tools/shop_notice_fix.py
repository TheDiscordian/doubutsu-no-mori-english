"""Match English GC's Nook 'n' Go wall by omitting its native hiring notice."""
import argparse
import json
from pathlib import Path
import struct

from aflib import apply_ups, by_vrom, make_ups, sha256, verified_rom
from apply_translation import write_new
from artwork_matches import data_pointers
from building_artwork import palette_equivalent
from map_artwork import compile_commands
from stall_model_source import packed
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, pack4, untile
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37'
OWNER = 0x013B6000
OWNER_SHA = '35f448bc7cf009995ea91ea6b760c2ed9e8de580a6ff68c7543cce0614342a1f'
TRIANGLES = 0x1F10
NOOP = bytes.fromhex('E000000000000000')
GC_PARTS = (
    ('rom_shop2w_v', 0x94DBA0, 0x1340,
     'eda20efd29fa577c9d14eb5bda407ab7fae93eeaef77ce6cd84acaa6677505c7'),
    ('rom_shop2w_modelT', 0x94EEE0, 0x68,
     '39f67662704880c157321361430aba33acc5c88de2d13192edd8b7d5a437e4e5'),
    ('rom_shop2w_model', 0x94EF48, 0x458,
     '5ba34891d3042ff0fb42ef96d68f6caad073d706958d7642e8479608161136de'),
)


def in_triangle(point, vertices):
    """Inclusive two-dimensional point test, independent of winding."""
    a, b, c = vertices
    if (b[0]-a[0])*(c[1]-a[1]) == (b[1]-a[1])*(c[0]-a[0]):
        return False
    crosses = [(b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0])
               for a, b in zip(vertices, vertices[1:]+vertices[:1])]
    return min(crosses) >= 0 or max(crosses) <= 0


def omission_source(original, rel, symbols):
    if (sha256(original) != OWNER_SHA or sha256(rel) != REL_SHA256
            or sha256(symbols) != SYMBOLS_SHA256):
        raise ValueError('Changed native room or supplied English shop source')
    for name, at, size, digest in GC_PARTS:
        if (symbols.decode().count(f'{name} = .data:0x{at:08X}; // type:object size:0x{size:X} ') != 1
                or sha256(rel[DATA_BASE+at:DATA_BASE+at+size]) != digest):
            raise ValueError('Changed complete English shop wall model or vertices')
    # One material owns exactly the four notice vertices and two triangles.
    required = {0x1EA0: 'FD10000006002878', 0x1ED0: 'FD50000006002EF8',
                0x1F00: 'F2000000000BC07C', 0x1F08: '0100400806001A80',
                TRIANGLES: '0600020400000406', 0x1F18: 'E700000000000000',
                0x20A0: 'FD10000006002898', 0x20D0: 'FD50000006003C78',
                0x2108: '01019032060009C0'}
    if any(original[at:at+8] != bytes.fromhex(value) for at, value in required.items()):
        raise ValueError('Changed notice or underlying wall reader')
    if (original.count(bytes.fromhex('FD50000006002EF8')) != 1
            or original.count(bytes.fromhex('0100400806001A80')) != 1):
        raise ValueError('Notice has another material or vertex consumer')
    pointers = data_pointers(rel)
    if {at: pointers.get(at) for at in (0x94F15C, 0x94F164, 0x94F174)} != {
            0x94F15C: 0x94C2A0, 0x94F164: 0x94D3A0, 0x94F174: 0x94DE20}:
        raise ValueError('Changed active English wall palette, image, or vertices')
    samples = untile(rel[DATA_BASE+0x94D3A0:DATA_BASE+0x94D7A0], 16, 128, 4)
    if pack4(samples) != original[0x3C78:0x4078]:
        raise ValueError('Native wall does not retain the English donor texture')
    palette_equivalent(original[0x2898:0x28B8],
                       rel[DATA_BASE+0x94C2A0:DATA_BASE+0x94C2C0], set(samples))
    native_wall = list(struct.iter_unpack('>3hH2h4B', original[0x9C0:0xB50]))
    wall = list(struct.iter_unpack('>3hH2h4B', rel[DATA_BASE+0x94DE20:DATA_BASE+0x94DFB0]))
    for n, g in zip(native_wall, wall):
        if (n[3] != 0 or g[3] != 1 or n[4:] != g[4:]
                or any(abs(5*y-4*x) > 80 for x, y in zip(n[:3], g[:3]))):
            raise ValueError('Native and English surrounding wall placements differ')
    # The English room draws the same wall behind the sign. Other trim at the
    # scaled Z=672 lies entirely left of this notice's X range, 4728..5512.
    vertices = list(struct.iter_unpack('>3hH2h4B', rel[DATA_BASE+0x94DBA0:DATA_BASE+0x94EEE0]))
    trim = [v for v in vertices if v[2] == 672]
    if not trim or max(v[0] for v in trim) >= 4728:
        raise ValueError('English wall model unexpectedly covers the notice plane')
    first = struct.unpack_from('>I', rel, DATA_BASE+0x94F178)[0]
    count = (first >> 17 & 127)+1
    size = (1+(max(0, count-3)+3)//4)*8
    faces = packed(rel[DATA_BASE+0x94F178:DATA_BASE+0x94F178+size], len(wall))
    background = [[wall[i][:2] for i in face] for face in faces if all(wall[i][2] == 640 for i in face)]
    notice = list(struct.iter_unpack('>3hH2h4B', original[0x1A80:0x1AC0]))
    for v in notice:
        if v[2] != 840 or not any(in_triangle((v[0]*4//5, v[1]*4//5), t) for t in background):
            raise ValueError('English background does not cover the notice placement')
    return {'native_texture_vrom': '013B8EF8', 'native_texture_sha256': sha256(original[0x2EF8:0x31F8]),
            'native_notice_vertices_sha256': sha256(original[0x1A80:0x1AC0]),
            'native_triangle_vrom': f'{OWNER+TRIANGLES:08X}',
            'omitted_triangles': [[0, 1, 2], [0, 2, 3]],
            'english_background_texture': '0094D3A0', 'english_wall_triangles': count,
            'source_model_sha256': GC_PARTS[2][3],
            'intent': 'English GC omits the hiring notice; retain the matching wall behind it'}


def patch_room(original, rel, symbols, compiled):
    if compiled != NOOP:
        raise ValueError('Expected one independently compiled native no-op')
    evidence = omission_source(original, rel, symbols)
    changed = original[:TRIANGLES]+compiled+original[TRIANGLES+8:]
    return changed, evidence


def build(native, base, rel, symbols, compiled):
    native = verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Shop notice correction requires the checked V1RC1 cartridge')
    old = by_vrom(native)[OWNER].extract(native)
    if by_vrom(base)[OWNER].extract(base) != old:
        raise ValueError('Shop room already differs from the reviewed original')
    changed, evidence = patch_room(old, rel, symbols, compiled)
    image = reconstruct(native, base, {OWNER: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Shop notice patch reconstruction failed')
    return image, patch, {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'toolchain_image': IMAGE,
        'sources': {name: sha256((ROOT/name).read_bytes()) for name in
                    ('tools/shop_notice_fix.py', 'overlays/fishing/artwork.c')},
        'room_vrom': f'{OWNER:08X}', 'room_sha256': sha256(changed), 'omission': evidence,
        'changed_command_bytes': 8, 'rom_bytes': len(image), 'required_ram_bytes': 0x800000,
        'cpu_code_changed': False, 'allocation_changed': False, 'save_format_changed': False,
        'native_wall_geometry_retained': True, 'hardware_retest': 'pending',
        'status': 'Post-V1RC1 artwork correction; existing V1RC1 artifact remains unchanged'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-rom', type=Path, default=ROOT/'build/v1rc1/Animal Forest English V1RC1.z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1-shop-notice-fix-01')
    args = p.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    compiled = compile_commands(args.output/'commands', ROOT/'overlays/fishing/artwork.c', (('remove', 8),))['remove']
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        args.base_rom.read_bytes(), (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), compiled)
    for name, data in {'animal-forest-title-preview.z64': image, 'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(args.output/name, data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
