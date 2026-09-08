#!/usr/bin/env python3
"""Bind complete English shop units and original actors before a silent batch."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256,verified_rom
from runtime_module import module_command_info,verify_test_module
from shop_units import SHOPS,FIRST,END,STRING_RELOCATION,permits,verify_values,verify_callers
from textbanks import Bank
from textcodec import encode,tokenize


def scenario(rom,native,module,edits):
    module=module.get('runtime_module',module)
    native=verified_rom(native);verify_test_module(rom,module);info=module_command_info(native)
    permits(native,edits,info);verify_callers(rom)
    files=by_vrom(rom);entries=Bank('string',STRING_RELOCATION[0],0xD18000,
        files[STRING_RELOCATION[0]].extract(rom),files[0xD18000].extract(rom)).entries()
    verify_values(entries[FIRST:END],info)
    actors={name:{'data':files[spec.vrom].extract(rom).hex(),
                  'reloc':files[spec.relocation].extract(rom).hex()} for name,spec in SHOPS.items()}
    main=Bank('message',0x2000000,0xCF9000,files[0x2000000].extract(rom),files[0xCF9000].extract(rom)).entries()
    by_id={e['id']:e for e in edits};messages={}
    for index in (0x108A,0x173D):
        value=encode(by_id[f'message:{index:04X}']['translation'],info)
        codes=[t.data[1] for t in tokenize(value,info) if t.kind=='cmd']
        if main[index]!=value or codes.count(0x2B)!=1 or 0x2C in codes:
            raise ValueError('Shop message no longer retains complete English count-only wording')
        messages[f'{index:04X}']=value.hex()
    at=0x1060+0x800262D0-0x80025C60;loader=native[at:at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request={'actors':actors,'units':[v.hex() for v in entries[FIRST:END]],
             'messages':messages,'loader':loader.hex(),'info':info}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_shop_units':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    p.add_argument('--module',type=Path,required=True,help='Configured build.json or its runtime_module report')
    p.add_argument('--translations',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    actions=scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()),
                     json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'actors':5,'units':120,'output':str(args.output)}))


if __name__=='__main__':main()
