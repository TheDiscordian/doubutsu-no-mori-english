#!/usr/bin/env python3
"""Bind a complete Snowman creation/receipt batch to the installed cartridge."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from snowman_actor import NEW_VROM,NEW_RELOCATION,native_sources,metadata,verify_installation
from snowman_snapshots import snapshots
from mail_npc import POST_CALL,POST_SHIM
from runtime_layout import MODULE_RAM,MODULE_VROM


def choice_for_seed(seed):
    seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
    fraction = struct.unpack('>f',struct.pack('>I',(seed>>9)|0x3F800000))[0]-1.0
    return int(struct.unpack('>f',struct.pack('>f',fraction*12))[0]),seed


def scenario(native,built,report,group='all'):
    if group not in ('all','edges'): raise ValueError('Unknown Snowman native group')
    if sha256(built)!=report['output_sha256']: raise ValueError('Changed Snowman ROM')
    module = report['runtime_module'];verify_installation(built,native,module,report['snowman_actor'])
    files = by_vrom(built);original,original_reloc = native_sources(native)
    _,prepared = snapshots(native,files[0x030A0000].extract(built),files[0x02A00000].extract(built))
    seeds = {}
    for seed in range(10000):
        choice,end = choice_for_seed(seed);seeds.setdefault(choice,(seed,end))
        if len(seeds)==12: break
    if len(seeds)!=12: raise ValueError('Incomplete Snowman RNG choices')
    cases = [{**c,'seed':seeds[c['choice']][0],'rng_end':seeds[c['choice']][1]} for c in prepared['cases']]
    loader_at = 0x1060+0x800262D0-0x80025C60;loader = native[loader_at:loader_at+0xF0]
    if (sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
            or built[loader_at:loader_at+0xF0]!=loader): raise ValueError('Changed native overlay loader')
    a,b = bytearray(by_vrom(native)[CODE_VROM].extract(native)),files[CODE_VROM].extract(built)
    # The existing NPC result hook occupies a different recipient branch of
    # the shared receipt function. Require exactly that approved hook, not an
    # arbitrary difference hidden by excluding the whole receipt routine.
    target = int(module['symbols']['af_mail_post_send'],16)
    if files[MODULE_VROM].extract(built)[target-MODULE_RAM:target-MODULE_RAM+24]!=POST_SHIM:
        raise ValueError('Changed shared NPC receipt shim')
    struct.pack_into('>I',a,POST_CALL-CODE_RAM,0x0C000000|((target&0x0FFFFFFF)>>2))
    guards = {}
    for start,end in ((0x8009519C,0x800951E4),(0x8009BFC0,0x8009C108),
                      (0x8009C384,0x8009C6A0),(0x800B67C0,0x800B6AC8)):
        value = a[start-CODE_RAM:end-CODE_RAM]
        if value!=b[start-CODE_RAM:end-CODE_RAM]: raise ValueError('Changed Snowman native ownership helper')
        guards[f'{start:08X}'] = value.hex()
    request = {'module':module,'report':report['snowman_actor']['overlay'],'cases':cases,'guards':guards,'group':group,
               'data':files[NEW_VROM].extract(built).hex(),'relocation':files[NEW_RELOCATION].extract(built).hex(),
               'original':original.hex(),'original_relocation':original_reloc.hex(),
               'loader':loader.hex(),'metadata':metadata(len(files[NEW_VROM].extract(built))).hex()}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_snowman_letters':request},
            {'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--build',type=Path,default=Path('build/snowman-letters-pilot'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--boot-output',type=Path)
    parser.add_argument('--group',choices=('all','edges'),default='all')
    args = parser.parse_args()
    actions = scenario(args.native_rom.read_bytes(),(args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()),args.group)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(actions,indent=2)+'\n')
    if args.boot_output:
        from mail_glyph_creator_scenario import without_captures
        root = Path(__file__).resolve().parents[1]
        boot = without_captures(json.loads((root/'tests/runtime-choice-scenario.json').read_text()))
        args.boot_output.parent.mkdir(parents=True,exist_ok=True);args.boot_output.write_text(json.dumps(boot,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'complete_snowman_cases':24 if args.group=='all' else 0,'owner_cases':5}))


if __name__=='__main__': main()
