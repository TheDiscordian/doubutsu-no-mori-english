#!/usr/bin/env python3
"""Bind the complete native villager-event batch to original callers and text."""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from audit_mail_templates import template_fields
from extended_items import COUNTS,HEADER,WIDTH
from item_aliases import ordinary_item
from mail_catalog import templates
from mail_record import Field,Record
from npc_mail_capture import ALIAS_HASH
from npc_mail_names import unpack_aliases
from runtime_module import verify_test_module
from villager_event_letters import EVENT,BIRTHDAY,GOODBYE,patches,verify_templates,verify_installation
import mail_creator_catalog as creator_catalog

IDENTITIES = tuple(f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4))


def expected_record(catalog,names,case,player,gift,capital):
    number = case['template'];values = {}
    if number != 0xD7:
        values = {0:Field(IDENTITIES[player][:6]),6 if number in EVENT else 1:Field(bytes.fromhex(case['name']))}
        if number in GOODBYE: values[3] = Field(b'HERE  ')
        if number in (0xEF,0xF1,0xF4,0xFB):
            item = ordinary_item(gift)
            group,index = (16,item&4095) if item>>12 == 1 else (item>>8,item&255)
            number_group = [*range(0x20,0x30),16].index(group)
            if index >= COUNTS[number_group]: raise ValueError('Selected native gift exceeds installed item group')
            at = 32+(sum(COUNTS[:number_group])+index)*WIDTH
            values[2] = Field(names[at:at+WIDTH])
    catalog_id = creator_catalog.identity(catalog)
    result = Record(catalog_id,0,(number,),tuple(sorted(values.items())),bool(capital))
    needed = set().union(*(template_fields(part,extended_glyphs=catalog_id==4) for part in templates(catalog,result).parts))
    return replace(result,fields=tuple((i,v) for i,v in result.fields if i in needed))


def scenario(native,built,report):
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['villager_event_letters'])
    files = by_vrom(built);catalog_id = creator_catalog.selected(module)
    catalog = files[creator_catalog.vrom(catalog_id)].extract(built);evidence = verify_templates(native,catalog)
    names = files[0x02A00000].extract(built)
    if (names[:32] != HEADER or len(names) != 32+sum(COUNTS)*WIDTH
            or sha256(names) != report['extended_items']['data_sha256']): raise ValueError('Changed selected item resource')
    original = by_vrom(native)[CODE_VROM].extract(native)
    creator = module['npc_mail_loader'];blob = files[0x03200000].extract(built)
    at = creator['overlay']['symbols']['af_npc_alias_data']
    aliases = unpack_aliases(blob[at:creator['configuration'][2]],ALIAS_HASH)
    npc_names = {row.npc_index:row.name for row in aliases}
    looks = original[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
    seeds = {}
    for seed in range(4096):
        next_seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
        draw = struct.unpack('>f',struct.pack('>I',(next_seed>>9)|0x3F800000))[0]-1.0
        choice = int(struct.unpack('>f',struct.pack('>f',draw*3.0))[0]);seeds.setdefault(choice,seed)
    if set(seeds) != {0,1,2}: raise ValueError('Incomplete three-choice native RNG fixtures')
    cases = []
    for number in evidence['complete_templates']:
        family = 'event' if number in EVENT else 'birthday' if number in BIRTHDAY else 'goodbye' if number in GOODBYE else 'christmas'
        first = {'event':0x60,'birthday':0xEA,'goodbye':0x20E,'christmas':0xD7}[family]
        personality,choice = divmod(number-first,3)
        npc = max((i for i in range(216) if looks[i] == personality),key=lambda i:len(npc_names[i].rstrip()))
        cases.append({'template':number,'family':family,'looks':personality,'choice':choice,'seed':seeds[choice],
                      'npc':0xE000+npc,'name':npc_names[npc].hex(),
                      'identity':(struct.pack('>HH',0xE000+npc,0x3002)+b'AWAY  '+bytes((13,personality))).hex()})
    originals = {name:{'ram':f'{start:08X}','data':original[start-CODE_RAM:end-CODE_RAM].hex()} for name,start,end in (
        ('common',0x800A93AC,0x800A9468),('event',0x800A94C8,0x800A956C),
        ('birthday',0x800A99B8,0x800A9A98),('goodbye',0x800AC284,0x800AC358),('christmas',0x800A9CD4,0x800A9D68))}
    guards = {}
    for start,end in ((0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54),(0x8002C970,0x8002CA58)):
        at = 0x1060+start-0x80025C60
        if built[at:at+end-start] != native[at:at+end-start]: raise ValueError('Changed original cache/RNG helper')
        guards[f'{start:08X}'] = native[at:at+end-start].hex()
    request = {'module':module,'catalog_id':catalog_id,'cases':cases,'catalog':catalog.hex(),'items':names.hex(),'originals':originals,
               'patches':{f'{at:08X}':value.hex() for at,value in patches(original,int(module['symbols']['af_npc_mail_load'],16)).items()},
               'guards':guards}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_villager_event_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/villager-event-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_event_templates':len(actions[3]['test_villager_event_letters']['cases'])}))


if __name__ == '__main__': main()
