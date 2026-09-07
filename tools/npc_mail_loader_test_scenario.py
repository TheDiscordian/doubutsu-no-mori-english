#!/usr/bin/env python3
"""Verify cartridge-loaded NPC creators against original native metadata."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,verified_rom
from mail_catalog import VROM as CATALOG_VROM,verify_registered
from npc_mail_capture import call_patches
from npc_mail_delivery import START,END,patch as gate
from npc_mail_loader import VROM
from runtime_module import verify_test_module
from textbanks import banks


def scenario(rom,native,module):
    native = verified_rom(native);verify_test_module(rom,module)
    if 'npc_mail_loader' not in module: raise ValueError('Cartridge loader test requires installed generation')
    files = by_vrom(rom)
    code,original = files[CODE_VROM].extract(rom),by_vrom(native)[CODE_VROM].extract(native)
    expected = bytearray(original)
    hooks = call_patches(original,module)
    for at,before,after in hooks: expected[at-CODE_RAM:at-CODE_RAM+4] = after
    expected[START-CODE_RAM:END-CODE_RAM] = gate(original[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16))
    guards = {}
    for start,end in ((0x800A8B10,0x800A9364),(0x800A7D70,0x800A80E8),(0x800ACD18,0x800ACD80),
                      (0x800950D8,0x800950E8),(0x8009BFC0,0x8009C11C),(0x8009C344,0x8009C3D0)):
        value = code[start-CODE_RAM:end-CODE_RAM]
        if value != expected[start-CODE_RAM:end-CODE_RAM]: raise ValueError('Changed installed cartridge creator helper')
        guards[f'{start:08X}'] = value.hex()
    for start,end in ((0x8002B9C0,0x8002BC00),(0x8002C970,0x8002CA58),
                      (0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54)):
        at,size = 0x1060+start-0x80025C60,end-start
        value = native[at:at+size]
        if rom[at:at+size] != value: raise ValueError('Changed boot relocation/cache/RNG helper')
        guards[f'{start:08X}'] = value.hex()
    catalog = files[CATALOG_VROM].extract(rom);verify_registered(catalog)
    sources = {b.name:b for b in banks(native) if b.name in ('string','npc_names')}
    for b in sources.values():
        b.data = files[b.data_vrom].extract(rom)[b.data_offset:b.data_offset+len(b.data)]
        if b.table_vrom is not None:
            b.table = files[b.table_vrom].extract(rom)[b.table_offset:b.table_offset+len(b.table)]
    request = {'module':module,'catalog':catalog.hex(),'blob':files[VROM].extract(rom).hex(),'guards':guards,
               'hooks':[(at,before.hex(),after.hex()) for at,before,after in hooks],
               'native_words':[entry.hex() for entry in sources['string'].entries()],
               'native_names':[entry.hex() for entry in sources['npc_names'].entries()]}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_npc_mail_loader':request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,required=True,help='Configured ROM build runtime-module.json, not the plain compiler report')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'original_comparisons':48,'cartridge_loading':True}))


if __name__ == '__main__': main()
