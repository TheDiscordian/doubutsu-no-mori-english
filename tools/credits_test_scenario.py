#!/usr/bin/env python3
"""Bind the installed complete native credits for a silent restored batch."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
import credits_strings as c
from fortune_strings import STRING_RELOCATION
from runtime_module import module_command_info,verify_test_module
from textbanks import Bank


def scenario(rom,native,report,edits):
    native=verified_rom(native);verify_test_module(rom,report['runtime_module'])
    info=module_command_info(native);c.permits(native,edits,info)
    files=by_vrom(rom);originals=by_vrom(native)
    data,reloc=(originals[v].extract(native) for v in (c.VROM,c.RELOCATION))
    if c.patch(data,reloc)!=tuple(files[v].extract(rom) for v in (c.VROM,c.RELOCATION)):
        raise ValueError('Credits fixture requires the exact installed caller and BSS patch')
    code=files[CODE_VROM].extract(rom)
    expected=bytearray(c.METADATA_BYTES);struct.pack_into('>I',expected,12,c.RAM+c.RESIDENT_BYTES)
    if code[c.METADATA-CODE_RAM:c.METADATA-CODE_RAM+32]!=expected:
        raise ValueError('Credits fixture requires updated native ownership metadata')
    values=Bank('string',STRING_RELOCATION[0],0xD18000,files[STRING_RELOCATION[0]].extract(rom),
                files[0xD18000].extract(rom)).entries()[c.FIRST:c.END]
    c.verify_values(values,info)
    loader_at=0x1060+0x800262D0-0x80025C60;loader=native[loader_at:loader_at+0xF0]
    if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    request={'source':data.hex(),'relocation':reloc.hex(),'loader':loader.hex(),
             'rows':[v.hex() for v in values],'metadata':expected.hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_credits':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


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
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'pages':16,'rows':110,'output':str(args.output)}))


if __name__=='__main__':main()
