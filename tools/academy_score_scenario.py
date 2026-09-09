#!/usr/bin/env python3
"""Bind complete HRA score mail tests to native selection and cartridge bytes."""

import argparse
import json
from pathlib import Path
import struct

from academy_letters import SCHEDULER,verify_installation as verify_advice
from academy_score_letters import RAM,VROM,RELOCATION,COMPLETE,fields,references,verify_installation
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from extended_items import COUNTS,HEADER,WIDTH
from item_aliases import ordinary_item
from mail_record import Field,Record
from runtime_module import verify_test_module


def selected_template(request,case,seed):
    next_seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
    draw = struct.unpack('>f',struct.pack('>I',(next_seed>>9)|0x3F800000))[0]-1
    row = int(struct.unpack('>f',struct.pack('>f',draw*3))[0])
    bits = int(case['bits'],16)
    for i in range(row*16+15,row*16-1,-1):
        number = request['selection_table'][i]
        if bits>>i&1 and number!=-1: return number
    points,room = case['points'],case['room']
    if points <= 0: return 0x42
    if points < 20000: return 0x43 if room==0 else 0x44 if room==1 else 0x45
    return 0x46 if points<70000 else 0x47 if points<100000 else 0x48


def expected_record(request,number,points,series,month,day,capital,item=0x11FC):
    months = ('January','February','March','April','May','June','July','August','September','October','November','December')
    suffix = 'th' if 11<=day<=13 else {1:'st',2:'nd',3:'rd'}.get(day%10,'th')
    values = {0:Field(f'{points:,}'.rjust(10).encode()),3:Field(b'2000'),
              4:Field(months[month-1].encode().ljust(9)),5:Field(f'{day}{suffix}'.encode().ljust(4))}
    if number == 0x37:
        item = ordinary_item(item)
        group,index = (16,item&4095) if item>>12==1 else (item>>8,item&255)
        i = [*range(0x20,0x30),16].index(group)
        if index >= COUNTS[i]: raise ValueError('Invalid selected score item')
        at = 32+(sum(COUNTS[:i])+index)*WIDTH
        values[1] = Field(bytes.fromhex(request['items'])[at:at+WIDTH])
    if number in (0x3A,0x3B): values[2] = Field(bytes.fromhex(request['series'][series]['english']))
    if set(values) != fields('mail',number): raise ValueError('Score fixture field set differs from source')
    return Record(2,0,(number,),tuple(sorted(values.items())),bool(capital))


def scenario(native,built,report):
    if sha256(built) != report['output_sha256']: raise ValueError('Changed score ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_advice(built,native,module,report['academy_letters'])
    verify_installation(built,native,module,report['academy_score_letters'])
    source,files = by_vrom(native),by_vrom(built)
    catalog = files[0x03000000].extract(built);evidence = references(native,catalog)
    items = files[0x02A00000].extract(built)
    if items[:32] != HEADER or sha256(items) != report['extended_items']['data_sha256']:
        raise ValueError('Changed installed item names')
    seeds = {}
    for seed in range(4096):
        next_seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
        draw = struct.unpack('>f',struct.pack('>I',(next_seed>>9)|0x3F800000))[0]-1
        choice = int(struct.unpack('>f',struct.pack('>f',draw*3))[0]);seeds.setdefault(choice,seed)
    if set(seeds) != {0,1,2}: raise ValueError('Incomplete native RNG choices')
    cases = []
    for number in COMPLETE:
        points,room,bits,seed = 123456,0,0,0
        if number < 0x42:
            index = evidence['native_selection_table'].index(number);bits = 1<<index;seed = seeds[index//16]
        else:
            points,room = {0x42:(0,0),0x43:(5000,0),0x44:(5000,1),0x45:(5000,2),
                           0x46:(20000,0),0x47:(70000,0),0x48:(100000,0)}[number]
        cases.append({'template':number,'points':points,'room':room,'bits':f'{bits:016X}','seed':seed})
    original,code = source[CODE_VROM].extract(native),files[CODE_VROM].extract(built);guards = {}
    for start,end in ((0x800262D0,0x800263C0),(0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54),
                      (0x8002C970,0x8002CA58)):
        at = 0x1060+start-0x80025C60;value = native[at:at+end-start]
        if built[at:at+end-start] != value: raise ValueError('Changed native loader/cache/RNG helper')
        guards[f'{start:08X}'] = value.hex()
    for start,end in ((0x8009CA94,0x8009CC00),(0x800BEBEC,0x800BEC8C),(0x800D3740,0x800D3864)):
        value = original[start-CODE_RAM:end-CODE_RAM]
        if code[start-CODE_RAM:end-CODE_RAM] != value: raise ValueError('Changed native eligibility/allocation helper')
        guards[f'{start:08X}'] = value.hex()
    request = {'module':module,'cases':cases,'series':evidence['series'],'items':items.hex(),'catalog':catalog.hex(),
               'selection_table':evidence['native_selection_table'],
               'data':files[VROM].extract(built).hex(),'relocation':files[RELOCATION].extract(built).hex(),
               'original':source[VROM].extract(native).hex(),'original_relocation':source[RELOCATION].extract(native).hex(),
               'scheduler':code[SCHEDULER-CODE_RAM:0x8009CFB0-CODE_RAM].hex(),'guards':guards}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_academy_scores':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/academy-score-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--scheduler-only',action='store_true',help='Run the focused original scoring/scheduler portion')
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    if args.scheduler_only: actions[3]['test_academy_scores']['scheduler_only'] = True
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_score_templates':0 if args.scheduler_only else len(actions[3]['test_academy_scores']['cases']),
                      'scheduler_only':args.scheduler_only}))


if __name__ == '__main__': main()
