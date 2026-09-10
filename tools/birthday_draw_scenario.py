"""One silent native birthday-drawing batch with complete checkpoint restoration."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256
from birthday_screen import ROOT,OWNER,RELOC,ASSET,compiled,replacements,profile
from hboard_overlay import OWNER as SUBMENU_OWNER

CALLBACK=bytes.fromhex('8C820298004018253C0EDA383C0F801125EFFCD035CE0003'
    'AC6E0000AC6F000424420008AC82029803E0000800000000')


def scenario(native,built,report):
    draw,hashes=compiled(ROOT/'build/birthday-draw-03');expected=replacements(native,draw)
    files=by_vrom(built)
    if (sha256(built)!=report['output_sha256'] or report['birthday_screen']!=profile(expected,hashes)
            or any(files[v].extract(built)!=data for v,data in expected.items())
            or files[SUBMENU_OWNER].extract(built)[0x218:0x248]!=CALLBACK):
        raise ValueError('Changed installed birthday or native matrix callback')
    at=0x1060+0x800262D0-0x80025C60;loader=native[at:at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request={'images':{f'{v:08X}':files[v].extract(built).hex() for v in (OWNER,RELOC,ASSET)},
        'loader':loader.hex(),'matrix_callback':CALLBACK.hex()}
    return [{'wait':8},{'read':['80000318',4],'expect':'00400000'},
        {'save_state':True},{'pause_game_thread':True},{'test_birthday_draw':request},
        {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/birthday-screen-01')
    p.add_argument('--output',type=Path,default=ROOT/'build/birthday-draw-scenario.json')
    a=p.parse_args()
    actions=scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((a.build/'build.json').read_text()))
    with a.output.open('x') as f:f.write(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'output':str(a.output),'draws':3,'save_io':False}))


if __name__=='__main__':main()
