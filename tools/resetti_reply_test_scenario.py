#!/usr/bin/env python3
"""Verify the complete cartridge reply dictionary before isolated actor calls."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom,sha256,verified_rom
from resetti_replies import VROM,RELOC_VROM,FIRST,END,STRING_RELOCATION,permits,patch,verify_values
from runtime_module import module_command_info,verify_test_module
from textbanks import Bank
from textcodec import encode


def scenario(rom,native,module,edits):
    native=verified_rom(native);verify_test_module(rom,module);info=module_command_info(native)
    permits(native,edits,info)
    sources,files=by_vrom(native),by_vrom(rom)
    data,reloc=sources[VROM].extract(native),sources[RELOC_VROM].extract(native)
    if files[VROM].extract(rom)!=patch(data,reloc)or files[RELOC_VROM].extract(rom)!=reloc:
        raise ValueError('Resetti test requires the complete patched cartridge actor')
    entries=Bank('string',STRING_RELOCATION[0],0xD18000,
                 files[STRING_RELOCATION[0]].extract(rom),files[0xD18000].extract(rom)).entries()
    verify_values(entries[FIRST:END],info)
    by_id={e['id']:e for e in edits};good={}
    for index in range(0x484,0x494):
        if index in (0x48E,0x491):continue
        if entries[index]!=encode(by_id[f'string:{index:04X}']['translation'],info):
            raise ValueError('Complete installed English apology target differs')
        good[f'{index:04X}']=entries[index].hex()
    at=0x1060+0x800262D0-0x80025C60;loader=native[at:at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Unexpected native overlay loader')
    request={'source':data.hex(),'relocation':reloc.hex(),'loader':loader.hex(),
             'values':[value.hex()for value in entries[FIRST:END]],'good_targets':good}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_resetti_replies':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--translations',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    actions=scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()),
                     json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'dictionary_words':32,'good_targets':14,'output':str(args.output)}))


if __name__=='__main__':main()
