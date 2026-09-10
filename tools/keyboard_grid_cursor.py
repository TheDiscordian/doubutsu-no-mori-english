"""Install the source-compiled native cursor ABI correction on the artwork chain."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256
from artwork_chain import rebuild
from keyboard_grid_labels import install,CURSOR_CORRECTED_SHA
from keyboard_grid_overlay import validate,verify_owned_parts,CURSOR_APPROVED

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='7cba9ed279dd90b8fa903cd3ab1745aacf7bd0383c5b43347cadc1bf6fecc39a'
GRID,RELOC=0x3940000,0x3948000


def build(native,base,report,directory):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Cursor correction requires the complete Redd/artwork baseline')
    verify_owned_parts(base,native,report['keyboard_grid'],report['apology_input'])
    raw=(directory/'overlay.bin').read_bytes()
    reloc=(directory/'relocation.bin').read_bytes()
    profile=json.loads((directory/'overlay.json').read_text())
    if profile.get('version')!=2 or sha256(raw)!=CURSOR_APPROVED['overlay_sha256']:
        raise ValueError('Cursor correction requires the reviewed native-command profile')
    validate(native,raw,reloc,profile)
    data=install(raw)
    old=by_vrom(base)[GRID].extract(base)
    if old[:0x5A80]!=data[:0x5A80] or old[0x5FD8:]!=data[0x5FD8:]:
        raise ValueError('Cursor correction changes editor bridges, resources, or state layout')
    image,patch,result=rebuild(native,base,report,{GRID:data,RELOC:reloc})
    result['keyboard_grid']['version']=2
    result['keyboard_grid']['overlay']=profile
    result['keyboard_grid']['status']='Native direction command ABI corrected; focused native confirmation pending'
    result['keyboard_grid_labels']['sha256']=CURSOR_CORRECTED_SHA
    result['keyboard_grid_cursor']={'version':1,'baseline_sha256':BASE_SHA,
        'overlay_sha256':sha256(data),'relocation_sha256':sha256(reloc),
        'native_commands':{'right':1,'left':2,'up':3,'down':4},
        'changed_code_bytes':sum(a!=b for a,b in zip(old,data)),
        'allocation_changed':False,'saved_format_changed':False,
        'status':'Compiled correction; ordinary native input confirmation pending'}
    result['release_status']='Corrected grid cursor with complete artwork/text; native confirmation pending'
    verify_owned_parts(image,native,result['keyboard_grid'],result['apology_input'])
    return image,patch,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/keyboard-grid-cursor-01')
    parser.add_argument('--overlay',type=Path,default=ROOT/'build/keyboard-grid-cursor-aligned')
    args=parser.parse_args();base=ROOT/'build/redd-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),args.overlay)
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
