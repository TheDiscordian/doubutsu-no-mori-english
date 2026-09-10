"""Prepare the checked V1RC1 patch archive and local ROM without overwriting files."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256, sha256, verified_rom
from apply_translation import apply_bundle, write_new
from package_v0 import archive_bytes
from rebuild_v1_fixes import BASE_SHA, FINAL_SHA, PATCH_SHA

ROOT=Path(__file__).resolve().parents[1]
CARTRIDGE_REVISION='d56215cc4b3afcafbfa2ec26146ace20afc7eefb'
ROM_NAME='Animal Forest English V1RC1.z64'
STAGES=('press-start','editor-pixels','hud','notice-tune','inventory-money','letter-ui','keyboard-background')


def prepare(directory, source, revision):
    source=verified_rom(source)
    image=(directory/'animal-forest-title-preview.z64').read_bytes()
    patch=(directory/'animal-forest-title-preview.ups').read_bytes()
    raw=(directory/'fixes.json').read_bytes(); report=json.loads(raw)
    if (sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or len(image)!=0x2000000
            or report.get('kind')!='combined_v1_playtest_corrections' or not report.get('complete_rebuild')
            or report.get('output_sha256')!=FINAL_SHA or report.get('patch_sha256')!=PATCH_SHA
            or report.get('required_ram_bytes')!=0x800000 or report.get('ordinary_heap_end')!=0x80400000
            or report.get('save_format_changed') is not False):
        raise ValueError('V1RC1 requires the checked complete correction replay')
    if tuple(stage['name'] for stage in report['stages'])!=STAGES:
        raise ValueError('Incomplete V1RC1 correction sequence')
    prior=BASE_SHA
    for stage in report['stages']:
        profile=stage['profile']
        if profile.get('baseline_sha256')!=prior: raise ValueError('Disconnected correction stage')
        prior=profile['output_sha256']
    if prior!=FINAL_SHA or len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Invalid final correction or packaging revision')
    manifest={'format':1,'label':'V1RC1','public_release':False,'complete_v1':False,
        'source_revision':'Doubutsu no Mori (Japan), verified retail','source_sha256':ROM_SHA256,
        'output_sha256':FINAL_SHA,'output_bytes':len(image),'patch_sha256':PATCH_SHA,
        'cartridge_source_revision':CARTRIDGE_REVISION,'packaging_source_revision':revision,
        'correction_rebuild_receipt_sha256':sha256(raw),'required_ram_bytes':0x800000,
        'expansion_pak_required':True,'ordinary_heap_end':0x80400000,'save_layout_changed':False,
        'original_hardware_verified':False,'human_playthrough_complete':False,
        'ordinary_save_restart_verified':False,'keyboard_background_native_test_complete':False,
        'embedded_warning_native_drawing_verified':False,'corrected_findings':[f'V1-{i:02}' for i in range(1,13)]}
    if apply_bundle(source,patch,manifest)!=image: raise ValueError('V1RC1 patch reconstruction failed')
    members={'animal-forest-english.ups':patch,
        'manifest.json':(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC1_PLAYTEST.md').read_bytes(),
        'SOURCES.md':(ROOT/'docs/SOURCES.md').read_bytes(),
        'LICENSE-tooling.txt':(ROOT/'LICENSE').read_bytes(),
        'apply_translation.py':(ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py':(ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS']=''.join(f'{sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    return archive_bytes(members),manifest,image


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/v1-fixes-rebuild-01')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc1');args=p.parse_args()
    output=args.output.resolve()
    if args.output.is_symlink() or output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('V1RC1 output must be a new local build directory')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    package,manifest,image=prepare(args.build,args.native.read_bytes(),revision)
    # Execute the actual portable patcher, separately from the in-process check.
    with tempfile.TemporaryDirectory(prefix='af-v1rc1-patch-') as temporary:
        directory=Path(temporary);archive=directory/'patch.zip';write_new(archive,package)
        with zipfile.ZipFile(archive) as bundle: bundle.extractall(directory/'bundle')
        result=subprocess.run(['python3',str(directory/'bundle/apply_translation.py'),
            '--rom',str(args.native.resolve()),'--output',str(directory/'verified.z64')],
            capture_output=True,text=True,check=True,timeout=60)
        if sha256((directory/'verified.z64').read_bytes())!=FINAL_SHA:
            raise ValueError('Standalone V1RC1 patcher output changed')
        verification={'standalone_patcher_passed':True,'output_sha256':json.loads(result.stdout)['sha256'],
                      'archive_sha256':sha256(package),'original_hardware_verified':False}
    output.mkdir()
    for name,data in {ROM_NAME:image,'V1RC1-patch.zip':package,
        'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode(),
        'verification.json':(json.dumps(verification,indent=2)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC1_PLAYTEST.md').read_bytes()}.items():
        write_new(output/name,data)
    print(json.dumps({'rom':str(output/ROM_NAME),'patch_archive':str(output/'V1RC1-patch.zip'),
                      'manifest':manifest,'verification':verification},indent=2))


if __name__=='__main__':main()
