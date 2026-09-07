#!/usr/bin/env python3
"""Create isolated Pelly handler checks for the identical-ROM town checkpoint."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from mail_npc_test_scenario import scenario as npc_scenario
from mail_runtime_test_scenario import reference_fixtures
from mail_storage import PELLY_VROM
from mail_record import unpack
from pelly_receipt import TABLE_VROM, MESSAGES, COUNT, RELOC_VROM
from pelly_receipt_smoke import relocated_pelly
from textbanks import Bank


def index_actions(module):
    return [{'call':{'address':module['symbols']['af_pelly_refusal_index'],
                     'arguments':[0,0,0,reason],'expect_return_v1':2 if reason == 4 else reason+1}}
            for reason in (0,1,2,3,4,5,6,127,254,255)]


def scenario(rom,native,module,grading,fixtures):
    native = verified_rom(native)
    npc = npc_scenario(rom,module,grading,fixtures)[3]['test_npc_mail_sends']
    files = by_vrom(rom)
    overlay,reloc = files[PELLY_VROM].extract(rom),files[RELOC_VROM].extract(rom)
    for base in (0x801A0000,0x802F8010): relocated_pelly(overlay,reloc,base)
    messages = Bank('message',0x02000000,TABLE_VROM,
                    files[0x02000000].extract(rom),files[TABLE_VROM].extract(rom)).entries()
    if len(messages) != COUNT+2 or messages[-2:] != list(MESSAGES):
        raise ValueError('Pelly scenario requires the complete English error appendix')
    selected = []
    kinds = set()
    for case in npc['cases']:
        data = bytes.fromhex(case['mail'])
        if not any(case.get(key) for key in ('reject','visitor','quest','post_office')):
            kind = unpack(data[0x2A:],expected_catalog=2).kind
            if kind not in kinds:
                kinds.add(kind);selected.append(case)
    if len(selected) != 2: raise ValueError('Pelly witnesses require classic and composite letters')
    for case in tuple(selected):
        data = bytearray.fromhex(case['mail']);data[-1]^=1
        selected.append({'label':'rejected:'+case['label'],'mail':data.hex(),'reject':True})
    def boot(start,end): return native[start-0x80025C60+0x1060:end-0x80025C60+0x1060]
    loader = boot(0x800262D0,0x800263C0)
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Unexpected native overlay loader')
    request = {'overlay':overlay.hex(),'relocation':reloc.hex(),'loader':loader.hex(),
               'context':npc['context'],'guards':npc['guards'],'cases':selected,
               'messages':{f'{i:04X}':messages[i].hex() for base in (0x8B9,0x8E1,0x8B5,0x1BD7,0x2DDA,0x2DDC,0x2DDE,0x2DE8)
                           for i in (base,base+1)}}
    code = files[CODE_VROM].extract(rom)
    for start,end in ((0x8009C67C,0x8009C6F4),(0x8009E388,0x8009E6B8)):
        request['guards'][f'{start:08X}'] = code[start-CODE_RAM:end-CODE_RAM].hex()
    return ([{'wait':2},{'save_state':True},{'pause_game_thread':True},{'test_pelly_receipt':request}]
            +index_actions(module)+[{'load_state':True},{'resume':True},{'wait':2}])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--overlay',type=Path,default=Path('build/mail-grading/overlay.json'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--index-only',action='store_true',help='Run only the ten native refusal-index boundaries')
    args = parser.parse_args()
    native,rom = args.native_rom.read_bytes(),args.rom.read_bytes()
    fixtures = reference_fixtures(native,args.gc_data,args.decomp,args.rel)
    actions = scenario(rom,native,json.loads(args.module.read_text()),json.loads(args.overlay.read_text()),fixtures)
    if args.index_only: actions.pop(3)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'rom_sha256':sha256(rom),'actions':len(actions),'cases':0 if args.index_only else 48,
                      'selectors':0 if args.index_only else 16,'index_cases':10}))


if __name__ == '__main__': main()
