"""Package the checked RC3 replay and execute the archived standalone patcher."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from aflib import ROM_SHA256,by_vrom,sha256,verified_rom
from apply_translation import apply_bundle,write_new
from package_v0 import archive_bytes
from package_v1rc2 import revision_valid
from rebuild_v1rc3 import BASE_SHA,FINAL_SHA,PATCH_SHA,STAGES
from font_polygon_edges import MODULE,VROM
from transition_edges import BASE_SHA as FONT_SHA

ROOT=Path(__file__).resolve().parents[1]
ROM_NAME='Animal Forest English V1RC3.z64'
FONT_RESULT_SHA='03902f0c5a34283d827fa0b35e9fbd4640a420e90c390f6c24f661a05a7e7d8e'
BEFORE_RESULT_SHA='57b158f1036c9ede0a96ec95ee0e3bb611cdd62a74a93f0fc4b4b08e180ba6d7'
AFTER_RESULT_SHA='cff353ec4a71a413fa548f9ed1b31e8191d1fd2a99bd8026eec7d54a6d8c27ad'

def checked_evidence(raw,digest,rom_sha):
    result=json.loads(raw)
    if (sha256(raw)!=digest or result[0].get('rom_sha256')!=rom_sha
        or result[0].get('audio')!='disabled' or result[0].get('expansion_pak') is not True
        or result[-1].get('graceful_shutdown') is not True):
        raise ValueError('Missing bound complete native evidence')
    return result

def prepare(directory,native,revision,font_raw,before_raw,after_raw):
    native=verified_rom(native)
    image=(directory/'animal-forest-edge-fixes.z64').read_bytes()
    patch=(directory/'animal-forest-edge-fixes.ups').read_bytes()
    raw=(directory/'fixes.json').read_bytes();report=json.loads(raw)
    if (sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or len(image)!=0x2000000
        or report.get('kind')!='v1rc3_followup_rebuild' or report.get('complete_rebuild') is not True
        or report.get('worktree_modified') is not False or not revision_valid(report.get('source_revision'))
        or not revision_valid(revision) or report.get('output_sha256')!=FINAL_SHA
        or report.get('patch_sha256')!=PATCH_SHA or report.get('required_ram_bytes')!=0x800000
        or report.get('ordinary_heap_end')!=0x80400000 or report.get('save_format_changed') is not False):
        raise ValueError('RC3 requires the committed complete follow-up replay')
    if tuple(s['name'] for s in report['stages'])!=STAGES:raise ValueError('Incomplete RC3 sequence')
    prior=BASE_SHA
    for stage in report['stages']:
        if stage['profile']['baseline_sha256']!=prior:raise ValueError('Disconnected RC3 sequence')
        prior=stage['profile']['output_sha256']
    if prior!=FINAL_SHA:raise ValueError('Wrong final RC3 stage')
    font=checked_evidence(font_raw,FONT_RESULT_SHA,FONT_SHA)
    before=checked_evidence(before_raw,BEFORE_RESULT_SHA,FONT_SHA)
    after=checked_evidence(after_raw,AFTER_RESULT_SHA,FINAL_SHA)
    draws=[r for r in font if 'font_preview_draws' in r]
    if (len(draws)!=2 or any(r.get('guards_intact') is not True or r.get('save_unchanged') is not True for r in draws)
        or not any(r.get('bordered_font_cartridge_loaded') is True for r in font)
        or not any(r.get('font_preview_checkpoint_restored') is True for r in font)):
        raise ValueError('Incomplete installed font drawing evidence')
    # The font test predates the scale-only correction. Bind the retained
    # persistent resources explicitly; do not relabel it as same-ROM execution.
    files=by_vrom(image);font_profile=report['stages'][0]['profile']
    for v,key in ((MODULE,'module_sha256'),(VROM,'font_blob_sha256')):
        if sha256(files[v].extract(image))!=font_profile[key]:raise ValueError('RC3 does not retain the tested font')
    samples=[r for r in after if 'nonblack_pixels' in r]
    expected=((0,548),(1,548),(2,548),(0,274),(0,0))
    if ([(r['transition_model'],r['transition_phase']) for r in samples]!=list(expected)
        or any(r.get('guards_intact') is not True or r.get('save_unchanged') is not True for r in samples)
        or any(r['nonblack_pixels']!=0 for r in samples[:3])
        or not 0<samples[3]['nonblack_pixels']<76800 or samples[4]['nonblack_pixels']!=76800
        or not any(r.get('transition_checkpoint_restored') is True for r in after)
        or not any(r.get('transition_checkpoint_restored') is True for r in before)
        or not any(r.get('nonblack_pixels')==1908 and r.get('nonblack_top_rows')==[320,320,4,4] for r in before)):
        raise ValueError('Incomplete transition reproduction/correction evidence')
    manifest={'format':1,'label':'V1RC3','public_release':False,'complete_v1':False,
        'source_revision':'Doubutsu no Mori (Japan), verified retail','source_sha256':ROM_SHA256,
        'output_sha256':FINAL_SHA,'output_bytes':len(image),'patch_sha256':PATCH_SHA,
        'cartridge_source_revision':report['source_revision'],'packaging_source_revision':revision,
        'correction_rebuild_receipt_sha256':sha256(raw),'font_native_receipt_sha256':FONT_RESULT_SHA,
        'font_native_test_rom_sha256':FONT_SHA,'font_test_resources_retained':True,
        'transition_before_receipt_sha256':BEFORE_RESULT_SHA,'transition_after_receipt_sha256':AFTER_RESULT_SHA,
        'required_ram_bytes':0x800000,'expansion_pak_required':True,'ordinary_heap_end':0x80400000,
        'save_layout_changed':False,'save_type':'FlashRAM 128 KiB','rtc_required':True,
        'original_hardware_verified':False,'human_playthrough_complete':False,
        'ordinary_save_restart_verified':False,'full_regression_passed':False,
        'controlled_font_and_transition_checks_complete':True,
        'corrected_findings':[f'V1-{i:02}' for i in range(1,19)],'v2_keyboard_redesign_included':False}
    if apply_bundle(native,patch,manifest)!=image:raise ValueError('RC3 patch reconstruction failed')
    members={'animal-forest-english.ups':patch,
        'manifest.json':(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC3_PLAYTEST.md').read_bytes(),
        'SOURCES.md':(ROOT/'docs/SOURCES.md').read_bytes(),'LICENSE-tooling.txt':(ROOT/'LICENSE').read_bytes(),
        'apply_translation.py':(ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py':(ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS']=''.join(f'{sha256(data)}  {name}\n' for name,data in sorted(members.items())).encode()
    return archive_bytes(members),manifest,image

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/v1rc3-rebuild-01')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc3');a=p.parse_args()
    output=a.output.resolve()
    if a.output.is_symlink() or output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('RC3 output must be a fresh local build directory')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    package,manifest,image=prepare(a.build,a.native.read_bytes(),revision,
        (ROOT/'build/font-edges-native-02/results.json').read_bytes(),
        (ROOT/'build/transition-native-before-02/results.json').read_bytes(),
        (ROOT/'build/transition-native-after-02/results.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='af-v1rc3-patch-') as temp:
        directory=Path(temp);archive=directory/'patch.zip';write_new(archive,package)
        with zipfile.ZipFile(archive) as bundle:bundle.extractall(directory/'bundle')
        result=subprocess.run(['python3',str(directory/'bundle/apply_translation.py'),
            '--rom',str(a.native.resolve()),'--output',str(directory/'verified.z64')],
            check=True,capture_output=True,text=True,timeout=60)
        if sha256((directory/'verified.z64').read_bytes())!=FINAL_SHA:
            raise ValueError('Standalone RC3 patcher output differs')
        verification={'standalone_patcher_passed':True,'output_sha256':json.loads(result.stdout)['sha256'],
            'archive_sha256':sha256(package),'original_hardware_verified':False}
    output.mkdir()
    for name,data in {ROM_NAME:image,'V1RC3-patch.zip':package,
        'manifest.json':(json.dumps(manifest,indent=2)+'\n').encode(),
        'verification.json':(json.dumps(verification,indent=2)+'\n').encode(),
        'README.md':(ROOT/'docs/V1RC3_PLAYTEST.md').read_bytes()}.items():write_new(output/name,data)
    print(json.dumps({'rom':str(output/ROM_NAME),'patch_archive':str(output/'V1RC3-patch.zip'),
        'manifest':manifest,'verification':verification},indent=2))

if __name__=='__main__':main()
