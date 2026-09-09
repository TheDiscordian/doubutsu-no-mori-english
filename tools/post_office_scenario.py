#!/usr/bin/env python3
"""Bind complete postal delivery cases to the actual translated cartridge."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from extended_items import COUNTS,WIDTH
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from post_office_letters import START,END,GUARDS,TEMPLATES,verify_installation,verify_templates
from runtime_module import verify_test_module
import mail_creator_catalog as creator_catalog

MONTHS = ('January','February','March','April','May','June','July','August','September','October','November','December')


def case(catalog,items,number,gift,capital):
    if number not in TEMPLATES or capital not in (0,1): raise ValueError('Invalid postal test template or capital')
    if number == 0x57:
        if not 0x2C00 <= gift <= 0x2C5C or gift&7 >= 5: raise ValueError('Invalid postal test ticket')
        fields = ((4,Field(MONTHS[(gift-0x2C00)//8].encode().ljust(9))),)
    else:
        group,index = (16,gift&4095) if gift>>12==1 else (gift>>8,gift&255)
        groups = [*range(0x20,0x30),16]
        if group not in groups or index>=COUNTS[groups.index(group)]: raise ValueError('Invalid postal test item')
        at = 32+(sum(COUNTS[:groups.index(group)])+index)*WIDTH
        fields = ((0,Field(items[at:at+WIDTH])),)
    record = Record(creator_catalog.identity(catalog),0,(number,),fields,bool(capital))
    return {'template':number,'gift':gift,'capital':capital,'wire':pack(record).hex(),
            'text':output_bytes(record,templates(catalog,record)).hex()}


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed postal ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['post_office_letters'])
    files = by_vrom(built);catalog = files[creator_catalog.vrom(creator_catalog.selected(module))].extract(built)
    verify_templates(native,catalog);items = files[0x02A00000].extract(built)
    cases = [case(catalog,items,n,0x11FC,c) for n in range(0x49,0x4D) for c in (0,1)]
    cases += [case(catalog,items,0x57,0x2C00+(month-1)*8+count-1,(month+count)%2)
              for month in range(1,13) for count in range(1,6)]
    original = by_vrom(native)[CODE_VROM].extract(native);code = files[CODE_VROM].extract(built)
    request = {'module':module,'catalog':catalog.hex(),'items':items.hex(),'cases':cases,
               'original_creator':original[START-CODE_RAM:END-CODE_RAM].hex(),
               'guards':{f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex() for a,b,_ in GUARDS}}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_post_office_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/post-office-letters-pilot'))
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
    print(json.dumps({'actions':len(actions),'complete_postal_cases':len(actions[3]['test_post_office_letters']['cases'])}))


if __name__=='__main__': main()
