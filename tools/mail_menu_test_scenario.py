#!/usr/bin/env python3
"""Generate source-guarded original letter-menu tests for a fresh emulator."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from mail_menu import source,definitions,cases,relocated
from runtime_module import verify_test_module


def scenario(rom,native,module):
    native = verified_rom(native)
    verify_test_module(rom,module)
    data,reloc = source(rom)
    definitions(data)
    for base in (0x801A0000,0x802F8010): relocated(data,reloc,base)
    loader = native[0x800262D0-0x80025C60+0x1060:0x800263C0-0x80025C60+0x1060]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Unexpected original native loader')
    code,original = by_vrom(rom)[CODE_VROM].extract(rom),by_vrom(native)[CODE_VROM].extract(native)
    guards = {}
    for start,end in ((0x8009C1C0,0x8009C284),(0x8009C414,0x8009C438),(0x8009C89C,0x8009C8C0)):
        value = code[start-CODE_RAM:end-CODE_RAM]
        if value != original[start-CODE_RAM:end-CODE_RAM]: raise ValueError('Native menu helper changed')
        guards[f'{start:08X}'] = value.hex()
    request = {'data':data.hex(),'relocation':reloc.hex(),'loader':loader.hex(),'cases':cases(),'guards':guards}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_mail_menu':request},{'load_state':True},{'resume':True},{'wait':2}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'menu_cases':len(cases()),'static_definitions':44}))


if __name__ == '__main__': main()
