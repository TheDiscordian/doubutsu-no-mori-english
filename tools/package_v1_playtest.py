"""Package an approved combined title/grid cartridge for private playtesting."""
import argparse
import json
from pathlib import Path
import subprocess

from aflib import ROM_SHA256,sha256,verified_rom
from apply_translation import apply_bundle,write_new
from package_v0 import archive_bytes

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19'
PATCH_SHA='600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0'
REPORT_SHA='20f970392d1d60136613ee439b3cc90bcc2abf77941fcf34f42f900b7877a815'
CARTRIDGE_REVISION='8222cb3c23c79813b5f45923a03e2537e1b23c07'
LABEL='v1-artwork-playtest-03'


def prepare(directory,source,revision):
    source=verified_rom(source)
    built=(directory/'animal-forest-title-preview.z64').read_bytes()
    patch=(directory/'animal-forest-title-preview.ups').read_bytes()
    report=json.loads((directory/'preview.json').read_text())
    report_sha=sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode())
    if (sha256(built)!=ROM_SHA or sha256(patch)!=PATCH_SHA or report_sha!=REPORT_SHA
            or report['output_sha256']!=ROM_SHA or report['patch_sha256']!=PATCH_SHA
            or report['memory']['required_ram_bytes']!=0x800000
            or report['memory']['ordinary_heap_end']!=0x80400000 or len(built)!=0x2000000):
        raise ValueError('Package requires the approved title/shared-stall/seasonal-artwork candidate')
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Packaging revision must identify a complete git commit')
    manifest={'format':1,'label':LABEL,'public_release':False,'complete_v1':False,
        'source_revision':'Doubutsu no Mori (Japan), verified retail','source_sha256':ROM_SHA256,
        'output_sha256':ROM_SHA,'output_bytes':len(built),'patch_sha256':PATCH_SHA,
        'cartridge_source_revision':CARTRIDGE_REVISION,'packaging_source_revision':revision,
        'required_ram_bytes':0x800000,'emulator_memory_bytes':0x800000,'expansion_pak_required':True,
        'ordinary_heap_end':0x80400000,'save_layout_changed':False,
        'original_hardware_verified':False,'human_playthrough_complete':False,
        'ordinary_save_restart_verified':False,'embedded_warning_native_drawing_verified':False}
    if apply_bundle(source,patch,manifest)!=built:raise ValueError('Playtest UPS does not reconstruct the approved ROM')
    members={'animal-forest-english.ups':patch,
        'manifest.json':(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode(),
        'README.md':(ROOT/'docs/V1_PATCH_PLAYTEST.md').read_bytes(),
        'FEATURES.md':(ROOT/'docs/V1_TITLE_PLAYTEST.md').read_bytes(),
        'SOURCES.md':(ROOT/'docs/SOURCES.md').read_bytes(),
        'LICENSE-tooling.txt':(ROOT/'LICENSE').read_bytes(),
        'apply_translation.py':(ROOT/'tools/apply_translation.py').read_bytes(),
        'aflib.py':(ROOT/'tools/aflib.py').read_bytes()}
    members['SHA256SUMS']=''.join(f'{sha256(value)}  {name}\n' for name,value in sorted(members.items())).encode()
    return archive_bytes(members),manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/title-stall-combined-01')
    p.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/releases'/f'{LABEL}.zip');a=p.parse_args()
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    package,manifest=prepare(a.build,a.rom.read_bytes(),revision)
    a.output.parent.mkdir(parents=True,exist_ok=True);write_new(a.output,package)
    print(json.dumps({'package':str(a.output),'sha256':sha256(package),'manifest':manifest},indent=2))


if __name__=='__main__':main()
