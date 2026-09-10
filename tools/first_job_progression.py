"""Guarded first-job conversation correction, retaining the complete v0 ROM."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups
from npc_mail_show import OVERLAYS, source, relocate_verified_data
from package_v0 import CANDIDATE_SHA256

ROOT = Path(__file__).resolve().parents[1]
SPEC = OVERLAYS['first_job']
PATCHES = ((0x8091D2E0, 0x8E0E01D4, 0x240E000B),
           (0x8091D2E4, 0xAFAE0024, 0xA20E0186),
           (0x8091D320, 0x8FA50024, 0x8E0501D4))
LETTER_PATCH = (0x8091D4C8, 0x2408000C, 0x2408000B)


def patch(native, data, reloc, *, letter_advice=False):
    original, original_reloc = source(verified_rom(native), 'first_job')
    if data != original or reloc != original_reloc:
        raise ValueError('First-job fix requires its exact unchanged native owner')
    result = bytearray(data)
    changes = (*PATCHES, LETTER_PATCH) if letter_advice else PATCHES
    for address, before, after in changes:
        at = address-SPEC.ram
        if struct.unpack_from('>I', result, at)[0] != before:
            raise ValueError('Unexpected first-job reward instruction')
        struct.pack_into('>I', result, at, after)
    result = bytes(result)
    # No changed instruction is a relocation site. Retain the complete original
    # layout and check each word at two independently modelled heap placements.
    allowed = {i for address, _, _ in changes for i in range(address-SPEC.ram, address-SPEC.ram+4)}
    for base in (0x801A0010, 0x802F8010):
        old = relocate_verified_data(SPEC, data, reloc, base)
        new = relocate_verified_data(SPEC, result, reloc, base)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(old, new))):
            raise ValueError('First-job correction changes unrelated relocated state')
        for address, _, after in changes:
            if struct.unpack_from('>I', new, address-SPEC.ram)[0] != after:
                raise ValueError('First-job correction overlaps native relocation')
    return result


def build(native, base, report, *, shrine=False, letter_advice=False):
    verified_rom(native)
    if sha256(base) != CANDIDATE_SHA256 or report.get('output_sha256') != CANDIDATE_SHA256:
        raise ValueError('First-job correction requires the unchanged handed-off v0')
    files = by_vrom(base)
    changed = patch(native, files[SPEC.vrom].extract(base), files[SPEC.relocation].extract(base),
                    letter_advice=letter_advice)
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    if SPEC.vrom in moved or SPEC.relocation in moved:
        raise ValueError('First-job ownership changed')
    replacements[SPEC.vrom] = changed
    expected_changes = {SPEC.vrom: changed}
    map_profile = None
    if shrine:
        from shrine_labels import patch as patch_shrine
        from map_names import VROM, NEW_VROM, NEW_RELOC
        map_data, map_profile = patch_shrine(native, files[NEW_VROM].extract(base),
            files[NEW_RELOC].extract(base), report['map_names']['overlay'], report['runtime_module'])
        replacements[VROM] = map_data
        expected_changes[NEW_VROM] = map_data
    image = replace_dma(native, replacements, moved, additions)
    installed = by_vrom(image)
    if set(installed) != set(files) or len(image) != len(base):
        raise ValueError('First-job correction changes ROM size or DMA identities')
    for vrom, entry in files.items():
        actual = installed[vrom].extract(image)
        expected = expected_changes.get(vrom, entry.extract(base))
        if vrom == 0x19D40:  # Rebuilt DMA table; its full rows are checked above/below.
            actual, expected = actual[:16], expected[:16]
        if actual != expected or installed[vrom].index != entry.index:
            raise ValueError(f'First-job correction loses prior resource {vrom:08X}')
    ups = make_ups(native, image)
    if apply_ups(native, ups) != image:
        raise ValueError('First-job patch reconstruction failed')
    result = copy.deepcopy(report)
    if map_profile is not None:
        result['map_names']['overlay'] = map_profile
    result.update(output_sha256=sha256(image), patch_sha256=sha256(ups),
                  replacement_files=[f'{v:08X}' for v in sorted(replacements)],
                  release_status='Separate first-job correction; focused native verification pending')
    result['first_job_progression'] = {
        'baseline_sha256': CANDIDATE_SHA256, 'overlay_sha256': sha256(changed),
        'native_overlay_sha256': SPEC.file_sha256, 'relocation_sha256': SPEC.relocation_sha256,
        'patches': [{'address': f'{a:08X}', 'before': f'{b:08X}', 'after': f'{c:08X}'}
                    for a, b, c in ((*PATCHES, LETTER_PATCH) if letter_advice else PATCHES)],
        'assembly_source_sha256': sha256((ROOT/'overlays/first_job/reward.s').read_bytes()),
        'text_changed': False, 'save_layout_changed': False, 'memory_requirement_mib': 4,
        'status': 'Candidate; conversation-owner execution pending'}
    if letter_advice:
        result['first_job_progression'].update(letter_advice=True,
            letter_assembly_source_sha256=sha256((ROOT/'overlays/first_job/letter_advice.s').read_bytes()))
    if shrine:
        from map_names import verify_shared_parts
        verify_shared_parts(image, native, result['runtime_module'], result['map_names'])
    return image, ups, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/v0-first-job-fix-01')
    parser.add_argument('--shrine', action='store_true', help='Also correct the native shrine map label')
    parser.add_argument('--letter-advice', action='store_true', help='Also retain complete later first-job letter advice')
    args = parser.parse_args()
    baseline = ROOT/'build/classic-letters-pilot'
    image, ups, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(), json.loads((baseline/'build.json').read_text()),
        shrine=args.shrine, letter_advice=args.letter_advice)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in (('animal-forest-halfwidth.z64', image), ('animal-forest-halfwidth.ups', ups),
                       ('build.json', (json.dumps(report, indent=2)+'\n').encode())):
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps({k: report[k] for k in ('output_sha256', 'patch_sha256', 'release_status')}))


if __name__ == '__main__':
    main()
