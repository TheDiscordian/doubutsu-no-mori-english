#!/usr/bin/env python3
"""Bind the installed Miko actor and complete expected native fortune letters."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from fortune_actor import NEW_VROM,NEW_RELOCATION,metadata,verify_installation
from fortune_slips import CATALOG_VROM
from mail_catalog import templates
from mail_record import Field,Record,pack
from mail_runtime_test_scenario import output_bytes
from runtime_module import verify_test_module


def choice_for_seed(seed):
    values = []
    states = []
    for limit in (4,16,16,16,16,3):
        seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
        single = struct.unpack('>f',struct.pack('>I',(seed>>9)|0x3F800000))[0]-1.0
        value = struct.unpack('>f',struct.pack('>f',single*limit))[0]
        values.append(int(value));states.append(seed)
    return bytes((*values[1:5],values[0],values[5],0,0)),states


def scenario(rom,native,build):
    native = verified_rom(native)
    module,report = build['runtime_module'],build['fortune_actor']['overlay']
    verify_test_module(rom,module)
    verify_installation(rom,native,report,module)
    files = by_vrom(rom)
    data,reloc = files[NEW_VROM].extract(rom),files[NEW_RELOCATION].extract(rom)
    at = report['symbols']['af_fortune_words'];words = data[at:at+1088]
    catalog = files[CATALOG_VROM].extract(rom)
    cases,seen = [],set()
    for seed in range(0xF1357900,0xF1357900+100000):
        choice,states = choice_for_seed(seed)
        for capital in (0,1):
            key = (choice[4],choice[5],capital)
            if key in seen: continue
            seen.add(key)
            rows = [slot*16+choice[slot] for slot in range(4)]+[64+choice[4]]
            record = Record(3,0,(0x72+choice[5],),tuple((slot,Field(words[row*16:(row+1)*16]))
                            for slot,row in enumerate(rows)),bool(capital))
            cases.append({'seed':seed,'rng_states':states,'choice':choice.hex(),'capital':capital,
                          'wire':pack(record).hex(),'text':output_bytes(record,templates(catalog,record)).hex()})
        if len(seen) == 24: break
    if len(seen) != 24: raise ValueError('Incomplete fortune outcome/template/capital cases')
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = native[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    # The direct order-table checks use these original get/set instructions.
    original_code = by_vrom(native)[CODE_VROM].extract(native)
    code = files[CODE_VROM].extract(rom)
    guards = {}
    for start,end in ((0x8007B44C,0x8007B4E8),(0x8009C0C0,0x8009C108),
                      (0x8009C384,0x8009C6A0)):
        value = original_code[start-CODE_RAM:end-CODE_RAM]
        if code[start-CODE_RAM:end-CODE_RAM] != value:
            raise ValueError('Changed native fortune metadata, demo, or heap helper')
        guards[f'{start:08X}'] = value.hex()
    request = {'data':data.hex(),'relocation':reloc.hex(),'report':report,'module':module,
               'metadata':metadata(len(data)).hex(),'loader':loader.hex(),'guards':guards,'cases':cases}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_fortune_actor':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    p.add_argument('--build-report',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.build_report.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_outcome_template_capital_cases':24}))


if __name__ == '__main__': main()
