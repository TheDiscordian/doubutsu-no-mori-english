"""Install full GameCube Insects/Fish headings inside the native collection pages."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups
from building_artwork import donor_texture_pointers
from inventory_artwork import VROM, patch_assets as inventory_assets, commands as inventory_commands
from map_artwork import Donor, compile_commands, port_quad
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, pack4, untile

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '54a6d643d27cd36345e2298407f47f5bb51ddf2c6f947558391da968cbf717be'
DONORS = (Donor(0x4362C0, 0x438590), Donor(0x441080, 0x443AF0))
ROWS = (('Insects', 80, 0xA31D28, 2048, 0xA31508, 0xA30980, 0x437C80),
        ('Fish', 64, 0xA3E438, 2560, 0xA3D818, 0xA3CC40, 0x4431C0))


def commands(out):
    result = compile_commands(out, ROOT/'overlays/inventory/collection.c', (('insects', 56), ('fish', 56)))
    result['inventory'] = inventory_commands(out/'inventory')
    return result


def patch_assets(native, prior, rel, symbols, compiled):
    verified_rom(native)
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Unexpected English collection donor')
    expected, _ = inventory_assets(native, rel, symbols, compiled['inventory'])
    if prior != expected:
        raise ValueError('Collection artwork requires the complete ordinary-inventory asset')
    pointers = donor_texture_pointers(rel, DONORS)
    result, changes = bytearray(prior), []
    def install(address, value):
        start = address-VROM
        if not 0 <= start <= len(result)-len(value):
            raise ValueError('Collection artwork exceeds native asset bounds')
        result[start:start+len(value)] = value
        changes.append({'vrom': f'{address:08X}', 'bytes': len(value),
                        'previous_sha256': sha256(prior[start:start+len(value)]), 'output_sha256': sha256(value)})
    for donor, (label, width, texture, capacity, load, vertices, gc_vertices) in zip(DONORS, ROWS):
        model = rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+donor.model_bytes]
        if model_texture_shape(model) != (width, 16, 4, 0):
            raise ValueError('English collection heading shape changed')
        value = pack4(untile(rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*8], width, 16, 4))
        install(texture, value+bytes(capacity-len(value)))
        load_bytes = compiled[label.lower()]
        # Independent fixed native command specification, including the 80-wide row stride.
        mask = 0 if width == 80 else 6
        line = width//16
        expected = struct.pack('>14I', 0xFD900000, 0x0C000000+texture-VROM,
            0xF5900000, 0x07090200+(mask<<4), 0xE6000000, 0,
            0xF3000000, 0x07000000+((width*16//4-1)<<12)+((2048+line-1)//line),
            0xE7000000, 0, 0xF5800000+(line<<9), 0x00F90200+(mask<<4),
            0xF2000000, ((width-1)*4<<12)+60)
        if load_bytes != expected:
            raise ValueError('Compiled collection texture load differs from native specification')
        install(load, load_bytes)
        gc = rel[DATA_BASE+gc_vertices:DATA_BASE+gc_vertices+64]
        quad = bytearray(port_quad(prior[vertices-VROM:vertices-VROM+64], gc, scale=1))
        for at in range(0, 64, 16):
            y = struct.unpack_from('>h', quad, at+2)[0]
            struct.pack_into('>h', quad, at+2, y-10)
        install(vertices, bytes(quad))
        if model[:4] != bytes.fromhex('FA0000FF'):
            raise ValueError('English collection primitive colour changed')
        install(load-8, model[:8])
    data = bytes(result)
    return data, {'version': 1, 'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
        'asset_sha256': sha256(data), 'previous_asset_sha256': sha256(prior),
        'labels': [r[0] for r in ROWS], 'donor_texture_pointers': pointers, 'changes': changes,
        'donor_y_offset': -10, 'allocation_changed': False, 'capture_state_changed': False,
        'status': 'English heading assets installed; ordinary collection display/navigation pending'}


def build(native, base, report, rel, symbols, compiled):
    if sha256(base) != BASE_SHA or report.get('output_sha256') != BASE_SHA:
        raise ValueError('Collection artwork requires the complete English clock baseline')
    files = by_vrom(base)
    data, profile = patch_assets(native, files[VROM].extract(base), rel, symbols, compiled)
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if VROM in moved or VROM in additions:
        raise ValueError('Collection asset ownership changed')
    replacements[VROM] = data
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('Collection artwork changes cartridge size or resource identities')
    for vrom, entry in files.items():
        actual, expected = installed[vrom].extract(image), data if vrom == VROM else entry.extract(base)
        if vrom == 0x19D40: actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'Collection artwork loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('Collection artwork patch reconstruction failed')
    result = copy.deepcopy(report)
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups), collection_artwork=profile,
        release_status='English collection/clock/map/inventory/shop candidate; ordinary screen/hardware checks pending')
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/collection-artwork-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    baseline = ROOT/'build/time-setting-01'
    image, ups, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), commands(args.output/'gbi'))
    for name, value in {'animal-forest-halfwidth.z64': image, 'animal-forest-halfwidth.ups': ups,
        'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(value)
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
                      'patch_sha256': report['patch_sha256'], 'labels': report['collection_artwork']['labels']}))


if __name__ == '__main__':
    main()
