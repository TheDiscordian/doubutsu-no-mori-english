"""One bounded gyroid-response probe, without transactions or persistent writes."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256
from birthday_draw_scenario import CALLBACK
from gyroid_service import ROOT,PARENT,NEW_VROM,NEW_RELOC,verify_shared_parts
from submenu_text_scenario import LOADER_SHA

ROM_SHA='0173bb83decfda63b299fb40aedd22121b546818081754032e60fc3b96d9a257'


def scenario(native,built,report):
    if sha256(built)!=ROM_SHA or report['output_sha256']!=ROM_SHA:
        raise ValueError('Changed gyroid service test cartridge')
    verify_shared_parts(built,native,report['gyroid_service']);files=by_vrom(built)
    if files[PARENT].extract(built)[0x218:0x248]!=CALLBACK:raise ValueError('Changed native matrix callback')
    at=0x1060+0x800262D0-0x80025C60;loader=native[at:at+0xF0]
    if sha256(loader)!=LOADER_SHA:raise ValueError('Changed native overlay loader')
    request={'owner':files[NEW_VROM].extract(built).hex(),'relocation':files[NEW_RELOC].extract(built).hex(),
        'loader':loader.hex(),'matrix_callback':CALLBACK.hex(),'rom_sha256':ROM_SHA}
    return [{'wait':8},{'read':['80000318',4],'expect':'00400000'},
        {'save_state':True},{'pause_game_thread':True},{'test_gyroid_service':request},
        {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/gyroid-service-01')
    p.add_argument('--output',type=Path,default=ROOT/'build/gyroid-service-scenario.json');a=p.parse_args()
    actions=scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (a.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((a.build/'build.json').read_text()))
    with a.output.open('x') as target:target.write(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'output':str(a.output),'actions':len(actions),'transactions':False}))


if __name__=='__main__':main()
