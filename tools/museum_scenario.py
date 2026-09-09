#!/usr/bin/env python3
"""Bind complete museum delivery cases to the installed translation cartridge."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from mail_catalog import templates
from mail_record import Record,pack
from mail_runtime_test_scenario import output_bytes
from museum_letters import START,END,GUARDS,FOSSILS,NAME,TABLE,verify_installation,verify_templates
from runtime_module import verify_test_module
import mail_creator_catalog as creator_catalog


def case(catalog,number,gift,capital):
    if capital not in (0,1): raise ValueError('Invalid museum test capital')
    if number in (0xBD,0xBE):
        if gift: raise ValueError('Museum notices have no gift')
    elif not 0x1E3C<=gift<0x1EA0 or number!=FOSSILS[(gift-0x1E3C)//4]:
        raise ValueError('Invalid museum fossil and template pair')
    record = Record(creator_catalog.identity(catalog),0,(number,),(),bool(capital))
    return {'template':number,'gift':gift,'capital':capital,'wire':pack(record).hex(),
            'text':output_bytes(record,templates(catalog,record)).hex()}


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed museum ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['museum_letters'])
    files = by_vrom(built);catalog = files[creator_catalog.vrom(creator_catalog.selected(module))].extract(built)
    verify_templates(native,catalog)
    pairs = [(0xBD,0),(0xBE,0)]+[(number,0x1E3C+index*4+index%4) for index,number in enumerate(FOSSILS)]
    cases = [case(catalog,number,gift,capital) for number,gift in pairs for capital in (0,1)]
    original = by_vrom(native)[CODE_VROM].extract(native);code = files[CODE_VROM].extract(built)
    guards = {f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex() for a,b,_ in GUARDS}
    guards.update({f'{a:08X}':code[a-CODE_RAM:a-CODE_RAM+size].hex() for a,size in ((NAME,6),(TABLE,100))})
    request = {'module':module,'catalog':catalog.hex(),'cases':cases,'guards':guards,
               'original_creator':original[START-CODE_RAM:END-CODE_RAM].hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_museum_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/museum-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--boot-output',type=Path)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    if args.boot_output:
        from mail_glyph_creator_scenario import without_captures
        root = Path(__file__).resolve().parents[1]
        boot = without_captures(json.loads((root/'tests/runtime-choice-scenario.json').read_text()))
        args.boot_output.parent.mkdir(parents=True,exist_ok=True);args.boot_output.write_text(json.dumps(boot,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_museum_cases':len(actions[3]['test_museum_letters']['cases'])}))


if __name__=='__main__': main()
