#!/usr/bin/env python3
"""Bind installed sale/Redd publication to complete native-item English outputs."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256
from event_actor import NEW_VROM,NEW_RELOCATION,verify_installation
from extended_items import COUNTS,HEADER,WIDTH
from item_aliases import ordinary_item
from leaflet_date_scenario import reference_fields
from leaflet_letters import fields,verify_templates
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from runtime_module import verify_test_module


def scenario(native,rom,build,creator):
    module,report = build['runtime_module'],build['event_actor']['overlay']
    verify_test_module(rom,module);verify_installation(rom,native,report,module,creator)
    files = by_vrom(rom);catalog = files[0x03000000].extract(rom)
    verify_templates(native,catalog)
    names = files[0x02A00000].extract(rom)
    if names[:32]!=HEADER or len(names)!=32+sum(COUNTS)*WIDTH: raise ValueError('Changed item resource')
    def name(item):
        item = ordinary_item(item)
        group,index = (16,item&4095) if item>>12==1 else (item>>8,item&255)
        number = [*range(0x20,0x30),16].index(group)
        if index>=COUNTS[number]: raise ValueError('Item fixture exceeds native group')
        at = 32+(sum(COUNTS[:number])+index)*WIDTH
        return names[at:at+WIDTH]
    items = (0x1000,0x2000,0x2200)
    words,cases = reference_fields(),[]
    for template in (*range(2,18),49,50,51):
        sale = template<49
        for count in (range(1,min(3,1+(template-2)//4)+1) if sale else (0,)):
            for capital in (0,1):
                hour = (0,11,12,23)[len(cases)%4];month = 1+len(cases)%12;day = 21
                source = bytearray(range(156))
                for at in (0,12): source[at:at+8] = bytes((0,0,hour,day,0,month,7,208))
                for i,item in enumerate(items): struct.pack_into('>H',source,28+i*2,item)
                slot = 17 if sale else 0
                values = {slot:Field(words['months'][month-1].encode().ljust(9,b' ')),
                          slot+1:Field(words['days'][day-1].encode().ljust(4,b' ')),
                          slot+2:Field(f'{hour%12 or 12} {words["ampm"][hour>=12]}'.encode())}
                if sale:
                    values[0] = Field(str(count).encode())
                    for i,item in enumerate(items[:count]): values[7+i] = Field(name(item))
                record = Record(2,0,(template,),tuple((i,values[i]) for i in sorted(fields(template))),bool(capital))
                mail = bytearray(164);mail[:12] = mail[18:30] = b' '*12
                mail[12:16] = mail[30:34] = b'\xff'*4;mail[16] = mail[34] = 255
                mail[38:42] = bytes((0,128,2 if sale else 3,55 if sale else 54));mail[42:] = pack(record)
                choice = (template-2)*3+count-1 if sale else 48+template-49
                cases.append({'template':template,'count':count,'capital':capital,'flag':2+choice*2+capital,
                              'source':source.hex(),'mail':mail.hex(),
                              'text':output_bytes(record,templates(catalog,record)).hex()})
    at = 0x1060+0x800262D0-0x80025C60;loader = native[at:at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request = {'module':module,'report':report,'loader':loader.hex(),'cases':cases,
               'data':files[NEW_VROM].extract(rom).hex(),'relocation':files[NEW_RELOCATION].extract(rom).hex(),
               'metadata':build['event_actor']['metadata']}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_event_actor':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/event-actor-pilot'))
    parser.add_argument('--creator',type=Path,default=Path('build/event-actor/creator-original.bin'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()),args.creator.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_event_cases':len(actions[3]['test_event_actor']['cases'])}))


if __name__=='__main__': main()
