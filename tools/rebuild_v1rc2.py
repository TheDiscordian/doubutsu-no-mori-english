"""Rebuild the three RC1 follow-up stages into the combined V1RC2 candidate."""
import argparse
import json
from pathlib import Path
import subprocess
import time

from aflib import sha256, verified_rom
from apply_translation import write_new
from map_artwork import compile_commands
from rebuild_v1 import checked_output, source_inventory, source_state
import shop_notice_fix
import rc1_text_hud_fix
import keyboard_rc1_fix

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA=shop_notice_fix.BASE_SHA
FINAL_SHA='7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb'
PATCH_SHA='6c334b39eeb92801196e3b7712e2ccf8663daa1d14bb92f8aed5ee7bdd393e43'
STAGES=('hiring-notice','text-hud','keyboard')


def rebuild(native,base,rel,symbols,output):
    verified_rom(native)
    if sha256(base)!=BASE_SHA: raise ValueError('V1RC2 replay requires the preserved complete V1RC1')
    output=checked_output(output); sources=source_inventory(); state=source_state()
    if state['worktree_modified']: raise ValueError('Commit cartridge sources before the RC2 replay')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    output.mkdir(parents=True,exist_ok=False)
    report={'version':1,'kind':'v1rc2_followup_rebuild','source_revision':revision,
        **state,'recipe_sha256':sha256(Path(__file__).read_bytes()),'sources':sources,
        'source_sha256':sha256(native),'baseline_sha256':BASE_SHA,'source_rel_sha256':sha256(rel),
        'source_symbols_sha256':sha256(symbols),'stages':[],'required_ram_bytes':0x800000,
        'ordinary_heap_end':0x80400000,'save_format_changed':False,'hardware_verified':False,
        'scope':'Three follow-up stages from preserved V1RC1 and supplied source games; no retained compiled helpers'}
    write_new(output/'inputs.json',(json.dumps(report,indent=2)+'\n').encode())
    builders=(
        lambda image,out:shop_notice_fix.build(native,image,rel,symbols,
            compile_commands(out/'commands',ROOT/'overlays/fishing/artwork.c',(('remove',8),))['remove']),
        lambda image,out:rc1_text_hud_fix.build(native,image,rel,symbols,
            compile_commands(out/'commands',rc1_text_hud_fix.SOURCE,(('clock',56),))['clock']),
        lambda image,out:keyboard_rc1_fix.build(native,image,rel,symbols,out))
    image=base
    for name,builder in zip(STAGES,builders):
        started=time.monotonic(); out=output/name; out.mkdir()
        image,patch,profile=builder(image,out)
        write_new(out/'fixes.json',(json.dumps(profile,indent=2)+'\n').encode())
        report['stages'].append({'name':name,'seconds':round(time.monotonic()-started,3),'profile':profile})
        print(f'{name}: {sha256(image)}',flush=True)
    if sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or source_inventory()!=sources:
        raise ValueError('RC2 replay differs from checked output or its sources changed')
    report.update(output_sha256=FINAL_SHA,patch_sha256=PATCH_SHA,rom_bytes=len(image),complete_rebuild=True)
    for name,data in {'animal-forest-title-preview.z64':image,'animal-forest-title-preview.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():write_new(output/name,data)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-rom',type=Path,default=ROOT/'build/v1rc1/Animal Forest English V1RC1.z64')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--rel',type=Path,default=ROOT/'build/gamecube/files/foresta.rel.szs.decoded')
    p.add_argument('--symbols',type=Path,default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc2-rebuild-01');a=p.parse_args()
    report=rebuild(a.native.read_bytes(),a.base_rom.read_bytes(),a.rel.read_bytes(),a.symbols.read_bytes(),a.output)
    print(json.dumps({'output':str(a.output),'sha256':report['output_sha256'],'stages':len(report['stages'])}))


if __name__=='__main__':main()
