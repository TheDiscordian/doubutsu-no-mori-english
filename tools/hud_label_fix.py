"""Install bound English camera/cash artwork and put AM/PM after the idle time."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, verified_rom, sha256, make_ups, apply_ups
from artwork_matches import converted, data_pointers, objects
from building_artwork import donor_texture_pointers
from map_artwork import Donor, compile_commands, port_quad
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '7c43f742009e391cae42bdf410f239f8a9c3aaf58003fd4f27371561109313ad'
VROM = 0xA22000
BANK_SHA = '8c85c03e1f714d961fb60c8277b7f9788fb7b8974668bd26891e789a4f1f0e55'
SOURCE = ROOT/'overlays/hud_labels/artwork.c'
DONORS = (Donor(0x87EE40, 0x880490, 0x48), Donor(0x8966A0, 0x8972D0))
CASH_LOAD = struct.pack('>14I', 0xFD900000, 0x0400B4D0, 0xF5900000, 0x07090260,
    0xE6000000, 0, 0xF3000000, 0x070FF200, 0xE7000000, 0,
    0xF5800800, 0x00F90260, 0xF2000000, 0x000FC03C)
# The six native display lists bind these quads to AM/PM, hour, colon, minute.
CLOCK = ((0x29E0, 36, (84, 97)), (0x2A20, -15, (99, 105)),
         (0x2A60, -15, (105, 111)), (0x2AA0, -15, (113, 119)),
         (0x2AE0, -15, (120, 126)), (0x2B20, -15, (127, 133)))
CLOCK_MODELS = (0x2B60, 0x2BD0, 0x2C40, 0x2CB0, 0x2D28, 0x2D98)


def patch_bank(bank, rel, symbols, commands):
    if sha256(bank) != BANK_SHA:
        raise ValueError('Changed native HUD bank')
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied English HUD sources')
    if commands != {'cash': CASH_LOAD}:
        raise ValueError('Unexpected compiled cash texture commands')
    named = {at: (name, size) for at, size, name in objects(symbols)}
    for donor, name, size, shape in zip(DONORS,
            ('cam_win_camera_tex', 'mny_win_money_tex'), (1024, 512),
            ((64, 16, 3, 1), (64, 16, 4, 0))):
        if named.get(donor.gc) != (name, size):
            raise ValueError('Changed English HUD symbol extent')
        if model_texture_shape(rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+donor.model_bytes]) != shape:
            raise ValueError('Changed English HUD tiled texture consumer')
    donor_texture_pointers(rel, DONORS)
    pointers = data_pointers(rel)
    if pointers.get(0x8972EC) != 0x8971E0:
        raise ValueError('Cash donor no longer consumes its bound quad')
    # Native load commands, vertex selection, and texture shapes are also pinned
    # by the bank digest; retain camera geometry and original N64 control icons.
    if struct.unpack_from('>2I', bank, 0x4A0) != (0xFD700000, 0x040008F8):
        raise ValueError('Changed camera artwork consumer')
    if struct.unpack_from('>2I', bank, 0xB4B8) != (0x01004008, 0x0400B320):
        raise ValueError('Changed cash artwork consumer')
    changed = bytearray(bank); changes = []

    def put(at, data, reason):
        if not 0 <= at <= len(bank)-len(data):
            raise ValueError('HUD replacement exceeds original allocation')
        if any(at < r['offset']+r['bytes'] and r['offset'] < at+len(data) for r in changes):
            raise ValueError('Overlapping HUD replacements')
        changed[at:at+len(data)] = data
        changes.append({'offset': at, 'bytes': len(data), 'reason': reason,
                        'before_sha256': sha256(bank[at:at+len(data)]), 'sha256': sha256(data)})

    camera = converted(rel[DATA_BASE+0x87EE40:DATA_BASE+0x87F240], 64, 16, 'ia8', 8)
    cash = converted(rel[DATA_BASE+0x8966A0:DATA_BASE+0x8968A0], 64, 16, 'i4', 4)
    if (sha256(camera), sha256(cash)) != (
            'e2d6b8e8ee0ef9fca9842dd58bf0cc5d97661e7550fc8ecb793f1cf6282428ae',
            '0eb7b7564fa8a8358b2ead089eeee0bb1571f1b00e9ce29cf70656e551482686'):
        raise ValueError('Changed decoded English HUD pixels')
    put(0x8F8, camera, 'V1-04: Camera, exact English GC texture')
    put(0xB4D0, cash+bytes(256), 'V1-11: Your Bells, English texture and cleared unused tail')
    put(0xB480, commands['cash'], 'V1-11: 64-by-16 I4 load in original command space')
    donor_quad = rel[DATA_BASE+0x8971E0:DATA_BASE+0x897220]
    put(0xB320, port_quad(bank[0xB320:0xB360], donor_quad, scale=1),
        'V1-11: English label geometry; native flags/colours retained')
    for model, (quad, delta, bounds) in zip(CLOCK_MODELS, CLOCK):
        end = bank.find(struct.pack('>2I', 0xDF000000, 0), model)
        if end == -1 or struct.pack('>2I', 0x01004008, 0x04000000+quad) not in bank[model:end]:
            raise ValueError('Clock model does not bind its expected quad')
        vertices = list(struct.iter_unpack('>3hH2h4B', bank[quad:quad+64]))
        if tuple(sorted({v[0] for v in vertices})) != bounds:
            raise ValueError('Changed native clock placement')
        moved = b''.join(struct.pack('>3hH2h4B', v[0]+delta, *v[1:]) for v in vertices)
        put(quad, moved, 'V1-05: horizontal reorder only; preserve time selection and blink')
    return bytes(changed), changes


def build(native, base, rel, symbols, commands):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('HUD fixes require the checked title/pixel-editor predecessor')
    bank, changes = patch_bank(by_vrom(base)[VROM].extract(base), rel, symbols, commands)
    image = reconstruct(native, base, {VROM: bank})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('HUD patch reconstruction failed')
    report = {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
              'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
              'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
              'asset_vrom': f'{VROM:08X}', 'asset_sha256': sha256(bank), 'changes': changes,
              'command_source_sha256': sha256(SOURCE.read_bytes()),
              'rom_bytes': len(image), 'required_ram_bytes': 0x800000,
              'code_changed': False, 'allocation_changed': False, 'save_format_changed': False,
              'fixed_issues': ['V1-04', 'V1-05', 'V1-11'], 'hardware_retest': 'pending'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1-editor-pixel-fix-03')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-hud-label-fix-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    commands = compile_commands(args.output/'commands', SOURCE, (('cash', 56),))
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (args.base/'animal-forest-title-preview.z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), commands)
    for name, data in {'animal-forest-title-preview.z64': image,
                       'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
