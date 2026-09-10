"""Package an approved combined title/grid cartridge for private playtesting."""
import argparse
import json
from pathlib import Path
import subprocess

from aflib import ROM_SHA256,sha256,verified_rom
from apply_translation import apply_bundle,write_new
from package_v0 import archive_bytes

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='da66a789341307c625da130ae11e20609b9a023fca82712f303fc59fe95deb94'
PATCH_SHA='6b423b37fc767c73d3490a2c2e5182509ccdf66c52cba4c663a5ac2d3065edbb'
REPORT_SHA='dea15128dbb5969ce2ad485acc5573ce210dea666b1a0cce7f0bde0c30ff9d1a'
CARTRIDGE_REVISION='a5e9eebbf3e36e736e6d806f5288623769b5b0bf'
LABEL='v1-artwork-playtest-01'


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
        raise ValueError('Package requires the approved complete title/gyroid/menu candidate')
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
    p.add_argument('--build',type=Path,default=ROOT/'build/title-gyroid-service-combined-01')
    p.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/releases'/f'{LABEL}.zip');a=p.parse_args()
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    package,manifest=prepare(a.build,a.rom.read_bytes(),revision)
    a.output.parent.mkdir(parents=True,exist_ok=True);write_new(a.output,package)
    print(json.dumps({'package':str(a.output),'sha256':sha256(package),'manifest':manifest},indent=2))


if __name__=='__main__':main()
