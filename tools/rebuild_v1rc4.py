"""Rebuild both RC4 corrections from the preserved exact RC3 cartridge."""
import argparse
import json
from pathlib import Path
import subprocess

from aflib import sha256
from apply_translation import write_new
from font_expansion_memory import ROOT, build
from rebuild_v1 import checked_output, source_inventory, source_state

FINAL_SHA = '5930435f588947df35313ae9cc2ea301af9fc7e68d59a7d8e13a48741d4f3067'
PATCH_SHA = 'f0e7d50f644135ea99cecb11b84056151b07f28500a9b36d2fe07dc1244f16a1'


def rebuild(native, base, output):
    output=checked_output(output)
    if source_state()['worktree_modified']:
        raise ValueError('Commit RC4 cartridge sources before replay')
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    sources=source_inventory()
    output.mkdir(parents=True,exist_ok=False)
    image,patch,report=build(native,base,output)
    if sha256(image)!=FINAL_SHA or sha256(patch)!=PATCH_SHA or source_inventory()!=sources:
        raise ValueError('RC4 cartridge, patch, or sources differ from checked correction')
    report.update(kind='v1rc4_followup_rebuild',source_revision=revision,worktree_modified=False,
                  complete_rebuild=True,recipe_sha256=sha256(Path(__file__).read_bytes()))
    for name,value in {'animal-forest-memory-fix.z64':image,'animal-forest-memory-fix.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        write_new(output/name,value)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/v1rc3/Animal Forest English V1RC3.z64')
    p.add_argument('--native',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    p.add_argument('--output',type=Path,default=ROOT/'build/v1rc4-rebuild-01')
    a=p.parse_args()
    print(json.dumps(rebuild(a.native.read_bytes(),a.base.read_bytes(),a.output),indent=2))


if __name__=='__main__':main()
