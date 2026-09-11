"""Prepare the private V2 offline patch handoff, without rebuilding the ROM."""
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
from package_v1_current import DOCUMENTS as BASE_DOCUMENTS, git, validate_documents
from rebuild_v1 import checked_output

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'V2 Development'
ROM_NAME = 'Animal Forest English V2 Development.z64'
ROM_SHA = '085e3dfc10cc03e591ce4197d7f3841c45e3fba3b51344d1be58c87cda2fe9d9'
PATCH_SHA = 'cbcee703fcf3f3957a112449a11e0718ac1a134fb440d2afddcfc6705228c888'
BASE_SHA = '0561182044c1526010ed77b1b9c72ac268794c2f7b615f8fa70c007f366483bf'
RECEIPT_SHA = '0ed07e68b807f2e48efc66270ce4ea0c4c75723aed46dea0ee6156dd352ecdfd'
BUILD_REVISION = '586d5abe50826358a39868e1d50dbe60f93bb145'
DOCUMENTS = {**BASE_DOCUMENTS, 'README.md': 'docs/V2_DEVELOPMENT.md',
    'TOOLCHAIN.md': 'docs/release/TOOLCHAIN_V2.md',
    'V1_SOURCE_BUILD.md': 'docs/release/TOOLCHAIN.md'}


def verify_receipt(raw):
    if sha256(raw) != RECEIPT_SHA:
        raise ValueError('V2 packaging requires the recorded current build receipt')
    report = json.loads(raw)
    expected = {'version': 2, 'baseline_sha256': BASE_SHA, 'source_sha256': ROM_SHA256,
        'output_sha256': ROM_SHA, 'patch_sha256': PATCH_SHA, 'required_ram_bytes': 0x800000,
        'shared_growth_bytes': 7744, 'existing_pool_extra_bytes': 8192, 'additional_pool_bytes': 0,
        'key_positions_changed': False, 'font_pixels_changed': False,
        'sound_code_changed': False, 'input_code_changed': False,
        'save_format_changed': False, 'public_release': False}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('V2 build contract changed')
    for source, digest in report['sources'].items():
        if sha256(git('show', BUILD_REVISION+':'+source)) != digest:
            raise ValueError('V2 build source does not match its recorded revision: '+source)
    return report


def prepare(directory, revision):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('Packaging requires a complete committed source revision')
    git('cat-file', '-e', revision+'^{commit}')
    report = verify_receipt((directory/'build.json').read_bytes())
    image = (directory/ROM_NAME).read_bytes()
    patch = (directory/ROM_NAME.replace('.z64', '.ups')).read_bytes()
    if sha256(image) != ROM_SHA or sha256(patch) != PATCH_SHA or len(image) != 0x2000000:
        raise ValueError('V2 ROM or patch differs from its recorded build')
    members = {name: (ROOT/source).read_bytes() for name, source in DOCUMENTS.items()}
    for name, source in DOCUMENTS.items():
        if git('show', revision+':'+source) != members[name]:
            raise ValueError('Bundle document or patcher has uncommitted changes: '+source)
    manifest = {'format': 1, 'label': LABEL, 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': ROM_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'packaging_source_revision': revision,
        'cartridge_source_revision': BUILD_REVISION, 'build_receipt_sha256': RECEIPT_SHA,
        'baseline_label': 'V1 Final', 'baseline_sha256': BASE_SHA,
        'cartridge_source_sha256': report['sources'], 'toolchain_image': report['toolchain_image'],
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'original_hardware_verified': False, 'human_playthrough_complete': False,
        'exact_output_gameplay_tested': False, 'fresh_full_chain_executed': False,
        'save_format_changed': False,
        'retained_native_evidence': {
            'rom_sha256': 'df903c293c98c9c8f942c95c47f7a8b1fbd8298ce86aa78d82eae2a4644fcd90',
            'scope': 'Controlled drawing and ordinary name entry before redundant-label removal',
            'source_record': 'docs/checkpoints/KEYBOARD_V2_ORDINARY.md',
            'bundled_summary': 'README.md#verification-and-limits'},
        'save_compatibility': {'previous_version': 'V1 Final', 'migration_required': False,
            'forward': 'expected, not independently verified',
            'backward': 'expected, not independently verified',
            'basis': 'Keyboard presentation suffix only; complete editing/input prefix and saved formats retained',
            'warning': 'Preserve backups and use the matching EverDrive save filename; RC3 is not a fallback'},
        'bundled_source_sha256': {DOCUMENTS[name]: sha256(raw) for name, raw in members.items()}}
    members['animal-forest-english.ups'] = patch
    members['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    validate_documents(members)
    members['SHA256SUMS'] = ''.join(f'{sha256(raw)}  {name}\n'
        for name, raw in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/v2-keyboard-05')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v2-private-bundle')
    args = parser.parse_args()
    output = checked_output(args.output)
    if git('status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Commit package code and documents before packaging')
    revision = git('rev-parse', 'HEAD').decode().strip()
    package, manifest, image = prepare(args.build, revision)
    with tempfile.TemporaryDirectory(prefix='af-v2-package-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as archive:
            archive.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'),
            '--rom', str(args.native.resolve()), '--output', str(folder/'verified.z64')],
            cwd=folder, check=True, capture_output=True, text=True, timeout=60)
        if ((folder/'verified.z64').read_bytes() != image
                or json.loads(result.stdout)['sha256'] != ROM_SHA):
            raise ValueError('V2 standalone patcher did not recreate the current cartridge')
    if (git('rev-parse', 'HEAD').decode().strip() != revision
            or git('status', '--porcelain', '--untracked-files=all').strip()):
        raise ValueError('Source changed during V2 packaging')
    verification = {'standalone_patcher_passed': True, 'output_sha256': ROM_SHA,
        'archive_sha256': sha256(package), 'packaging_source_revision': revision,
        'old_builds_retested': False, 'gameplay_tests_run': False,
        'original_hardware_verified': False, 'public_release': False}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in {'V2-Development-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/DOCUMENTS['README.md']).read_bytes()}.items():
        write_new(output/name, raw)
    print(json.dumps({'package': str(output/'V2-Development-patch.zip'), **verification}, indent=2))


if __name__ == '__main__':
    main()
