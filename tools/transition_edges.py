"""Cover the framebuffer edges with the native building-transition mesh."""
import argparse
import json
import math
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,make_ups,sha256,verified_rom
from apply_translation import write_new
from title_start_fix import reconstruct

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='ee6f792083c6e4a434fdb8dc440cbe667bc5fd1c497b24e03a983b7eb06dc65f'
SCALE=0x80116D24-CODE_RAM
OLD=struct.pack('>f',0.019)
NEW=struct.pack('>f',0.0195)
KEEP=0xA22000

def projected_bounds(value):
    # guScale/guMtxF2L truncate to 16.16; include this quantisation.
    scale=int(value*65536)/65536
    radius_y=12000*scale/(400*math.tan(math.pi/6))*120
    radius_x=16000*scale/(400*math.tan(math.pi/6)*(4/3))*160
    return [160-radius_x,120-radius_y,160+radius_x,120+radius_y]

def build(native,base):
    verified_rom(native)
    if sha256(base)!=BASE_SHA: raise ValueError('Transition fix requires the checked font-edge candidate')
    files=by_vrom(base);code=files[CODE_VROM].extract(base);keep=files[KEEP].extract(base)
    original=by_vrom(native)[CODE_VROM].extract(native)
    if (code[0x80083C00-CODE_RAM:0x80084058-CODE_RAM]!=original[0x80083C00-CODE_RAM:0x80084058-CODE_RAM]
        or keep[0x4300:0x54F8]!=by_vrom(native)[KEEP].extract(native)[0x4300:0x54F8]
        or code[SCALE:SCALE+4]!=OLD
        or code[0x80083F0C-CODE_RAM:0x80083F10-CODE_RAM]!=bytes.fromhex('C4206D24')):
        raise ValueError('Native transition code, models, or scale binding changed')
    changed=bytearray(code);changed[SCALE:SCALE+4]=NEW
    image=reconstruct(native,base,{CODE_VROM:bytes(changed)})
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image: raise ValueError('Transition patch reconstruction failed')
    return image,patch,{'version':1,'baseline_sha256':BASE_SHA,'source_sha256':sha256(native),
        'output_sha256':sha256(image),'patch_sha256':sha256(patch),
        'sources':{'tools/transition_edges.py':sha256(Path(__file__).read_bytes())},
        'code_sha256':sha256(changed),'keep_sha256':sha256(keep),
        'scale_ram':'80116D24','old_scale':0.019,'new_scale':0.0195,
        'old_projected_bounds':projected_bounds(0.019),'new_projected_bounds':projected_bounds(0.0195),
        'changed_resource':f'{CODE_VROM:08X}','changed_range_bytes':4,
        'transition_timing_changed':False,'allocation_changed':False,'save_format_changed':False,
        'fixed_issues':['V1-18'],'required_ram_bytes':0x800000,'hardware_retest':'pending'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/v1-font-edges-03/animal-forest-font-edges.z64')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),a.base.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    for name,data in {'animal-forest-edge-fixes.z64':image,'animal-forest-edge-fixes.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        write_new(a.output/name,data)
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
