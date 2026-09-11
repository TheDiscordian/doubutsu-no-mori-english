"""Package the committed tune/Pak menu corrections as the private RC6 candidate."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256, sha256, verified_rom
from apply_translation import apply_bundle, write_new
from package_v0 import archive_bytes
from package_v1rc2 import revision_valid
from rebuild_v1 import checked_output, source_state

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_SHA = '6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4'
INTERMEDIATE_SHA = '5f85299d975858017f6d822664933bc332908cde17adf7ff0f4b175e941b1f13'
FINAL_SHA = '800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09'
PATCH_SHA = '51702b426b92097686087fc1bf239fe1ed4e4eb7c91a9bacdbbfb288de33e0bb'
ROM_NAME = 'Animal Forest English V1RC6.z64'
STAGES = (
    ('tools/tune_confirmation.py', 'e5111adfc9c6212301045a85d6304fd44865b3cd66826693bfba727b85ea8e6e',
     PREVIOUS_SHA, INTERMEDIATE_SHA),
    ('tools/pak_erase_heading.py', 'cd41ade17423d63e639beee8bc390b2922a776c3ad9498f03c3ef90134a81ee6',
     INTERMEDIATE_SHA, FINAL_SHA),
)


def verify_receipts(raws):
    if len(raws) != len(STAGES):
        raise ValueError('RC6 requires both committed correction receipts')
    stages = []
    for raw, (builder, builder_sha, before, after) in zip(raws, STAGES):
        report = json.loads(raw)
        if (report.get('source_sha256') != ROM_SHA256 or report.get('version') != 1
                or report.get('baseline_sha256') != before or report.get('output_sha256') != after
                or report.get('source_builder_sha256') != builder_sha
                or sha256((ROOT/builder).read_bytes()) != builder_sha
                or report.get('required_ram_bytes') != 0x800000
                or report.get('worktree_modified') is not False
                or any(report.get(key) is not False for key in ('saved_format_changed',
                    'save_readers_writers_changed', 'allocation_changed', 'relocation_changed'))
                or not revision_valid(report.get('source_revision'))):
            raise ValueError('RC6 requires the exact checked, committed menu-correction stages')
        committed = subprocess.run(['git', 'show', report['source_revision']+':'+builder],
                                   cwd=ROOT, check=True, capture_output=True).stdout
        if sha256(committed) != report['source_builder_sha256']:
            raise ValueError('Correction builder does not match its recorded Git revision')
        stages.append({'builder': builder, 'source_revision': report['source_revision'],
                       'builder_sha256': report['source_builder_sha256'], 'receipt_sha256': sha256(raw),
                       'input_sha256': before, 'output_sha256': after})
    return stages


def prepare(directory, tune_directory, native, revision):
    native = verified_rom(native)
    if not revision_valid(revision):
        raise ValueError('RC6 packaging needs a complete source revision')
    subprocess.run(['git', 'cat-file', '-e', revision+'^{commit}'], cwd=ROOT, check=True, capture_output=True)
    stages = verify_receipts([(tune_directory/'fixes.json').read_bytes(), (directory/'fixes.json').read_bytes()])
    image = (directory/'animal-forest-menu-followup.z64').read_bytes()
    patch = (directory/'animal-forest-menu-followup.ups').read_bytes()
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or len(image) != 0x2000000:
        raise ValueError('RC6 cartridge or patch differs from the checked combined build')
    manifest = {'format': 1, 'label': 'V1RC6', 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'packaging_source_revision': revision, 'correction_stages': stages,
        'previous_candidate': 'V1RC5', 'previous_candidate_sha256': PREVIOUS_SHA,
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'corrected_findings': [f'V1-{i:02}' for i in range(1, 26)],
        'new_findings': ['V1-24', 'V1-25'], 'original_hardware_verified': False,
        'human_playthrough_complete': False, 'ordinary_menu_appearance_verified': False,
        'ordinary_save_restart_verified': False, 'native_execution_on_this_candidate_verified': False,
        'earlier_native_evidence': 'Retained on its actual tested candidates; not fresh RC6 execution',
        'save_compatibility': {'previous_candidate': 'V1RC5', 'migration_required': False,
            'forward': 'expected, not independently verified', 'backward': 'expected, not independently verified',
            'basis': 'Saved formats and readers/writers unchanged; only menu strings, pointer/count words, and heading centring change',
            'warning': 'Keep original backups and test copies; do not use RC3 as a fallback'}}
    if apply_bundle(native, patch, manifest) != image:
        raise ValueError('RC6 UPS does not reconstruct the checked complete candidate')
    sources = (ROOT/'docs/SOURCES.md').read_bytes()
    if sources.count(b'](TOOLCHAIN.md)') != 1:
        raise ValueError('Review the source-guide link before packaging')
    sources = sources.replace(b'](TOOLCHAIN.md)',
        f'](https://github.com/TheDiscordian/doubutsu-no-mori-english/blob/{revision}/docs/TOOLCHAIN.md)'.encode())
    members = {'animal-forest-english.ups': patch,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC6_PLAYTEST.md').read_bytes(), 'SOURCES.md': sources,
        'LICENSE-tooling.txt': (ROOT/'LICENSE').read_bytes(),
        'apply_translation.py': (ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py': (ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS'] = ''.join(f'{sha256(value)}  {name}\n' for name, value in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/menu-text-followup-01')
    p.add_argument('--tune-build', type=Path, default=ROOT/'build/tune-confirmation-01')
    p.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1rc6')
    a = p.parse_args()
    output = checked_output(a.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit RC6 sources before packaging')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    package, manifest, image = prepare(a.build, a.tune_build, a.native.read_bytes(), revision)
    with tempfile.TemporaryDirectory(prefix='af-rc6-patch-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as bundle:
            bundle.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'), '--rom',
            str(a.native.resolve()), '--output', str(folder/'verified.z64')],
            check=True, capture_output=True, text=True, timeout=60)
        if (folder/'verified.z64').read_bytes() != image or json.loads(result.stdout)['sha256'] != FINAL_SHA:
            raise ValueError('Archived standalone patcher differs from the checked RC6 candidate')
    output.mkdir(parents=True, exist_ok=False)
    verification = {'standalone_patcher_passed': True, 'output_sha256': FINAL_SHA,
                    'archive_sha256': sha256(package), 'original_hardware_verified': False}
    for name, value in {ROM_NAME: image, 'V1RC6-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC6_PLAYTEST.md').read_bytes()}.items():
        write_new(output/name, value)
    print(json.dumps({'rom': str(output/ROM_NAME), **verification}, indent=2))


if __name__ == '__main__':
    main()
