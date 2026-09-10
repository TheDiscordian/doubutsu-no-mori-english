"""Bounded native menu-text batch; no Controller Pak operations or save writes."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256
from birthday_draw_scenario import CALLBACK
from submenu_text import ROOT,PARENT,verify_shared_parts
import editor_confirmation as confirmation
import embedded_warnings as warning

ROM_SHA='9f12c83314b048225e87c0c4ba46853caf3dadb21f863a234ca03a879987474d'
LOADER_SHA='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
ASSETS=(0xACA000,0xB17000)


def scenario(native,built,report):
    if sha256(built)!=ROM_SHA or report['output_sha256']!=ROM_SHA:
        raise ValueError('Changed embedded menu native test cartridge')
    verify_shared_parts(built,native,report['submenu_text'],report['editor_confirmation'])
    files=by_vrom(built)
    if files[PARENT].extract(built)[0x218:0x248]!=CALLBACK:
        raise ValueError('Changed native menu matrix callback')
    at=0x1060+0x800262D0-0x80025C60;loader=native[at:at+0xF0]
    if sha256(loader)!=LOADER_SHA:raise ValueError('Changed native menu loader')
    addresses=[confirmation.VROM,confirmation.RELOC,*ASSETS]
    addresses.extend(v for owner in warning.OWNERS for v in (owner.new_vrom,owner.new_relocation))
    request={'images':{f'{v:08X}':files[v].extract(built).hex() for v in addresses},
        'loader':loader.hex(),'matrix_callback':CALLBACK.hex(),'rom_sha256':ROM_SHA}
    return [{'wait':8},{'read':['80000318',4],'expect':'00400000'},
        {'save_state':True},{'pause_game_thread':True},{'test_submenu_text':request},
        {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/submenu-text-01')
    p.add_argument('--output',type=Path,default=ROOT/'build/submenu-text-scenario.json')
    a=p.parse_args()
    actions=scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((a.build/'build.json').read_text()))
    with a.output.open('x') as target:target.write(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'output':str(a.output),'save_io':False,'pak_operations':False}))


if __name__=='__main__':main()
