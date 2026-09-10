"""Package the memory/space corrections with verified loading and honest save notes."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256, sha256, verified_rom
from apply_translation import apply_bundle, write_new
from font_expansion_memory import BASE_SHA, source_hashes
from rebuild_v1rc4 import FINAL_SHA, PATCH_SHA
from rc4_native_evidence import verify as verify_native
from package_v0 import archive_bytes
from package_v1rc2 import revision_valid
from rebuild_v1 import checked_output, source_state

ROOT = Path(__file__).resolve().parents[1]
ROM_NAME = 'Animal Forest English V1RC4.z64'
PARENT_MANIFEST_SHA = '28f3ab1ffea3dfefd0efe6e3ae3df583df11e36a3fa490a199eddefda7c19c11'


def prepare(directory, native, base, revision, parent_raw):
    native = verified_rom(native)
    if (sha256(parent_raw) != PARENT_MANIFEST_SHA or not revision_valid(revision)
            or sha256(base) != BASE_SHA):
        raise ValueError('RC4 requires the bound RC3 manifest and source revision')
    parent = json.loads(parent_raw)
    if parent['output_sha256'] != BASE_SHA:
        raise ValueError('Wrong preceding RC3 cartridge')
    image = (directory/'animal-forest-memory-fix.z64').read_bytes()
    patch = (directory/'animal-forest-memory-fix.ups').read_bytes()
    raw = (directory/'fixes.json').read_bytes()
    report = json.loads(raw)
    if (sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA
            or report.get('output_sha256') != FINAL_SHA or report.get('patch_sha256') != PATCH_SHA
            or report.get('baseline_sha256') != BASE_SHA or report.get('source_sha256') != ROM_SHA256
            or report.get('sources') != source_hashes() or report.get('save_format_changed') is not False
            or report.get('required_ram_bytes') != 0x800000):
        raise ValueError('RC4 artifact or sources differ from the checked memory correction')
    if (report.get('kind') != 'v1rc4_followup_rebuild' or report.get('complete_rebuild') is not True
            or report.get('worktree_modified') is not False or not revision_valid(report.get('source_revision'))):
        raise ValueError('RC4 requires a committed complete correction replay')
    evidence = verify_native(image, ROOT/'build')
    manifest = dict(parent)
    manifest.update(label='V1RC4', source_sha256=ROM_SHA256,
        output_sha256=sha256(image), patch_sha256=sha256(patch), output_bytes=len(image),
        cartridge_source_revision=report['source_revision'], packaging_source_revision=revision,
        correction_rebuild_receipt_sha256=sha256(raw), previous_candidate='V1RC3',
        previous_candidate_sha256=BASE_SHA, previous_manifest_sha256=PARENT_MANIFEST_SHA,
        retained_native_evidence_from='V1RC3 font drawing/transition checks; unchanged pixels/code, font address changes',
        font_test_resources_retained=False, font_image_retained=True,
        controlled_font_and_transition_checks_complete=False,
        native_loading_movement_memory_evidence=evidence,
        font_memory_region='80450000..80457FFF',
        space_marker_native_drawing_verified=False, space_marker_instruction_checks_complete=True,
        save_compatibility={'previous_candidate': 'V1RC3', 'forward': 'unverified', 'backward': 'unverified',
            'migration_required': False, 'rc2_to_rc4': 'supplied cartridge save loads; movement verified',
            'basis': 'Saved formats and readers/writers unchanged; RC3 town-memory failure corrected',
            'warning': 'RC3 has a known loading crash with older saves; preserve backups and use separate test copies',
            'ordinary_save_restart_verified': False},
        corrected_findings=[f'V1-{i:02}' for i in range(1, 21)])
    if apply_bundle(native, patch, manifest) != image:
        raise ValueError('RC4 bundle reconstruction failed')
    sources = (ROOT/'docs/SOURCES.md').read_bytes()
    toolchain_link = b'](TOOLCHAIN.md)'
    if sources.count(toolchain_link) != 1:
        raise ValueError('Changed source-note toolchain link; review the packaged document')
    # This guide belongs to the source tree, not the standalone patch archive.
    sources = sources.replace(toolchain_link,
        f'](https://github.com/TheDiscordian/doubutsu-no-mori-english/blob/{revision}/docs/TOOLCHAIN.md)'.encode())
    members = {'animal-forest-english.ups': patch,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC4_PLAYTEST.md').read_bytes(),
        'SOURCES.md': sources,
        'LICENSE-tooling.txt': (ROOT/'LICENSE').read_bytes(),
        'apply_translation.py': (ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py': (ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS'] = ''.join(f'{sha256(data)}  {name}\n' for name, data in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/v1rc4-rebuild-01')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc3/Animal Forest English V1RC3.z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1rc4')
    args = parser.parse_args()
    output = checked_output(args.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit RC4 packaging sources before handoff')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    package, manifest, image = prepare(args.build, args.native.read_bytes(), args.base.read_bytes(), revision,
                                      (ROOT/'build/v1rc3/manifest.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='af-v1rc4-patch-') as temporary:
        directory = Path(temporary)
        write_new(directory/'patch.zip', package)
        with zipfile.ZipFile(directory/'patch.zip') as bundle:
            bundle.extractall(directory/'bundle')
        result = subprocess.run(['python3', str(directory/'bundle/apply_translation.py'),
            '--rom', str(args.native.resolve()), '--output', str(directory/'verified.z64')],
            check=True, capture_output=True, text=True, timeout=60)
        if (directory/'verified.z64').read_bytes() != image:
            raise ValueError('Standalone RC4 patcher output differs')
        verification = {'standalone_patcher_passed': True,
            'output_sha256': json.loads(result.stdout)['sha256'], 'archive_sha256': sha256(package),
            'original_hardware_verified': False, 'ordinary_save_restart_verified': False}
    output.mkdir(parents=True, exist_ok=False)
    for name, value in {ROM_NAME: image, 'V1RC4-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC4_PLAYTEST.md').read_bytes()}.items():
        write_new(output/name, value)
    print(json.dumps({'rom': str(output/ROM_NAME), 'verification': verification}, indent=2))


if __name__ == '__main__':
    main()
