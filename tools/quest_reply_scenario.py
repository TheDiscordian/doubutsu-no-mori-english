#!/usr/bin/env python3
"""Source-bound complete quest reply creation, home delivery, and readback cases."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from audit_quest_reply_letters import audit,TEMPLATES,ITEM_FIELDS,GUARDS
from extended_items import COUNTS,WIDTH
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from npc_mail_capture import ALIAS_HASH
from npc_mail_names import unpack_aliases
from quest_reply_letters import START,verify_installation
from runtime_module import verify_test_module
import mail_creator_catalog as creator_catalog


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed complete quest reply ROM')
    module = report['runtime_module'];verify_test_module(built,module)
    verify_installation(built,native,module,report['quest_replies'])
    files = by_vrom(built);catalog = files[creator_catalog.vrom(creator_catalog.selected(module))].extract(built)
    audit(native,catalog);items = files[0x02A00000].extract(built)
    creator = module['npc_mail_loader'];offset = creator['overlay']['symbols']['af_npc_alias_data']
    aliases = unpack_aliases(files[0x03200000].extract(built)[offset:offset+6368],ALIAS_HASH)
    names = {r.npc_index:r.name for r in aliases}
    wide = next(i for i in range(216) if len(names[i].rstrip(b' '))==8)
    item = 0x11FC;at = 32+(sum(COUNTS[:-1])+(item&4095))*WIDTH;item_name = items[at:at+WIDTH]
    if len(item_name.rstrip(b' '))<=10: raise ValueError('Quest reply fixture must cover a full wide item')
    cases = []
    for number in TEMPLATES:
        rank,looks = divmod(number-0x75,6)
        for capital in (0,1):
            npc = wide if number in ITEM_FIELDS else (number-0x75)*3+capital
            gift = 0 if rank<3 else item
            fields = ((0,Field(item_name)),) if number in ITEM_FIELDS else ()
            record = Record(creator_catalog.identity(catalog),0,(number,),fields+((6,Field(names[npc])),),bool(capital))
            cases.append({'template':number,'rank':rank,'looks':looks,'capital':capital,'gift':gift,
                          'animal':struct.pack('>HH6sBB',0xE000+npc,0x1234,b'TOWN  ',npc,looks).hex(),
                          'wire':pack(record).hex(),'text':output_bytes(record,templates(catalog,record)).hex()})
    original = by_vrom(native)[CODE_VROM].extract(native);code = files[CODE_VROM].extract(built)
    request = {'module':module,'cases':cases,'original_creator':original[START-CODE_RAM:0x800BB990-CODE_RAM].hex(),
               'guards':{f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex() for a,b,_ in GUARDS}}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_quest_replies':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/quest-reply-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--boot-output',type=Path)
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    if args.boot_output:
        from mail_glyph_creator_scenario import without_captures
        boot = without_captures(json.loads((Path(__file__).resolve().parents[1]/'tests/runtime-choice-scenario.json').read_text()))
        args.boot_output.parent.mkdir(parents=True,exist_ok=True);args.boot_output.write_text(json.dumps(boot,indent=2)+'\n')
    print(json.dumps({'templates':72,'creation_delivery_readback_cases':len(actions[3]['test_quest_replies']['cases'])}))


if __name__=='__main__': main()
