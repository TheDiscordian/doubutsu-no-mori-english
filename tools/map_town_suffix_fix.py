"""Remove the map's independent Japanese village-suffix bitmap on current V2."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256, verified_rom, make_ups, apply_ups
from apply_translation import write_new
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '259543536db43733d4a73ede05949ba52b1ce4ac3c557fc1c8e97b205856ad12'
ASSET_SHA = '39fadcd7853b28d3a7907d868541c06118d683509e102e1f53507809ef7fd3d5'
TEXTURE_SHA = '088faebeb065b56db12596786acbf8cfc9b605fa7ca258961e4872147d130f14'
VROM, START, SIZE = 0xAAD000, 0x11C8, 256
LOAD = bytes.fromhex('fd9000000c0011c8f590000007050150e600000000000000'
                     'f30000000707f400e700000000000000f580040000f50150f20000000007c03c')


def patch_asset(old):
    if (sha256(old) != ASSET_SHA or sha256(old[START:START+SIZE]) != TEXTURE_SHA
            or old[0x1178:0x11B0] != LOAD):
        raise ValueError('Changed current map asset or village-suffix texture reader')
    # I4 is used as both intensity and alpha by this existing material. Zero
    # removes only this lettering, retaining the frame, vertices, and commands.
    return old[:START]+bytes(SIZE)+old[START+SIZE:]


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Map suffix correction requires current V2-06')
    old = by_vrom(base)[VROM].extract(base)
    changed = patch_asset(old)
    image = reconstruct(native, base, {VROM: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Map suffix UPS reconstruction failed')
    return image, patch, {
        'build': 'V2-07', 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'source_builder_sha256': sha256(Path(__file__).read_bytes()),
        'asset_vrom': f'{VROM:08X}', 'texture_vrom': f'{VROM+START:08X}',
        'texture_bytes': SIZE, 'asset_sha256': sha256(changed),
        'change': 'Omit the separate map village suffix, matching English GameCube town labels',
        'saved_format_changed': False, 'saved_names_changed': False,
        'cpu_code_changed': False, 'allocation_changed': False,
        'other_resources_preserved': True, 'ups_roundtrip': True,
        'required_ram_bytes': 0x800000, 'public_release': False,
        'original_hardware_verified': False, 'trailer_modified': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v2-map-suffix-07')
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        raise ValueError('Choose a fresh directory inside ignored build/')
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/v2-keyboard-06/Animal Forest English V2 Development.z64').read_bytes())
    out.mkdir(parents=True)
    for name, raw in {'Animal Forest English V2.z64': image,
                      'Animal Forest English V2.ups': patch,
                      'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, raw)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
