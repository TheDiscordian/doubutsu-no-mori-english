"""Rebuild all seven human-playtest correction stages after the artwork baseline."""
import argparse
import json
from pathlib import Path
import subprocess
import time

from aflib import sha256, verified_rom
from apply_translation import write_new
from package_v1_playtest import ROM_SHA as BASE_SHA, REPORT_SHA
from rebuild_v1 import checked_output, source_inventory, source_state
from toolchain import profile_sha256
import title_start_fix
import editor_pixel_fix
import hud_label_fix
import notice_tune_fix
import inventory_money_fix
import letter_ui_fix
import keyboard_background_fix

ROOT = Path(__file__).resolve().parents[1]
FINAL_SHA = '63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37'
PATCH_SHA = 'b0316888443f92bc2a56aa3eeec8f49a8278bf834bb8e495278ac1d2bff975bb'


def rebuild(native, base, title_report, translation_report, rel, symbols, output):
    verified_rom(native)
    if sha256(base) != BASE_SHA or title_report.get('output_sha256') != BASE_SHA or profile_sha256(title_report) != REPORT_SHA:
        raise ValueError('Fix recipe needs the checked final artwork/title baseline')
    if translation_report.get('output_sha256') != title_report['baseline_sha256']:
        raise ValueError('Runtime report is not the translation underlying this title')
    module = translation_report['runtime_module']
    output = checked_output(output); before = source_inventory()
    revision = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    output.mkdir(parents=True,exist_ok=False)
    report = {'version':1,'kind':'combined_v1_playtest_corrections','source_revision':revision,**source_state(),
        'recipe_sha256':sha256(Path(__file__).read_bytes()),'source_sha256':sha256(native),
        'baseline_sha256':BASE_SHA,'baseline_profile_sha256':REPORT_SHA,
        'translation_report_sha256':sha256(json.dumps(translation_report,sort_keys=True,separators=(',',':')).encode()),
        'source_rel_sha256':sha256(rel),'source_symbols_sha256':sha256(symbols),'sources':before,
        'stages':[],'required_ram_bytes':0x800000,'ordinary_heap_end':0x80400000,
        'save_format_changed':False,'native_tests_run':False,'hardware_verified':False,
        'scope':'Seven correction stages; the reproducible artwork/title baseline is an explicit input'}
    write_new(output/'inputs.json',(json.dumps(report,indent=2)+'\n').encode())
    image = base
    stages = (
        ('press-start',lambda image,out:title_start_fix.build(native,image,rel,symbols)),
        ('editor-pixels',lambda image,out:editor_pixel_fix.build(native,image,out,module=module)),
        ('hud',lambda image,out:hud_label_fix.build(native,image,rel,symbols,
            hud_label_fix.compile_commands(out/'commands',hud_label_fix.SOURCE,(('cash',56),)))),
        ('notice-tune',lambda image,out:notice_tune_fix.build(native,image,rel,symbols)),
        ('inventory-money',lambda image,out:inventory_money_fix.build(native,image)),
        ('letter-ui',lambda image,out:letter_ui_fix.build(native,image,rel,symbols,out)),
        ('keyboard-background',lambda image,out:keyboard_background_fix.build(native,image,rel,symbols,out)))
    for name, build in stages:
        started = time.monotonic(); directory = output/name; directory.mkdir()
        image, patch, profile = build(image,directory)
        write_new(directory/'fixes.json',(json.dumps(profile,indent=2)+'\n').encode())
        report['stages'].append({'name':name,'seconds':round(time.monotonic()-started,3),'profile':profile})
        print(f'{name}: {sha256(image)}',flush=True)
    if sha256(image) != FINAL_SHA or sha256(patch) != PATCH_SHA or source_inventory() != before:
        raise ValueError('Complete correction replay changed its approved output or live sources')
    report.update(output_sha256=FINAL_SHA,patch_sha256=PATCH_SHA,rom_bytes=len(image),complete_rebuild=True)
    for name,data in {'animal-forest-title-preview.z64':image,'animal-forest-title-preview.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        write_new(output/name,data)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/title-civic-interior-combined-01')
    p.add_argument('--translation-report',type=Path,default=ROOT/'build/civic-interior-artwork-01/build.json')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--rel',type=Path,default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    p.add_argument('--symbols',type=Path,default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1-fixes-rebuild-01');a=p.parse_args()
    report=rebuild(a.native.read_bytes(),(a.base/'animal-forest-title-preview.z64').read_bytes(),
        json.loads((a.base/'preview.json').read_text()),json.loads(a.translation_report.read_text()),
        a.rel.read_bytes(),a.symbols.read_bytes(),a.output)
    print(json.dumps({'output':str(a.output),'sha256':report['output_sha256'],'stages':len(report['stages'])}))


if __name__=='__main__':main()
