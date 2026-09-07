#!/usr/bin/env python3
"""Build an isolated NPC creation-failure gate test with real native receipt."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,verified_rom
from audit_mail_templates import template_fields
from mail_catalog import VROM,templates,verify_registered
from mail_record import Record,Field,pack
from mail_npc import POST_CALL,POST_SHIM
from npc_mail_delivery import START,END,patch
from npc_mail_generation import native_evidence
from runtime_module import MODULE_RAM,MODULE_VROM,verify_test_module


def scenario(rom,native,module):
    native = verified_rom(native)
    verify_test_module(rom,module)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    original = by_vrom(native)[CODE_VROM].extract(native)
    expected = bytearray(original)
    post_target = int(module['symbols']['af_mail_post_send'],16)
    resident = by_vrom(rom)[MODULE_VROM].extract(rom)
    if resident[post_target-MODULE_RAM:post_target-MODULE_RAM+len(POST_SHIM)] != POST_SHIM:
        raise ValueError('Unexpected installed NPC send-result shim')
    struct.pack_into('>I',expected,POST_CALL-CODE_RAM,0x0C000000|((post_target>>2)&0x03FFFFFF))
    native_evidence(code)
    function = code[START-CODE_RAM:END-CODE_RAM]
    patch(function,0x80200000)
    # These actual receipt/identity/copy routines remain native, not mocked.
    ranges = ((START,END),(0x800B67C0,0x800B6B94),(0x8009C1C0,0x8009C89C),
              (0x800B77D0,0x800B7A94),(0x80094E38,0x80094EB0))
    guards = {}
    for start,end in ranges:
        value = code[start-CODE_RAM:end-CODE_RAM]
        if value != expected[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError(f'NPC delivery fixture requires unchanged native receipt helpers: {start:08X}..{end:08X}')
        guards[f'{start:08X}'] = value.hex()
    catalog = by_vrom(rom)[VROM].extract(rom)
    verify_registered(catalog)
    letters = []
    for kind,selected in ((0,(0,)),(1,(32,)*5)):
        record = Record(2,kind,selected,())
        fields = set().union(*(template_fields(part) for part in templates(catalog,record).parts))
        record = Record(2,kind,selected,tuple((i,Field(b'captured')) for i in sorted(fields)))
        letters.append(pack(record).hex())
    request = {'function':function.hex(),'guards':guards,'letters':letters}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},
            {'test_npc_mail_delivery':request},{'load_state':True},{'resume':True},{'wait':2}]


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
    print(json.dumps({'actions':len(actions),'record_kinds':2,'production_hook_installed':False}))


if __name__ == '__main__': main()
