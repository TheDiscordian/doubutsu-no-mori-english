"""Remove fixed-width ordinary-space markers from the shared name-entry window."""
import argparse
import json
from pathlib import Path
import struct
import subprocess

from aflib import apply_ups, by_vrom, make_ups, sha256, verified_rom
from apply_translation import write_new
from rebuild_v1 import checked_output, source_state
from title_start_fix import reconstruct

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = 'b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0'
VROM, RELOC, RAM = 0x78BFB0, 0x78CAD0, 0x80884340
OWNER_SHA = '5c8966332f57edcc9e8c33bd231b2d573c00e7fd30678872cd136add8e15a22f'
RELOC_SHA = '9da34103980ca7fd81005da0998aa6d39a8b1e74f81989a6565ee72c2c6c8741'
BRANCH, TARGET = 0x808847AC, 0x80884870
OLD, NEW, DELAY = 0x17010030, 0x10000030, 0x3C014320


def patch_overlay(data, relocation):
    if sha256(data) != OWNER_SHA or sha256(relocation) != RELOC_SHA:
        raise ValueError('Changed RC3 name-window owner or relocation')
    at = BRANCH - RAM
    if struct.unpack_from('>2I', data, at) != (OLD, DELAY):
        raise ValueError('Changed ordinary-space branch or delay slot')
    sections = struct.unpack_from('>5I', relocation)
    if sections != (2528, 288, 32, 560, 35):
        raise ValueError('Changed name-window section layout')
    for (row,) in struct.iter_unpack('>I', relocation[20:20+sections[4]*4]):
        section, offset = row >> 30, row & 0xFFFFFF
        if section not in (1, 2, 3):
            raise ValueError('Unsupported name-window relocation section')
        if sum(sections[:section-1]) + offset == at:
            raise ValueError('Space-marker branch must not be relocated')
    if BRANCH + 4 + (NEW & 0xFFFF)*4 != TARGET:
        raise ValueError('Space-marker branch does not reach the native continuation')
    changed = bytearray(data)
    struct.pack_into('>I', changed, at, NEW)
    return bytes(changed)


def build(native, base):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Space-marker correction requires exact V1RC3')
    files = by_vrom(base)
    old = files[VROM].extract(base)
    changed = patch_overlay(old, files[RELOC].extract(base))
    image = reconstruct(native, base, {VROM: changed})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Space-marker patch reconstruction failed')
    report = {'version': 1, 'baseline_sha256': BASE_SHA, 'source_sha256': sha256(native),
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'sources': {'tools/name_space_markers.py': sha256(Path(__file__).read_bytes())},
        'name_window_sha256': sha256(changed), 'relocation_sha256': RELOC_SHA,
        'changed_vrom': f'{VROM:08X}', 'changed_instruction_ram': f'{BRANCH:08X}',
        'old_instruction': f'{OLD:08X}', 'new_instruction': f'{NEW:08X}',
        'continuation_ram': f'{TARGET:08X}', 'changed_range_bytes': 4,
        'allocation_changed': False, 'input_code_changed': False, 'caret_code_changed': False,
        'save_format_changed': False, 'existing_save_loading_verified': False,
        'unresolved_findings': ['V1-20'],
        'save_compatibility_basis': 'Only one name-window drawing branch changes; save readers/writers are retained',
        'ordinary_save_restart_verified': False, 'required_ram_bytes': 0x800000,
        'fixed_issues': ['V1-19'], 'native_drawing_verified': False, 'hardware_retest': 'pending'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc3/Animal Forest English V1RC3.z64')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = checked_output(args.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit cartridge sources before the named marker replay')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    image, patch, report = build(args.native.read_bytes(), args.base.read_bytes())
    report.update(kind='name_space_marker_correction', source_revision=revision,
                  worktree_modified=False, complete_rebuild=True)
    output.mkdir(parents=True, exist_ok=False)
    for name, value in {'animal-forest-name-spaces.z64': image, 'animal-forest-name-spaces.ups': patch,
                        'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(output/name, value)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
