"""Apply English inventory headings with their donor layout and native asset bounds."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups
from building_artwork import donor_texture_pointers
from map_artwork import Donor, compile_commands, port_quad
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, pack4, untile

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '29576ea8bc82a55193a263b913a15ffe81554746a2cec5cdcff3bf84a26b6cdc'
VROM, VERTICES = 0xA30000, 0x43CFE0
NATIVE_SHA = 'd39cedf24822c4b3ad6b28944eda1dc7a90c478a1bf18529b2f70fb4cc1b73ed'
DONORS = (Donor(0x43B960, 0x43E398), Donor(0x43BB60, 0x43E3C8), Donor(0x43BD60, 0x43E3F8))
TARGETS = ((0xA3AD00, 0xA360B0, 56), (0xA3AF00, 0xA36170, 60), (0xA3B100, 0xA361B0, 64))


def commands(out):
    return compile_commands(out, ROOT/'overlays/inventory/artwork.c', (('items', 56),))['items']


def patch_assets(native, rel, symbols, compiled):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English inventory source')
    pointers = donor_texture_pointers(rel, DONORS)
    source = by_vrom(native)[VROM].extract(native)
    if sha256(source) != NATIVE_SHA:
        raise ValueError('Unexpected native inventory asset file')
    expected = struct.pack('>14I', 0xFD900000, 0x0C00AD00, 0xF5900000, 0x07090260,
        0xE6000000, 0, 0xF3000000, 0x070FF200, 0xE7000000, 0,
        0xF5800800, 0x00F90260, 0xF2000000, 0x000FC03C)
    if compiled != expected:
        raise ValueError('Compiled inventory load differs from fixed native command specification')
    result, changes = bytearray(source), []
    def install(address, value):
        start = address-VROM
        if not 0 <= start <= len(result)-len(value):
            raise ValueError('Inventory artwork exceeds original allocation')
        result[start:start+len(value)] = value
        changes.append({'vrom': f'{address:08X}', 'bytes': len(value),
            'native_sha256': sha256(source[start:start+len(value)]), 'output_sha256': sha256(value)})
    for donor, (texture, vertices, index) in zip(DONORS, TARGETS):
        model = rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+donor.model_bytes]
        if model_texture_shape(model) != (64, 16, 4, 0):
            raise ValueError('English inventory heading has unexpected dimensions/format')
        install(texture, pack4(untile(rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+512], 64, 16, 4)))
        gc = rel[DATA_BASE+VERTICES+index*16:DATA_BASE+VERTICES+(index+4)*16]
        install(vertices, port_quad(source[vertices-VROM:vertices-VROM+64], gc, scale=1))
    install(0xA371A8, compiled)
    install(0xA3AA00, bytes(256))
    # The native normal-inventory frame appends this village suffix at
    # 8087FCD0..8087FCDC. The English donor draws only the actual town name.
    install(0xA300B8, bytes(256))
    colour = rel[DATA_BASE+DONORS[0].gc_model:DATA_BASE+DONORS[0].gc_model+8]
    if colour != bytes.fromhex('FA0000FF7878E1FF'):
        raise ValueError('English Items heading colour changed')
    install(0xA371A0, colour)
    return bytes(result), {'version': 1, 'source_rel_sha256': REL_SHA256, 'symbols_sha256': SYMBOLS_SHA256,
        'native_asset_sha256': NATIVE_SHA, 'asset_vrom': f'{VROM:08X}', 'asset_bytes': len(result),
        'asset_sha256': sha256(result), 'changes': changes,
        'donor_texture_pointers': {f'{k:08X}': f'{v:08X}' for k, v in pointers.items()},
        'command_source_sha256': sha256((ROOT/'overlays/inventory/artwork.c').read_bytes()),
        'command_sha256': sha256(compiled), 'labels': ['Items', 'Letters', 'Bells'],
        'cpu_code_changed': False, 'selection_logic_changed': False, 'save_layout_changed': False,
        'removed_duplicate_units': ['Japanese Bells unit', 'Japanese town suffix'],
        'status': 'English inventory headings installed; ordinary visual/navigation checks pending'}


def build(native, base, report, rel, symbols, compiled):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Inventory artwork requires complete map/shop/hardware-fix baseline')
    changed, profile = patch_assets(native, rel, symbols, compiled)
    files = by_vrom(base)
    if sha256(files[VROM].extract(base)) != NATIVE_SHA:
        raise ValueError('Installed inventory assets already have unrelated changes')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if VROM in moved or VROM in additions:
        raise ValueError('Inventory asset ownership changed')
    replacements[VROM] = changed
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Inventory artwork alters cartridge size or DMA identities')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), changed if vrom == VROM else entry.extract(base)
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'Inventory artwork loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Inventory artwork UPS reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)], inventory_artwork=profile,
        release_status='English inventory/map/shop artwork candidate; ordinary visual/hardware checks pending')
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/inventory-artwork-01')
    parser.add_argument('--commands', type=Path, default=ROOT/'build/inventory-artwork-commands')
    args = parser.parse_args()
    compiled = commands(args.commands)
    baseline = ROOT/'build/map-artwork-01'
    image, ups, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), compiled)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
                      'patch_sha256': report['patch_sha256'], 'labels': report['inventory_artwork']['labels']}))


if __name__ == '__main__':
    main()
