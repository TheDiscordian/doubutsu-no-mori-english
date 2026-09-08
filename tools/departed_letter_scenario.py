#!/usr/bin/env python3
"""Compare native departed-letter choices, full English text, and receipt."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom
from audit_mail_templates import template_fields
from departed_letters import START,POST,END,verify_templates,verify_installation
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from npc_mail_capture import ALIAS_HASH
from npc_mail_names import unpack_aliases
from runtime_module import verify_test_module

PID = b'PLAYER'+b'TOWN  '+bytes.fromhex('12343001')


def expected_record(catalog,number,name,capital):
    fields = (Field(PID[:6]),Field(name),Field(b'AWAY  '),Field(PID[6:12]))
    result = Record(2,0,(number,),tuple(enumerate(fields)),bool(capital))
    needed = set().union(*(template_fields(part) for part in templates(catalog,result).parts))
    return replace(result,fields=tuple((i,v) for i,v in result.fields if i in needed))


def scenario(native,built,report):
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['departed_letters'])
    files = by_vrom(built);catalog = files[0x03000000].extract(built)
    verify_templates(native,catalog)
    code = files[CODE_VROM].extract(built);original = by_vrom(native)[CODE_VROM].extract(native)
    descriptor = module['npc_mail_loader'];data = files[0x03200000].extract(built)
    at = descriptor['overlay']['symbols']['af_npc_alias_data']
    aliases = unpack_aliases(data[at:descriptor['configuration'][2]],ALIAS_HASH)
    names = {row.npc_index:row.name for row in aliases}
    looks = original[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
    seeds = {}
    for seed in range(4096):
        next_seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
        draw = struct.unpack('>f',struct.pack('>I',(next_seed>>9)|0x3F800000))[0]-1.0
        choice = int(struct.unpack('>f',struct.pack('>f',draw*3.0))[0])
        seeds.setdefault(choice,seed)
    if set(seeds) != {0,1,2}: raise ValueError('Incomplete deterministic native RNG fixtures')
    cases = []
    for personality in range(6):
        npc = max((i for i in range(216) if looks[i] == personality),key=lambda i:len(names[i].rstrip()))
        for choice in range(3):
            number = 0xFC+personality*3+choice
            for capital in range(2):
                record = expected_record(catalog,number,names[npc],capital)
                cases.append({'npc':0xE000+npc,'looks':personality,'name':names[npc].hex(),'seed':seeds[choice],
                              'template':number,'capital':capital,'wire':pack(record).hex(),
                              'text':output_bytes(record,templates(catalog,record)).hex()})
    guards = {}
    for start,end in ((0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54),(0x8002C970,0x8002CA58)):
        at = 0x1060+start-0x80025C60
        if built[at:at+end-start] != native[at:at+end-start]: raise ValueError('Changed native cache/RNG helper')
        guards[f'{start:08X}'] = native[at:at+end-start].hex()
    request = {'module':module,'cases':cases,'catalog':catalog.hex(),'guards':guards,
               'original_creator':original[START-CODE_RAM:POST-CODE_RAM].hex(),
               'installed_code':code[START-CODE_RAM:END-CODE_RAM].hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_departed_letters':request},{'load_state':True},{'resume':True},
            {'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/departed-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'departed_comparisons':36,'queue_delivery_templates':18}))


if __name__ == '__main__': main()
