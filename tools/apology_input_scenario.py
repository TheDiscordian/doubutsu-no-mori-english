#!/usr/bin/env python3
"""One bounded native input/key drawing/Done/matcher check, without screenshots."""
import argparse
import json
from pathlib import Path
from aflib import by_vrom,sha256
from apology_overlay import verify_installation
import hboard_overlay as editor
import resetti_replies as actor


def scenario(native,built,report):
    verify_installation(built,native,report)
    files=by_vrom(built)
    request={'module':report['runtime_module'],'overlay':report['apology_input']['overlay'],
             'images':{f'{v:08X}':files[v].extract(built).hex() for v in
                (editor.NEW_VROM,editor.NEW_RELOCATION,editor.OWNER,editor.OWNER_RELOC,actor.VROM,actor.RELOC_VROM)}}
    at=0x1060+0x800262D0-0x80025C60
    loader=native[at:at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request['loader']=loader.hex()
    return [{'wait':8},{'read':['80000318',4],'expect':'00400000'},
            {'save_state':True},{'pause_game_thread':True},{'test_apology_input':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=Path('build/apology-input-pilot'))
    p.add_argument('--output',type=Path,default=Path('build/apology-input-scenario.json'))
    a=p.parse_args()
    actions=scenario(Path('local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((a.build/'build.json').read_text()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'output':str(a.output)}))


if __name__=='__main__':main()
