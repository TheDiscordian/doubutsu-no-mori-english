"""Package the checked RC2 replay, execute its portable patcher, and retain RC1."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256, sha256, verified_rom
from apply_translation import apply_bundle, write_new
from package_v0 import archive_bytes
from rebuild_v1rc2 import BASE_SHA, FINAL_SHA, PATCH_SHA, STAGES

ROOT=Path(__file__).resolve().parents[1]
ROM_NAME='Animal Forest English V1RC2.z64'


def revision_valid(value):
    return isinstance(value,str) and len(value)==40 and all(c in '0123456789abcdef' for c in value)


def prepare(directory,source,revision,native_result):
    source=verified_rom(source)
    image=(directory/'animal-forest-title-preview.z64').read_bytes()
    patch=(directory/'animal-forest-title-preview.ups').read_bytes()
    raw=(directory/'fixes.json').read_bytes(); report=json.loads(raw)
    if (sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or len(image)!=0x2000000
            or report.get('kind')!='v1rc2_followup_rebuild' or report.get('complete_rebuild') is not True
            or report.get('worktree_modified') is not False or not revision_valid(report.get('source_revision'))
            or report.get('output_sha256')!=FINAL_SHA or report.get('patch_sha256')!=PATCH_SHA
            or report.get('required_ram_bytes')!=0x800000 or report.get('ordinary_heap_end')!=0x80400000
            or report.get('save_format_changed') is not False or not revision_valid(revision)):
        raise ValueError('V1RC2 requires the committed, complete, checked follow-up replay')
    if tuple(stage['name'] for stage in report['stages'])!=STAGES:
        raise ValueError('Incomplete V1RC2 sequence')
    prior=BASE_SHA
    for stage in report['stages']:
        profile=stage['profile']
        if profile.get('baseline_sha256')!=prior: raise ValueError('Disconnected RC2 correction stage')
        prior=profile['output_sha256']
    if prior!=FINAL_SHA: raise ValueError('RC2 correction sequence has the wrong final output')
    evidence=json.loads(native_result)
    checks=[r for r in evidence if 'native_background_calls' in r]
    if (evidence[0].get('rom_sha256')!=FINAL_SHA or evidence[0].get('audio')!='disabled'
            or len(checks)!=1 or checks[0].get('native_background_calls')!=5
            or checks[0].get('assertions')!=30 or checks[0].get('save_unchanged') is not True
            or checks[0].get('fixture_released') is not True
            or not any(r.get('loaded_state')=='test.bs1' for r in evidence)
            or evidence[-1].get('graceful_shutdown') is not True):
        raise ValueError('Missing complete same-ROM controlled keyboard evidence')
    manifest={'format':1,'label':'V1RC2','public_release':False,'complete_v1':False,
        'source_revision':'Doubutsu no Mori (Japan), verified retail','source_sha256':ROM_SHA256,
        'output_sha256':FINAL_SHA,'output_bytes':len(image),'patch_sha256':PATCH_SHA,
        'cartridge_source_revision':report['source_revision'],'packaging_source_revision':revision,
        'correction_rebuild_receipt_sha256':sha256(raw),'native_keyboard_receipt_sha256':sha256(native_result),
        'required_ram_bytes':0x800000,'expansion_pak_required':True,'ordinary_heap_end':0x80400000,
        'save_layout_changed':False,'save_type':'FlashRAM 128 KiB','rtc_required':True,
        'original_hardware_verified':False,'human_playthrough_complete':False,
        'ordinary_save_restart_verified':False,'keyboard_background_native_test_complete':True,
        'keyboard_ordinary_appearance_verified':False,'full_regression_passed':False,
        'embedded_warning_native_drawing_verified':False,
        'corrected_findings':[f'V1-{i:02}' for i in range(1,17)],'v2_keyboard_redesign_included':False}
    if apply_bundle(source,patch,manifest)!=image: raise ValueError('V1RC2 patch reconstruction failed')
    members={'animal-forest-english.ups':patch,
        'manifest.json':(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC2_PLAYTEST.md').read_bytes(),
        'SOURCES.md':(ROOT/'docs/SOURCES.md').read_bytes(),'LICENSE-tooling.txt':(ROOT/'LICENSE').read_bytes(),
        'apply_translation.py':(ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py':(ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS']=''.join(f'{sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    return archive_bytes(members),manifest,image


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/v1rc2-rebuild-01')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--native-result',type=Path,default=ROOT/'build/v1rc1-keyboard-native-02/results.json')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc2');a=p.parse_args()
    output=a.output.resolve()
    if a.output.is_symlink() or output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('RC2 output must be a fresh local build directory')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    package,manifest,image=prepare(a.build,a.native.read_bytes(),revision,a.native_result.read_bytes())
    with tempfile.TemporaryDirectory(prefix='af-v1rc2-patch-') as temp:
        directory=Path(temp); archive=directory/'patch.zip'; write_new(archive,package)
        with zipfile.ZipFile(archive) as bundle:bundle.extractall(directory/'bundle')
        result=subprocess.run(['python3',str(directory/'bundle/apply_translation.py'),
            '--rom',str(a.native.resolve()),'--output',str(directory/'verified.z64')],
            check=True,capture_output=True,text=True,timeout=60)
        if sha256((directory/'verified.z64').read_bytes())!=FINAL_SHA:
            raise ValueError('Standalone RC2 patcher output changed')
        verification={'standalone_patcher_passed':True,'output_sha256':json.loads(result.stdout)['sha256'],
                      'archive_sha256':sha256(package),'original_hardware_verified':False}
    output.mkdir()
    for name,data in {ROM_NAME:image,'V1RC2-patch.zip':package,
        'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode(),
        'verification.json':(json.dumps(verification,indent=2)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC2_PLAYTEST.md').read_bytes()}.items():write_new(output/name,data)
    print(json.dumps({'rom':str(output/ROM_NAME),'patch_archive':str(output/'V1RC2-patch.zip'),
                      'manifest':manifest,'verification':verification},indent=2))


if __name__=='__main__':main()
