"""Package V1 Final from the completed development output, without rebuilding."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256, sha256
from apply_translation import write_new
from package_v0 import archive_bytes
from package_v1_current import (DOCUMENTS as BASE_DOCUMENTS, git,
                                validate_documents, verify_build_report)
from rebuild_v1 import checked_output

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'V1 Final'
ROM_NAME = f'Animal Forest English {LABEL}.z64'
FINAL_SHA = '0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf'
PATCH_SHA = 'acdfe82eae085337cc23d261154fbd06004f56d234b0a76587d2e6885047ae47'
PREVIOUS_SHA = '2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4'
RECEIPT_SHA = '20f302a4b1f37a4ba9f7a6e168e8015a569f64c87f36406d34a490e0564368b0'
BUILD_REVISION = '5dcc07ed779f18ba1973e055e67c65b9855190d5'
BUILDER_SHA = '570750f79c90ad4fd8c4fbc13e116d176143b8ec7939bb88c3a66aa9b18ff00b'
DOCUMENTS = {**BASE_DOCUMENTS, 'README.md': 'docs/V1_FINAL.md'}


def verify_final_receipt(raw):
    if sha256(raw) != RECEIPT_SHA:
        raise ValueError('V1 Final requires the completed diagnostic build receipt')
    report = json.loads(raw)
    expected = {'source_sha256': ROM_SHA256, 'baseline_sha256': PREVIOUS_SHA,
        'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA, 'rom_bytes': 0x2000000,
        'source_builder_sha256': BUILDER_SHA, 'source_revision': BUILD_REVISION,
        'translated_records': 13, 'drawn_diagnostic_records': 12, 'unused_literal_records': 1,
        'text_storage_bytes': 252, 'instructions_changed': False, 'pointers_changed': False,
        'allocation_changed': False, 'menu_access_changed': False,
        'generation_behaviour_changed': False, 'saved_format_changed': False,
        'save_readers_writers_changed': False, 'required_ram_bytes': 0x800000,
        'native_execution_verified': False, 'original_hardware_verified': False,
        'prior_rc8_corrections_retained': True, 'worktree_modified': False}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('Final build contract changed')
    if sha256(git('show', BUILD_REVISION+':tools/main_diagnostic_text.py')) != BUILDER_SHA:
        raise ValueError('Final builder does not match its recorded committed source')
    return report


def prepare(directory, baseline_receipt, revision):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Packaging requires a complete committed source revision')
    git('cat-file', '-e', revision+'^{commit}')
    final = verify_final_receipt((directory/'fixes.json').read_bytes())
    baseline_raw = baseline_receipt.read_bytes()
    baseline = verify_build_report(baseline_raw)
    if final['baseline_sha256'] != baseline['output_sha256']:
        raise ValueError('Final stage does not retain the recorded correction baseline')
    image = (directory/'animal-forest-diagnostic-text.z64').read_bytes()
    patch = (directory/'animal-forest-diagnostic-text.ups').read_bytes()
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or len(image) != 0x2000000:
        raise ValueError('Final ROM or patch differs from its completed build')
    manifest = {'format': 1, 'label': LABEL, 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'packaging_source_revision': revision,
        'cartridge_source_revision': BUILD_REVISION, 'final_build_receipt_sha256': RECEIPT_SHA,
        'final_builder_sha256': BUILDER_SHA, 'baseline_build_revision': baseline['source_revision'],
        'baseline_build_report_sha256': sha256(baseline_raw),
        'baseline_recipe_sha256': baseline['recipe_sha256'],
        'correction_stages': 20, 'composed_source_stages': 109,
        'fresh_full_chain_executed': False,
        'previous_candidate': 'V1RC8', 'previous_candidate_sha256': PREVIOUS_SHA,
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'corrected_findings': [f'V1-{i:02}' for i in range(1, 30)],
        'new_findings': ['V1-29'], 'new_japanese_strings_translated': 13,
        'new_diagnostic_reader_strings': 12, 'new_unused_literals': 1,
        'original_hardware_verified': False, 'human_playthrough_complete': False,
        'new_candidate_gameplay_run': False,
        'prior_human_acceptance': {
            'source_record': 'docs/checkpoints/V1_HUMAN_ACCEPTANCE.md',
            'bundled_summary': 'README.md#verification-and-limits',
            'ordinary_save_restart_reload_confirmed': True,
            'confirmed_reported_findings': [f'V1-{i:02}' for i in range(1, 24)],
            'scope': 'Prior user hardware playtests; exact ROM hash not supplied; not fresh final execution'},
        'save_compatibility': {'previous_candidate': 'V1RC8', 'migration_required': False,
            'forward': 'expected, not independently verified',
            'backward': 'expected, not independently verified',
            'basis': 'Thirteen in-place literals only; instructions, pointers, allocations, and save code unchanged',
            'warning': 'Keep save backups; a new ROM name may select a new save filename; do not use RC3 as fallback'}}
    members = {name: (ROOT/source).read_bytes() for name, source in DOCUMENTS.items()}
    manifest['bundled_source_sha256'] = {DOCUMENTS[name]: sha256(raw) for name, raw in members.items()}
    members['animal-forest-english.ups'] = patch
    members['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    validate_documents(members)
    members['SHA256SUMS'] = ''.join(f'{sha256(raw)}  {name}\n'
        for name, raw in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/main-diagnostic-text-01')
    parser.add_argument('--baseline-receipt', type=Path, default=ROOT/'build/v1-current-01/final/build.json')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-final')
    args = parser.parse_args()
    output = checked_output(args.output)
    if git('status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Commit final package code and documents before packaging')
    revision = git('rev-parse', 'HEAD').decode().strip()
    package, manifest, image = prepare(args.build, args.baseline_receipt, revision)
    with tempfile.TemporaryDirectory(prefix='af-final-package-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as archive:
            archive.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'),
            '--rom', str(args.native.resolve()), '--output', str(folder/'verified.z64')],
            cwd=folder, check=True, capture_output=True, text=True, timeout=60)
        if ((folder/'verified.z64').read_bytes() != image
                or json.loads(result.stdout)['sha256'] != FINAL_SHA):
            raise ValueError('Final standalone patcher did not recreate the complete cartridge')
    if git('rev-parse', 'HEAD').decode().strip() != revision or git('status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Source changed during final packaging')
    verification = {'standalone_patcher_passed': True, 'output_sha256': FINAL_SHA,
        'archive_sha256': sha256(package), 'packaging_source_revision': revision,
        'old_builds_retested': False, 'gameplay_tests_run': False,
        'original_hardware_verified': False}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in {ROM_NAME: image, 'V1-Final-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/DOCUMENTS['README.md']).read_bytes()}.items():
        write_new(output/name, raw)
    print(json.dumps({'rom': str(output/ROM_NAME), **verification}, indent=2))


if __name__ == '__main__':
    main()
