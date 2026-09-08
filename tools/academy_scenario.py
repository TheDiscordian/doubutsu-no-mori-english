#!/usr/bin/env python3
"""Bind the HRA mailbox and actual scheduler batch to the completed ROM."""

import argparse
import json
from pathlib import Path

from academy_letters import START,END,TEMPLATES,patches,verify_templates,verify_installation
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from runtime_module import verify_test_module


def scenario(native,built,report):
    if sha256(built) != report['output_sha256']: raise ValueError('Changed academy pilot ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['academy_letters'])
    catalog = by_vrom(built)[0x03000000].extract(built);verify_templates(native,catalog)
    original = by_vrom(native)[CODE_VROM].extract(native)
    code = by_vrom(built)[CODE_VROM].extract(built);guards = {}
    for start,end in ((0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54),(0x8002C970,0x8002CA58)):
        at = 0x1060+start-0x80025C60
        if built[at:at+end-start] != native[at:at+end-start]: raise ValueError('Changed original cache/RNG helper')
        guards[f'{start:08X}'] = native[at:at+end-start].hex()
    for start,end in ((0x8007D318,0x8007D36C),(0x8007D650,0x8007D6E0)):
        if original[start-CODE_RAM:end-CODE_RAM] != code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed original employment-eligibility helper')
        guards[f'{start:08X}'] = original[start-CODE_RAM:end-CODE_RAM].hex()
    request = {'module':module,'templates':list(TEMPLATES),'catalog':catalog.hex(),
               'original':original[START-CODE_RAM:END-CODE_RAM].hex(),
               'patches':{f'{at:08X}':v.hex() for at,v in patches(original,int(module['symbols']['af_npc_mail_load'],16)).items()},
               'guards':guards}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_academy_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/academy-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_academy_templates':len(actions[3]['test_academy_letters']['templates'])}))


if __name__ == '__main__': main()
