"""Install the supplied English SOLD OUT sign and encode native grid hints."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, u32
from building_artwork import donor_texture_pointers, palette_equivalent
from map_artwork import Donor
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, untile, pack4
from keyboard_grid_labels import install as encode_grid_labels, CORRECTED_SHA
from keyboard_grid_overlay import verify_owned_parts

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '28c551708dbbc1d78333abc7ebf81d5001663859775ca9f85427ced8208b0020'
OBJECT, GRID = 0x140C000, 0x3940000
OBJECT_SHA = 'e0e87769178c5593175d0d69a395190693dc1cd6481ae9fc1a327de82dd84f06'
DONOR = Donor(0x399280, 0x399540, 0x48)


def sign_asset(native, rel, symbols):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English SOLD OUT source')
    donor_texture_pointers(rel, (DONOR,))
    data = by_vrom(native)[OBJECT].extract(native)
    if sha256(data) != OBJECT_SHA:
        raise ValueError('Unexpected native shared item object')
    if model_texture_shape(rel[DATA_BASE+DONOR.gc_model:DATA_BASE+DONOR.gc_model+DONOR.model_bytes]) != (32, 32, 2, 0):
        raise ValueError('SOLD OUT donor texture shape changed')
    pixels = untile(rel[DATA_BASE+DONOR.gc:DATA_BASE+DONOR.gc+512], 32, 32, 4)
    palette_equivalent(data[0x36B0:0x36D0], rel[DATA_BASE+0x399260:DATA_BASE+0x399280], set(pixels))
    for i in range(12):
        old = data[0x3520+i*16:0x3530+i*16]
        gc = rel[DATA_BASE+0x399480+i*16:DATA_BASE+0x399490+i*16]
        if old[:6]+old[8:] != gc[:6]+gc[8:]:
            raise ValueError('SOLD OUT donor model coordinates or lighting differ')
    expected_load = struct.pack('>14I', 0xFD500000, 0x060036D0,
        0xF5500000, 0x070D4350, 0xE6000000, 0, 0xF3000000, 0x070FF400,
        0xE7000000, 0, 0xF5400400, 0x00FD4350, 0xF2000000, 0x0007C07C)
    if (data[0x3638:0x3670] != expected_load
            or data[0x3688:0x3690] != bytes.fromhex('0100C01806003520')
            or data[0x3608:0x3610] != bytes.fromhex('FD100000060036B0')):
        raise ValueError('Native SOLD OUT texture, palette, or vertex load changed')
    converted = pack4(pixels)
    changed = data[:0x36D0]+converted+data[0x38D0:]
    if changed == data:
        raise ValueError('English sign does not replace Japanese pixels')
    return changed, {'version': 1, 'label': 'SOLD OUT', 'source_rel_sha256': REL_SHA256,
        'source_symbols_sha256': SYMBOLS_SHA256, 'texture_vrom': '0140F6D0',
        'source_texture_offset': '00399280', 'texture_sha256': sha256(converted),
        'object_vrom': f'{OBJECT:08X}', 'object_sha256': sha256(changed),
        'changed_texture_bytes': sum(a != b for a, b in zip(data, changed)),
        'matched_vertex_uses': 12, 'allocation_changed': False, 'model_changed': False,
        'status': 'English sign installed; ordinary shop/hardware appearance pending'}


def build(native, base, report, rel, symbols):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Shop sign requires the complete Nookington/grid baseline')
    sign, profile = sign_asset(native, rel, symbols)
    files = by_vrom(base)
    if sha256(files[OBJECT].extract(base)) != OBJECT_SHA:
        raise ValueError('Shared item object has unrelated installed changes')
    verify_owned_parts(base, native, report['keyboard_grid'], report['apology_input'])
    grid = encode_grid_labels(files[GRID].extract(base))
    changes = {OBJECT: sign, GRID: grid}
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    replacements[OBJECT] = sign
    for original in replacements:
        target = moved.get(original, original)
        if target in changes: replacements[original] = changes[target]
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Shop sign changes cartridge/resource sizes')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changes.get(vrom, entry.extract(base))
        if vrom == 0x19D40: actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index or installed[vrom].size != entry.size:
            raise ValueError(f'Shop sign loses earlier resource {vrom:08X}')
    verify_owned_parts(image, native, report['keyboard_grid'], report['apology_input'])
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Shop sign UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(patch), shop_signs=profile,
        keyboard_grid_labels={'version': 1, 'vrom': f'{GRID:08X}', 'sha256': CORRECTED_SHA,
            'changed_bytes': 3, 'native_plus': '5C', 'movement_separator': 'space',
            'code_changed': False, 'allocation_changed': False},
        replacement_files=[f'{v:08X}' for v in sorted(replacements)],
        release_status='English shop signs and corrected keyboard hints; further native acceptance pending')
    return image, patch, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/shop-signs-01')
    args = parser.parse_args()
    baseline = ROOT/'build/nookington-sign-02'
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': patch,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
        'patch_sha256': report['patch_sha256']}))


if __name__ == '__main__':
    main()
