#!/usr/bin/env python3
"""Source-bound complete fortune-slip creation and old-catalog native probes."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256
from audit_mail_templates import template_fields
from fortune_slips import CATALOG_VROM, WORDS_HASH
from mail_catalog import templates, verify_registered
from mail_generate_probe import validate
from mail_record import Field, Record, pack
from mail_runtime_test_scenario import output_bytes
from runtime_module import verify_test_module


def scenario(rom,module,code,report,words):
    verify_test_module(rom,module)
    validate(code,report,module,fortune_slip=True)
    if len(words) != 1088 or sha256(words) != WORDS_HASH:
        raise ValueError('Native fortune-slip probe requires all complete verified words')
    files = by_vrom(rom)
    catalogs = {2:files[0x03000000].extract(rom),3:files[CATALOG_VROM].extract(rom)}
    for id,data in catalogs.items():
        if verify_registered(data)['catalog'] != id:
            raise ValueError('Native fortune-slip probe catalog address/identity mismatch')
    cases = []
    def add(phrases,outcome,template,capital):
        fields = tuple((slot,Field(words[row*16:(row+1)*16])) for slot,row in
                       enumerate([slot*16+phrases[slot] for slot in range(4)]+[64+outcome]))
        record = Record(3,0,(0x72+template,),fields,bool(capital))
        mail = bytearray(range(164));mail[38:42] = bytes((0,128,5,25));mail[42:] = pack(record)
        cases.append({'choice':bytes((*phrases,outcome,template,0,0)).hex(),'capital':capital,
                      'mail':mail.hex(),'text':output_bytes(record,templates(catalogs[3],record)).hex()})
    for index in range(16): add(tuple((index+slot*3)%16 for slot in range(4)),index%4,index%3,index%2)
    for outcome in range(4):
        for template in range(3):
            for capital in range(2): add((0,5,10,15),outcome,template,capital)
    old_cases = []
    for kind,ids in ((0,(2,)),(1,(0,0,0,0,0))):
        record = Record(2,kind,ids,())
        parts = templates(catalogs[2],record)
        mask = sorted(set().union(*(template_fields(p) for p in parts.parts)))
        for capital in (False,True):
            record = Record(2,kind,ids,tuple((i,Field(b'Retained value  ')) for i in mask),capital)
            old_cases.append({'wire':pack(record).hex(),'text':output_bytes(record,parts).hex()})
    request = {'code':code.hex(),'probe':report,'module':module,'words':words.hex(),
               'cases':cases,'old_cases':old_cases}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_fortune_slip':request},{'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True,help='Configured ROM runtime-module.json')
    p.add_argument('--probe',type=Path,default=Path('build/fortune-slip-probe'))
    p.add_argument('--words',type=Path,default=Path('build/fortune-slip-resources/fortune-words.bin'))
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    actions = scenario(args.rom.read_bytes(),json.loads(args.module.read_text()),
        (args.probe/'generate.bin').read_bytes(),json.loads((args.probe/'generate.json').read_text()),args.words.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_slips':40,'old_catalog_reads':4}))


if __name__ == '__main__': main()
