"""Package the RC4 menu corrections as a private, source-bound RC5 playtest."""
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
from rc4_menu_labels import BASE_SHA, ROOT, source_hashes
from rebuild_v1 import checked_output, source_state

FINAL_SHA = '6ed7d636b953d24d4ad10ae8ea806deb133a752f4295ad79727c52336095dae4'
PATCH_SHA = 'aaa8c3c35f6ea187f375906af789823235a06599cdc6ce50af4049727f037ec8'
ROM_NAME = 'Animal Forest English V1RC5.z64'


def prepare(directory, native, revision):
    native = verified_rom(native)
    raw = (directory/'fixes.json').read_bytes()
    report = json.loads(raw)
    image = (directory/'animal-forest-menu-labels.z64').read_bytes()
    patch = (directory/'animal-forest-menu-labels.ups').read_bytes()
    if (sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA
            or report.get('output_sha256') != FINAL_SHA or report.get('patch_sha256') != PATCH_SHA
            or report.get('source_sha256') != ROM_SHA256 or report.get('baseline_sha256') != BASE_SHA
            or report.get('sources') != source_hashes() or report.get('save_format_changed') is not False
            or report.get('save_readers_writers_changed') is not False
            or report.get('price_and_repayment_arithmetic_changed') is not False
            or report.get('required_ram_bytes') != 0x800000 or report.get('worktree_modified') is not False
            or report.get('complete_correction_rebuild') is not True
            or not revision_valid(report.get('source_revision')) or not revision_valid(revision)):
        raise ValueError('RC5 requires the bound committed menu-correction replay')
    evidence_raw = (ROOT/'build/rc4-menu-labels-native-01/results.json').read_bytes()
    run_raw = (ROOT/'build/rc4-menu-labels-native-01/run.json').read_bytes()
    if (sha256(evidence_raw) != '0c82b25d708228b2219d27d679b81910094161cc9e7022d859e7669857c5b3fd'
            or sha256(run_raw) != '0c0260eac0ff5daf9a5438eb50f46b1cdcd21e247d943c820e40c04d5177eb61'):
        raise ValueError('Changed bound native price-adapter evidence')
    results, run = json.loads(evidence_raw), json.loads(run_raw)
    proof = [row for row in results if 'price_adapter_native_cases' in row]
    if (len(proof) != 1 or proof[0]['rom_sha256'] != FINAL_SHA
            or proof[0]['fixture_sha256'] != sha256((ROOT/'tools/rc4_menu_label_smoke.py').read_bytes())
            or [row['price'] for row in proof[0]['price_adapter_native_cases']] != [12345, 0]
            or not all(proof[0][key] is True for key in ('font_entry_restored', 'save_unchanged',
                                                       'guards_intact', 'allocation_released', 'font_drawing_stubbed'))
            or not any(row.get('loaded_state') == 'test.bs1' for row in results)
            or results[-1].get('graceful_shutdown') is not True or run['audio'] != 'disabled'
            or run['allow_test_flash_write'] or run['allow_test_pak_write']):
        raise ValueError('Incomplete native adapter check or overstated evidence scope')
    manifest = {'format': 1, 'label': 'V1RC5', 'public_release': False,
        'source_sha256': ROM_SHA256, 'output_sha256': FINAL_SHA, 'patch_sha256': PATCH_SHA,
        'output_bytes': len(image), 'cartridge_source_revision': report['source_revision'],
        'packaging_source_revision': revision, 'previous_candidate': 'V1RC4',
        'previous_candidate_sha256': BASE_SHA, 'correction_receipt_sha256': sha256(raw),
        'required_ram_bytes': 0x800000, 'expansion_pak_required': True,
        'save_type': 'FlashRAM', 'save_bytes': 131072, 'rtc_required': True,
        'corrected_findings': [f'V1-{i:02}' for i in range(1, 24)],
        'original_hardware_verified': False, 'human_playthrough_complete': False,
        'ordinary_menu_appearance_verified': False, 'ordinary_save_restart_verified': False,
        'native_price_adapter_capture': proof[0], 'native_results_sha256': sha256(evidence_raw),
        'save_compatibility': {'previous_candidate': 'V1RC4', 'migration_required': False,
            'forward': 'expected, not independently verified', 'backward': 'expected, not independently verified',
            'basis': 'Saved formats and readers/writers unchanged; presentation-only menu corrections',
            'warning': 'Preserve original backups and test copies; do not use RC3 as a fallback'}}
    if apply_bundle(native, patch, manifest) != image:
        raise ValueError('RC5 patch does not reconstruct the checked candidate')
    sources = (ROOT/'docs/SOURCES.md').read_bytes()
    if sources.count(b'](TOOLCHAIN.md)') != 1:
        raise ValueError('Review the source-guide link before packaging')
    sources = sources.replace(b'](TOOLCHAIN.md)',
        f'](https://github.com/TheDiscordian/doubutsu-no-mori-english/blob/{revision}/docs/TOOLCHAIN.md)'.encode())
    members = {'animal-forest-english.ups': patch,
        'manifest.json': (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC5_PLAYTEST.md').read_bytes(), 'SOURCES.md': sources,
        'LICENSE-tooling.txt': (ROOT/'LICENSE').read_bytes(),
        'apply_translation.py': (ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py': (ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS'] = ''.join(f'{sha256(value)}  {name}\n' for name, value in sorted(members.items())).encode()
    return archive_bytes(members), manifest, image


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/rc4-menu-labels-03')
    p.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/v1rc5')
    a = p.parse_args()
    output = checked_output(a.output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit RC5 sources before packaging')
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    package, manifest, image = prepare(a.build, a.native.read_bytes(), revision)
    with tempfile.TemporaryDirectory(prefix='af-rc5-patch-') as temporary:
        folder = Path(temporary)
        write_new(folder/'patch.zip', package)
        with zipfile.ZipFile(folder/'patch.zip') as bundle:
            bundle.extractall(folder/'bundle')
        result = subprocess.run(['python3', str(folder/'bundle/apply_translation.py'), '--rom',
            str(a.native.resolve()), '--output', str(folder/'verified.z64')],
            check=True, capture_output=True, text=True, timeout=60)
        if (folder/'verified.z64').read_bytes() != image or json.loads(result.stdout)['sha256'] != FINAL_SHA:
            raise ValueError('Standalone RC5 patcher differs from the checked candidate')
    output.mkdir(parents=True, exist_ok=False)
    verification = {'standalone_patcher_passed': True, 'output_sha256': FINAL_SHA,
                    'archive_sha256': sha256(package), 'original_hardware_verified': False}
    for name, value in {ROM_NAME: image, 'V1RC5-patch.zip': package,
        'manifest.json': (json.dumps(manifest, indent=2)+'\n').encode(),
        'verification.json': (json.dumps(verification, indent=2)+'\n').encode(),
        'README.md': (ROOT/'docs/V1RC5_PLAYTEST.md').read_bytes()}.items():
        write_new(output/name, value)
    print(json.dumps({'rom': str(output/ROM_NAME), **verification}, indent=2))


if __name__ == '__main__':
    main()
