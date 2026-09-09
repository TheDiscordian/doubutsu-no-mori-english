#!/usr/bin/env python3
"""Complete shop notice cases bound to the installed ROM and original owners."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from audit_shop_notice_letters import audit,RARE_TABLE,REOPENING_TABLE
from extended_items import COUNTS,WIDTH
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from runtime_module import verify_test_module
from shop_notice_letters import START,END,GUARDS,TEMPLATES,verify_installation
import mail_creator_catalog as creator_catalog


def case(catalog,items,number,item,capital):
    if number not in TEMPLATES or capital not in (0,1): raise ValueError('Invalid shop notice case')
    fields = ()
    if number>=0x1B:
        if item: raise ValueError('Reopening notice must not attach an item')
    elif not item: raise ValueError('Spotlight notice requires the original selected item')
    if 0x14<=number<=0x17:
        group,index = (16,item&4095) if item>>12==1 else (item>>8,item&255)
        groups = [*range(0x20,0x30),16]
        if group not in groups or index>=COUNTS[groups.index(group)]: raise ValueError('Invalid shop notice item')
        at = 32+(sum(COUNTS[:groups.index(group)])+index)*WIDTH
        fields = ((7,Field(items[at:at+WIDTH])),)
    record = Record(creator_catalog.identity(catalog),0,(number,),fields,bool(capital))
    return {'template':number,'item':item,'capital':capital,'wire':pack(record).hex(),
            'text':output_bytes(record,templates(catalog,record)).hex()}


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed shop notice ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['shop_notices'])
    files = by_vrom(built);catalog = files[creator_catalog.vrom(creator_catalog.selected(module))].extract(built)
    audit(native,catalog);items = files[0x02A00000].extract(built)
    cases = [{**case(catalog,items,RARE_TABLE[shop*2+kind],0x11FC,capital),
              'shop':shop,'kind':kind,'mode':mode}
             for shop in range(4) for kind in range(2) for mode in range(2) for capital in range(2)]
    reopening = [{**case(catalog,items,number,0,capital),'shop':shop}
                 for shop,number in enumerate(REOPENING_TABLE) for capital in range(2)]
    original = by_vrom(native)[CODE_VROM].extract(native);code = files[CODE_VROM].extract(built)
    intervals = [(a,b) for a,b,_ in GUARDS]+[(0x8010DC3C,0x8010DC6C),
                 (0x800C164C,0x800C1764),(0x8007D318,0x8007D36C)]
    request = {'module':module,'cases':cases,'reopening':reopening,
               'original':original[START-CODE_RAM:END-CODE_RAM].hex(),
               'guards':{f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex() for a,b in intervals}}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_shop_notices':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/shop-notice-letters-pilot'))
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
    print(json.dumps({'spotlight_cases':32,'reopening_cases':8,'full_readbacks':64}))


if __name__=='__main__': main()
