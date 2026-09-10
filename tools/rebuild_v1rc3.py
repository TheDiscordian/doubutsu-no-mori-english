"""Rebuild the font-border and transition-edge corrections from preserved RC2."""
import argparse
import json
from pathlib import Path
import subprocess

from aflib import sha256,verified_rom
from apply_translation import write_new
from rebuild_v1 import checked_output,source_inventory,source_state
import font_polygon_edges
import transition_edges

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA=font_polygon_edges.BASE_SHA
FINAL_SHA='b8a4608b62c098b334dcbe5c87ad2483406c559ba3dbcd2ed26fd64ee27368f0'
PATCH_SHA='27895f1412a60a5cb6ba2388b4db3a85fbd3c82c4167790f7ea0f6202a0f2796'
STAGES=('font-edges','transition-edges')

def rebuild(native,base,output):
    verified_rom(native)
    if sha256(base)!=BASE_SHA:raise ValueError('RC3 requires the preserved V1RC2 cartridge')
    output=checked_output(output);sources=source_inventory();state=source_state()
    if state['worktree_modified']:raise ValueError('Commit cartridge sources before the RC3 replay')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    output.mkdir(parents=True,exist_ok=False)
    report={'version':1,'kind':'v1rc3_followup_rebuild','source_revision':revision,
        'worktree_modified':False,'recipe_sha256':sha256(Path(__file__).read_bytes()),'sources':sources,
        'source_sha256':sha256(native),'baseline_sha256':BASE_SHA,'stages':[],
        'required_ram_bytes':0x800000,'ordinary_heap_end':0x80400000,'save_format_changed':False,
        'hardware_verified':False,'scope':'Two corrections from preserved RC2; freshly compiled font extension'}
    write_new(output/'inputs.json',(json.dumps(report,indent=2)+'\n').encode())
    image=base
    for name in STAGES:
        stage=output/name;stage.mkdir()
        if name=='font-edges': image,patch,profile=font_polygon_edges.build(native,image,stage)
        else:image,patch,profile=transition_edges.build(native,image)
        write_new(stage/'fixes.json',(json.dumps(profile,indent=2)+'\n').encode())
        report['stages'].append({'name':name,'profile':profile})
        print(f'{name}: {sha256(image)}',flush=True)
    if sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or source_inventory()!=sources:
        raise ValueError('RC3 replay or sources differ from checked corrections')
    report.update(output_sha256=FINAL_SHA,patch_sha256=PATCH_SHA,rom_bytes=len(image),complete_rebuild=True)
    for name,data in {'animal-forest-edge-fixes.z64':image,'animal-forest-edge-fixes.ups':patch,
        'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():write_new(output/name,data)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-rom',type=Path,default=ROOT/'build/v1rc2/Animal Forest English V1RC2.z64')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc3-rebuild-01');a=p.parse_args()
    report=rebuild(a.native.read_bytes(),a.base_rom.read_bytes(),a.output)
    print(json.dumps({'output':str(a.output),'sha256':report['output_sha256'],'stages':len(report['stages'])}))

if __name__=='__main__':main()
