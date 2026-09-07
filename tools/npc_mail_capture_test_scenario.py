#!/usr/bin/env python3
"""Build isolated real-creator capture tests; no production hooks or save I/O."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,verified_rom
from mail_catalog import VROM,verify_registered
from npc_mail_capture import call_patches,validate
from runtime_module import verify_test_module
from textbanks import banks


def scenario(rom,native,module,data,reloc,report):
    native = verified_rom(native)
    verify_test_module(rom,module)
    validate(data,reloc,report,module)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    original = by_vrom(native)[CODE_VROM].extract(native)
    hooks = call_patches(code,module)
    guards = {}
    for start,end in ((0x800A8B10,0x800A9110),(0x800A7D70,0x800A80E8),
                      (0x800ACD18,0x800ACD80),(0x800950D8,0x800950E8)):
        value = code[start-CODE_RAM:end-CODE_RAM]
        if value != original[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed native NPC capture helper')
        guards[f'{start:08X}'] = value.hex()
    # The boot section is outside the compressed main code segment.
    for start,end in ((0x8002B9C0,0x8002BC00),(0x8002C970,0x8002CA58),
                      (0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54)):
        at,size = 0x1060+start-0x80025C60,end-start
        value = native[at:at+size]
        if rom[at:at+size] != value: raise ValueError('Changed native relocation/RNG helper')
        guards[f'{start:08X}'] = value.hex()
    catalog = by_vrom(rom)[VROM].extract(rom)
    verify_registered(catalog)
    # The pilot relocates dialogue banks, so the retail all-bank enumerator
    # cannot enumerate it. Resolve only these unchanged-layout source banks.
    files = by_vrom(rom)
    bank = {b.name:b for b in banks(native) if b.name in ('string','npc_names')}
    for b in bank.values():
        b.data = files[b.data_vrom].extract(rom)[b.data_offset:b.data_offset+len(b.data)]
        if b.table_vrom is not None:
            b.table = files[b.table_vrom].extract(rom)[b.table_offset:b.table_offset+len(b.table)]
    request = {'module':module,'code':data.hex(),'relocations':reloc.hex(),'report':report,
               'catalog':catalog.hex(),'guards':guards,
               'hooks':[(at,before.hex(),after.hex()) for at,before,after in hooks],
               'native_words':[entry.hex() for entry in bank['string'].entries()],
               'native_names':[entry.hex() for entry in bank['npc_names'].entries()]}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_npc_mail_capture':request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--overlay',type=Path,default=Path('build/npc-mail-capture'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()),
                       (args.overlay/'overlay.bin').read_bytes(),(args.overlay/'relocation.bin').read_bytes(),
                       json.loads((args.overlay/'overlay.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'creator_contexts':48,'production_hooks_installed':False}))


if __name__ == '__main__': main()
