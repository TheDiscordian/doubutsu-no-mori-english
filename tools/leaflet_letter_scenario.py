#!/usr/bin/env python3
"""Source-bound full English leaflets in an owned native creation fixture."""

import argparse
from datetime import date,timedelta
import json
from pathlib import Path
import struct

from aflib import by_vrom
from leaflet_letters import TEMPLATES,SALE,RENEWAL,REDD,fields,verify_templates
from leaflet_date_scenario import reference_fields
from mail_catalog import templates
from mail_generate_probe import validate
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from runtime_module import verify_test_module


def scenario(native,rom,module,code,report):
    verify_test_module(rom,module);validate(code,report,module,leaflets=True)
    catalog = by_vrom(rom)[0x03000000].extract(rom)
    evidence = verify_templates(native,catalog);words = reference_fields()
    cases = []
    def add(id,when,hour,capital):
        count = min(3,1+(id-2)//4) if id in SALE else 0
        item_ids = [0x1000+i*4 if i < count else 0 for i in range(3)]
        selected = struct.pack('>HH4B3H',id,when.year,when.month,when.day,hour,count,*item_ids)
        items = b''.join(struct.pack('>H2B',item_ids[i],16,i)+b'synthetic name '+bytes((65+i,)) for i in range(count))
        display = when-timedelta(days=1) if id in RENEWAL else when
        slot = 17 if id in SALE else 0
        values = {slot:Field(words['months'][display.month-1].encode().ljust(9,b' ')),
                  slot+1:Field(words['days'][display.day-1].encode().ljust(4,b' ')),
                  slot+2:Field(str(display.year).encode() if id in RENEWAL else
                              f'{hour%12 or 12} {words["ampm"][int(hour>=12)]}'.encode())}
        if count:
            values[0] = Field(str(count).encode())
            for i in range(count): values[7+i] = Field(items[i*20+4:(i+1)*20],i)
        record = Record(2,0,(id,),tuple((i,values[i]) for i in sorted(fields(id))),bool(capital))
        mail = bytearray(range(164));mail[38:42] = bytes((0,128,3 if id in REDD else 2,54 if id in REDD else 55))
        mail[42:] = pack(record)
        cases.append({'choice':selected.hex(),'items':items.hex(),'capital':capital,
                      'mail':mail.hex(),'text':output_bytes(record,templates(catalog,record)).hex()})
    for id in TEMPLATES:
        for capital in range(2): add(id,date(2000,9,21),12,capital)
    for when in (date(2000,1,1),date(2000,3,1),date(2001,3,1)):
        for id in RENEWAL: add(id,when,0,0)
    for hour in range(24): add(REDD[hour%3],date(2000,12,31),hour,hour%2)
    request = {'code':code.hex(),'probe':report,'module':module,'cases':cases,
               'sources':evidence,'item_fixture':'Synthetic full sixteen-byte names; not native item lookup evidence'}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_leaflet_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--probe',type=Path,default=Path('build/leaflet-letters-probe'))
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    actions = scenario(args.native_rom.read_bytes(),args.rom.read_bytes(),json.loads(args.module.read_text()),
                       (args.probe/'generate.bin').read_bytes(),json.loads((args.probe/'generate.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_leaflets':len(actions[3]['test_leaflet_letters']['cases'])}))


if __name__ == '__main__': main()
