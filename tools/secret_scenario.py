#!/usr/bin/env python3
"""Bind the secret-letter native batch to the complete installed cartridge."""
import argparse
import json
from pathlib import Path
import struct
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from audit_secret_letters import snapshots
from secret_actor import (ROOT,NEW_VROM,NEW_RELOCATION,OWNER_VROM,OWNER_RELOCATION,
                          verify_installation,native_sources)


def choice_for_seed(seed):
    end = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
    fraction = struct.unpack('>f',struct.pack('>I',(end>>9)|0x3F800000))[0]-1.0
    return int(struct.unpack('>f',struct.pack('>f',fraction*15))[0]),end


def scenario(native,built,report):
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed secret-letter cartridge')
    module = report['runtime_module'];verify_installation(built,native,module,report['secret_actor'])
    files = by_vrom(built);original,original_reloc = native_sources(native)
    _,prepared = snapshots(native,files[0x030A0000].extract(built));seeds = {}
    for seed in range(10000):
        choice,end = choice_for_seed(seed);seeds.setdefault(choice,(seed,end))
        if len(seeds)==15: break
    if len(seeds)!=15: raise ValueError('Incomplete secret RNG selection')
    cases = [{**case,'choice':case['template']-0x22,'seed':seeds[case['template']-0x22][0],
              'rng_first':seeds[case['template']-0x22][1]} for case in prepared['cases']]
    loader_at = 0x1060+0x800262D0-0x80025C60;loader = native[loader_at:loader_at+0xF0]
    if (sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
            or built[loader_at:loader_at+0xF0]!=loader): raise ValueError('Changed native overlay loader')
    code,old_code = files[CODE_VROM].extract(built),by_vrom(native)[CODE_VROM].extract(native);guards = {}
    for lo,hi in ((0x8009BFC0,0x8009C108),(0x8009C384,0x8009C414),
                  (0x800A82C8,0x800A83F0),(0x800A9364,0x800A93AC)):
        if code[lo-CODE_RAM:hi-CODE_RAM]!=old_code[lo-CODE_RAM:hi-CODE_RAM]:
            raise ValueError('Changed secret-letter native helper')
        guards[f'{lo:08X}'] = code[lo-CODE_RAM:hi-CODE_RAM].hex()
    request = {'module':module,'report':report['secret_actor']['overlay'],'cases':cases,'guards':guards,
               'data':files[NEW_VROM].extract(built).hex(),'relocation':files[NEW_RELOCATION].extract(built).hex(),
               'owner':files[OWNER_VROM].extract(built).hex(),'owner_relocation':files[OWNER_RELOCATION].extract(built).hex(),
               'original':original.hex(),'original_relocation':original_reloc.hex(),'loader':loader.hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_secret_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'build/secret-letters-pilot')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--boot-output',type=Path)
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    if args.boot_output:
        from mail_glyph_creator_scenario import without_captures
        args.boot_output.parent.mkdir(parents=True,exist_ok=True)
        args.boot_output.write_text(json.dumps(without_captures(json.loads((ROOT/'tests/runtime-choice-scenario.json').read_text())),indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'secret_letter_cases':30,'owner_loader_bases':2}))


if __name__=='__main__': main()
