#!/usr/bin/env python3
"""Bind actual cartridge resident-word callers and their complete message cases."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom,CODE_RAM,CODE_VROM
from birthday_smoke import RNG_START,RNG_END,RNG_SHA256
from fortune_strings import STRING_RELOCATION
from npc_mail_show import source
from resident_words import SPEC,IDS,permits,patch,verify_values
from resident_word_smoke import prepared_tokens
from runtime_module import module_command_info,verify_test_module
from textbanks import Bank
from textcodec import encode,tokenize


def scenario(rom,native,report,edits):
    native=verified_rom(native);module=report['runtime_module'];dates=bool(report.get('dialogue_dates'))
    verify_test_module(rom,module);info=module_command_info(native);permits(native,edits,info)
    original,reloc=source(native,'ordinary');files=by_vrom(rom)
    actual,actual_reloc=files[SPEC.vrom].extract(rom),files[SPEC.relocation].extract(rom)
    if (actual,actual_reloc)!=patch(original,reloc,module=module,dates=dates):
        raise ValueError('Resident-word test requires the complete installed caller patch')
    entries=Bank('string',STRING_RELOCATION[0],0xD18000,files[STRING_RELOCATION[0]].extract(rom),
                 files[0xD18000].extract(rom)).entries()
    verify_values([entries[int(id[7:],16)] for id in IDS],info)
    if report.get('shared_npc_words'):
        from shared_npc_words import IDS as SHARED_IDS, validated_values, verify_values as verify_shared_values
        validated_values(native,edits,info)
        verify_shared_values([entries[int(id[7:],16)] for id in SHARED_IDS])
    by_id={e['id']:e for e in edits}
    for index,value in enumerate(entries):
        id=f'string:{index:04X}'
        if id in by_id and value!=encode(by_id[id]['translation'],info):raise ValueError('Changed installed string candidate')
    main=Bank('message',0x2000000,0xCF9000,files[0x2000000].extract(rom),files[0xCF9000].extract(rom)).entries()
    messages={str(group):{} for group in (1,2,3)}
    for id,edit in by_id.items():
        if not id.startswith('message:'):continue
        value=encode(edit['translation'],info,extended_glyphs=True)
        if main[int(id[8:],16)]!=value:raise ValueError('Changed complete installed resident message')
        requests={t.data for t in tokenize(value,info) if t.kind=='cmd' and t.data[1]==0x0C}
        for group in (1,2,3):
            if bytes((0x7F,0x0C,9,0,group)) not in requests:continue
            if any(t.data[1]-0x31 >= (3 if group==3 else 5) for t in prepared_tokens(value,info,group)):
                raise ValueError('Resident message refers to an unprepared field: '+id)
            messages[str(group)][id[8:]]=value.hex()
    if any(not rows for rows in messages.values()):raise ValueError('Missing resident preparation message group')
    loader_at=0x1060+0x800262D0-0x80025C60;loader=native[loader_at:loader_at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed original overlay loader')
    rng_at=0x1060+RNG_START-0x80025C60;rng=native[rng_at:rng_at+RNG_END-RNG_START]
    if sha256(rng)!=RNG_SHA256 or rom[rng_at:rng_at+len(rng)]!=rng:raise ValueError('Changed native RNG')
    code=files[CODE_VROM].extract(rom)
    if (sha256(code[0x800C165C-CODE_RAM:0x800C1674-CODE_RAM])!='1d362ccdaa6698214736ec69ec9ce9732dd4231dd670b5ec3e4fd85cf2390e26'
            or struct.unpack_from('>I',code,0x80107CB8-CODE_RAM+0x37*4)[0]!=0x800A15C8
            or sha256(code[0x800A15C8-CODE_RAM:0x800A15FC-CODE_RAM])!='d5d71c273c32e5c9de9d67dd4c1dc16c3858a54e4b438280ad7e2e3cccb99751'):
        raise ValueError('Changed native shop-level bits or free-string 11 command')
    request={'source':original.hex(),'relocation':reloc.hex(),'installed_relocation':actual_reloc.hex(),
             'module':module,'dates':dates,'loader':loader.hex(),'rng':rng.hex(),
             'strings':[value.hex() for value in entries],'messages':messages,'info':info}
    if report.get('shared_npc_words'):request['shared_npc_words']=True
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_resident_words':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    p.add_argument('--module',type=Path,required=True,help='Complete configured build.json')
    p.add_argument('--translations',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    actions=scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()),
                     json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'random_words':288 if actions[3]['test_resident_words'].get('shared_npc_words') else 128,'message_cases':{
        k:len(v) for k,v in actions[3]['test_resident_words']['messages'].items()},'output':str(args.output)}))


if __name__=='__main__':main()
