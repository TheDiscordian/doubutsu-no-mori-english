"""Package the completed current V1 build with self-contained playtest documents."""
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
from rebuild_v1 import checked_output

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'V1RC8'
ROM_NAME = f'Animal Forest English {LABEL}.z64'
FINAL_SHA = '2a04f6e5c54dc2d5ed03009395af815b464bebdef51d67d899554deb54b3bcb4'
PATCH_SHA = 'c3931b2e029bf4182864306ed2cbf28ea4c1d6c9d609cd33d68047132029b769'
PREVIOUS_SHA = '3a2e8b4241837daa7cea094deb2f2d229b2fa34755cf9103e493e27b1cf3fd8a'
BUILD_SHA = '4a0df7d8d6cffa2658303bb633fe45877a418a0e7796df2663af0baa7916cfb6'
BUILD_REVISION = 'b193042a53c85652195756dfab945c64ba148b42'
RECIPE_SHA = '8d37fbd75f99297b18f706e41a3b7dd10e610247d630bb450f166521cfa7d8ff'
DOCUMENTS = {
    'README.md': 'docs/V1RC8_PLAYTEST.md',
    'SOURCES.md': 'docs/SOURCES.md',
    'TOOLCHAIN.md': 'docs/release/TOOLCHAIN.md',
    'BUG_REPORT.md': 'docs/release/BUG_REPORT.md',
    'LICENSE-tooling.txt': 'LICENSE',
    'apply_translation.py': 'tools/apply_translation.py',
    'aflib.py': 'tools/aflib.py',
}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def verify_build_report(raw):
    # Bind the completed current build, without revisiting old intermediate ROMs.
    if sha256(raw) != BUILD_SHA:
        raise ValueError('Package requires the recorded completed current V1 build report')
    report = json.loads(raw)
    expected = {'kind': 'current_v1_correction_rebuild', 'complete': True,
        'source_revision': BUILD_REVISION, 'recipe_sha256': RECIPE_SHA,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'groups': 10, 'correction_stages': 19, 'rom_bytes': 0x2000000,
        'required_ram_bytes': 0x800000, 'save_type': 'FlashRAM', 'save_bytes': 131072,
        'rtc_required': True, 'save_format_changed': False,
        'native_tests_run': False, 'original_hardware_verified': False}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('Current V1 build contract changed')
    if sha256(git('show', BUILD_REVISION+':tools/rebuild_v1_current.py')) != RECIPE_SHA:
        raise ValueError('Current build recipe does not match its committed source')
    return report


def validate_documents(members):
    """Every relative Markdown link in the shipped guide resolves inside the ZIP."""
    for name, raw in members.items():
        if not name.endswith('.md'):
            continue
        content = raw.decode('utf-8')
        if '/home/' in content or '/run/media/' in content:
            raise ValueError('Do not package private machine paths')
        for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
            target = href.split('#', 1)[0]
            if target and '://' not in target and target not in members:
                raise ValueError(f'Unbundled documentation link in {name}: {href}')


def prepare(directory, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Packaging needs a complete source revision')
    git('cat-file', '-e', revision+'^{commit}')
    report = verify_build_report((directory/'build.json').read_bytes())
    image = (directory/'Animal Forest English V1-current.z64').read_bytes()
    patch = (directory/'animal-forest-english.ups').read_bytes()
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or len(image) != 0x2000000:
        raise ValueError('Current V1 ROM or patch differs from the completed build')
    manifest = {'format': 1, 'label': LABEL, 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'packaging_source_revision': revision,
        'cartridge_source_revision': BUILD_REVISION, 'build_report_sha256': BUILD_SHA,
        'build_recipe_sha256': RECIPE_SHA, 'correction_stages': report['correction_stages'],
        'previous_candidate': 'V1RC7', 'previous_candidate_sha256': PREVIOUS_SHA,
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'corrected_findings': [f'V1-{i:02}' for i in range(1, 29)],
        'new_findings': ['V1-28'], 'new_japanese_strings_translated': 76,
        'original_hardware_verified': False, 'human_playthrough_complete': False,
        'new_candidate_gameplay_run': False,
        'prior_human_acceptance': {
            'source_record': 'docs/checkpoints/V1_HUMAN_ACCEPTANCE.md',
            'bundled_summary': 'README.md#verification-and-limits',
            'ordinary_save_restart_reload_confirmed': True,
            'confirmed_reported_findings': [f'V1-{i:02}' for i in range(1, 24)],
            'scope': 'Prior user hardware playtests; exact ROM hash not supplied; not fresh RC8 execution'},
        'save_compatibility': {'previous_candidate': 'V1RC7', 'migration_required': False,
            'forward': 'expected, not independently verified',
            'backward': 'expected, not independently verified',
            'basis': 'Scene-menu text and display placement only; saved formats and readers/writers unchanged',
            'warning': 'Preserve save backups; RC3 retains its known town-loading memory defect'}}
    members = {name: (ROOT/source).read_bytes() for name, source in DOCUMENTS.items()}
    manifest['bundled_source_sha256'] = {DOCUMENTS[name]: sha256(raw) for name, raw in members.items()}
    members['animal-forest-english.ups'] = patch
    members['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    validate_documents(members)
    members['SHA256SUMS'] = ''.join(f'{sha256(raw)}  {name}\n'
        for name, raw in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/v1-current-01/final')
    p.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1rc8')
    args = p.parse_args()
    output = checked_output(args.output)
    if git('status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Commit package code and documents before packaging')
    revision = git('rev-parse', 'HEAD').decode().strip()
    package, manifest, image = prepare(args.build, revision)
    # Run only the new package's own offline patcher; no game or old build runs.
    with tempfile.TemporaryDirectory(prefix='af-current-package-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as bundle:
            bundle.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'),
            '--rom', str(args.native.resolve()), '--output', str(folder/'verified.z64')],
            cwd=folder, check=True, capture_output=True, text=True, timeout=60)
        if ((folder/'verified.z64').read_bytes() != image
                or json.loads(result.stdout)['sha256'] != FINAL_SHA):
            raise ValueError('Archived patcher does not reconstruct the complete current candidate')
    if git('rev-parse', 'HEAD').decode().strip() != revision or git('status', '--porcelain', '--untracked-files=all').strip():
        raise ValueError('Source changed during packaging')
    verification = {'standalone_patcher_passed': True, 'output_sha256': FINAL_SHA,
        'archive_sha256': sha256(package), 'packaging_source_revision': revision,
        'old_builds_retested': False, 'gameplay_tests_run': False,
        'original_hardware_verified': False}
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in {ROM_NAME: image, f'{LABEL}-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/DOCUMENTS['README.md']).read_bytes()}.items():
        write_new(output/name, raw)
    print(json.dumps({'rom': str(output/ROM_NAME), **verification}, indent=2))


if __name__ == '__main__':
    main()
