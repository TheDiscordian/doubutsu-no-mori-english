"""Package committed title/gamestate wording corrections as the private RC7."""
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
PREVIOUS_SHA = '800c7e9d4e6a4b81db05d0a8258d151417d02c9edc47806cf3429e3d144fab09'
INTERMEDIATE_SHA = '614e387ee7591d935c091852512f7a60dc181fe25892843a2458c70a69e87037'
FINAL_SHA = '3a2e8b4241837daa7cea094deb2f2d229b2fa34755cf9103e493e27b1cf3fd8a'
PATCH_SHA = 'c477bd1e5fdeb7e36621bd7c594d23b369e9d97216eb2df68473c31a8a796427'
ROM_NAME = 'Animal Forest English V1RC7.z64'
STAGES = (
    ('tools/title_warning_text.py', '430131ad33af441433c6456875587de7d8eed0c69d28fa119050caa92c61a984',
     PREVIOUS_SHA, INTERMEDIATE_SHA),
    ('tools/gamestate_menu_text.py', '11de8c43235548860c05f221a131e0a460fa92dc96a4a676bd94f2969f5a5f0f',
     INTERMEDIATE_SHA, FINAL_SHA),
)


def verify_receipts(raws):
    if len(raws) != len(STAGES):
        raise ValueError('RC7 requires both committed correction receipts')
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
                    'save_readers_writers_changed', 'allocation_changed', 'relocation_changed', 'menu_actions_changed'))
                or not revision_valid(report.get('source_revision'))):
            raise ValueError('RC7 requires the exact checked, committed text-correction stages')
        committed = subprocess.run(['git', 'show', report['source_revision']+':'+builder],
                                   cwd=ROOT, check=True, capture_output=True).stdout
        if sha256(committed) != report['source_builder_sha256']:
            raise ValueError('Correction builder does not match its recorded Git revision')
        stages.append({'builder': builder, 'source_revision': report['source_revision'],
                       'builder_sha256': report['source_builder_sha256'], 'receipt_sha256': sha256(raw),
                       'input_sha256': before, 'output_sha256': after})
    return stages


def prepare(directory, title_directory, native, revision):
    native = verified_rom(native)
    if not revision_valid(revision):
        raise ValueError('RC7 packaging needs a complete source revision')
    subprocess.run(['git', 'cat-file', '-e', revision+'^{commit}'], cwd=ROOT, check=True, capture_output=True)
    stages = verify_receipts([(title_directory/'fixes.json').read_bytes(), (directory/'fixes.json').read_bytes()])
    image = (directory/'animal-forest-gamestate-text.z64').read_bytes()
    patch = (directory/'animal-forest-gamestate-text.ups').read_bytes()
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or len(image) != 0x2000000:
        raise ValueError('RC7 cartridge or patch differs from the checked combined build')
    manifest = {'format': 1, 'label': 'V1RC7', 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'packaging_source_revision': revision, 'correction_stages': stages,
        'previous_candidate': 'V1RC6', 'previous_candidate_sha256': PREVIOUS_SHA,
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'corrected_findings': [f'V1-{i:02}' for i in range(1, 28)],
        'new_findings': ['V1-26', 'V1-27'], 'original_hardware_verified': False,
        'human_playthrough_complete': False, 'ordinary_menu_appearance_verified': False,
        'ordinary_save_restart_verified': False, 'native_execution_on_this_candidate_verified': False,
        'prior_human_acceptance': {
            'evidence': 'docs/checkpoints/V1_HUMAN_ACCEPTANCE.md',
            'ordinary_save_restart_reload_confirmed': True,
            'confirmed_reported_findings': [f'V1-{i:02}' for i in range(1, 24)],
            'scope': 'User hardware playtests before RC7; exact ROM hash not supplied; not RC7 execution'},
        'earlier_native_evidence': 'Retained on its actual tested candidates; not fresh RC7 execution',
        'save_compatibility': {'previous_candidate': 'V1RC6', 'migration_required': False,
            'forward': 'expected, not independently verified', 'backward': 'expected, not independently verified',
            'basis': 'Saved formats and readers/writers unchanged; title/gamestate labels and bounded display copies change',
            'warning': 'Keep original backups and test copies; do not use RC3 as a fallback'}}
    if apply_bundle(native, patch, manifest) != image:
        raise ValueError('RC7 UPS does not reconstruct the checked complete candidate')
    sources = (ROOT/'docs/SOURCES.md').read_bytes()
    if sources.count(b'](TOOLCHAIN.md)') != 1:
        raise ValueError('Review the source-guide link before packaging')
    sources = sources.replace(b'](TOOLCHAIN.md)',
        f'](https://github.com/TheDiscordian/doubutsu-no-mori-english/blob/{revision}/docs/TOOLCHAIN.md)'.encode())
    members = {'animal-forest-english.ups': patch,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC7_PLAYTEST.md').read_bytes(), 'SOURCES.md': sources,
        'LICENSE-tooling.txt': (ROOT/'LICENSE').read_bytes(),
        'apply_translation.py': (ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py': (ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS'] = ''.join(f'{sha256(value)}  {name}\n' for name, value in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/gamestate-menu-text-01')
    p.add_argument('--title-build', type=Path, default=ROOT/'build/title-warning-text-01')
    p.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1rc7')
    a = p.parse_args()
    output = checked_output(a.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit RC7 sources before packaging')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    package, manifest, image = prepare(a.build, a.title_build, a.native.read_bytes(), revision)
    with tempfile.TemporaryDirectory(prefix='af-rc7-patch-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as bundle:
            bundle.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'), '--rom',
            str(a.native.resolve()), '--output', str(folder/'verified.z64')],
            check=True, capture_output=True, text=True, timeout=60)
        if (folder/'verified.z64').read_bytes() != image or json.loads(result.stdout)['sha256'] != FINAL_SHA:
            raise ValueError('Archived standalone patcher differs from the checked RC7 candidate')
    output.mkdir(parents=True, exist_ok=False)
    verification = {'standalone_patcher_passed': True, 'output_sha256': FINAL_SHA,
                    'archive_sha256': sha256(package), 'original_hardware_verified': False}
    for name, value in {ROM_NAME: image, 'V1RC7-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC7_PLAYTEST.md').read_bytes()}.items():
        write_new(output/name, value)
    print(json.dumps({'rom': str(output/ROM_NAME), **verification}, indent=2))


if __name__ == '__main__':
    main()
