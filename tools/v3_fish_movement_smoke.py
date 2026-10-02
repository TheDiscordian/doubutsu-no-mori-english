"""Focused actual native freshwater turns and shared ocean mode checks."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import TEST_RETURN
from v3_npc_draw_smoke import boot_proofs
from v3_asset_loader import BLOB


def exercise(debug,rom_path,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256'] or report['composition']['behaviours']['fish-movement']!='GameCube':
        raise ValueError('Fish movement check requires its current GameCube composition')
    files=by_vrom(image);boot=boot_proofs(image)
    fish=report['equipment_resources']['creature_fish'];world=fish['world']
    row=next(r for r in fish['owners'] if r['name']=='river')
    data=files[row['vrom']].extract(image);rel=files[row['reloc']].extract(image);ram=row['ram']
    if sha256(data)!=row['sha256'] or sha256(rel)!=row['reloc_sha256']:
        raise ValueError('Changed checked freshwater owner')
    checks=0
    def check(label,at,want):
        nonlocal checks
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(fish_movement_check=label,address=f'{at:08X}',assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Native fish movement mismatch: '+label)
        checks+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=TEST_RETURN,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def flush(at,n):
        for helper,digest in ((0x8002FE00,'5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'),
                (0x80034CE0,'713e7b78373df6fbf3d030b5237e9c1e2148c9443cbfdf938f2e8ffdf8e2d326')):
            code=debug.read_memory(helper,116)
            if sha256(code)!=digest:raise ValueError('Changed native cache helper')
            call(helper,[at,n],(helper,code))
    size=0x4000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not 0x801A0000<=allocation<=0x80400000-size:
        raise ValueError('Fish movement fixture allocation exceeds native heap')
    root=allocation+16;actor=allocation+0x3000;edge=b'FISH'*4
    debug.write_memory(allocation,edge+bytes(size-32)+edge)
    sections=struct.unpack_from('>5I',rel)
    loaded=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),data,rel,root)
    call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+len(data),root,root+len(data),len(rel)])
    check('complete cartridge freshwater DMA and relocations',root,loaded)
    patch_at=0x80932090-ram
    original=bytes.fromhex('84ef00de84f8022c01f8c8211000001ca4f900de')
    modified=loaded[patch_at:patch_at+20]
    if modified.hex()!='84ef00de84f8022c0018c04001f8c821a4f900de':
        raise ValueError('GameCube freshwater patch missing')
    wrap=lambda n:(n+32768)%65536-32768
    bits=lambda value:int.from_bytes(struct.pack('>f',value),'big')
    speeds={}
    packet=world['packet'];blob=files[BLOB].extract(image)
    source=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    helper=world['compiled']['symbols']['donor'];mode=world['patrol_mode']['ram']
    proof=source[helper-packet['ram']:helper-packet['ram']+36]
    saved_mode=debug.read_memory(mode,4)
    try:
        for gc in (False,True):
            live=bytearray(loaded);live[patch_at:patch_at+20]=modified if gc else original
            debug.write_memory(root+patch_at,live[patch_at:patch_at+20]);flush(root+patch_at,20)
            for phase,heading,increment in ((0.,12000,-12000),(5.,1000,100),(90.,32700,300),
                    (90.,-32700,-300),(175.,1000,100),(180.,-1000,-100)):
                before=bytearray([0xA5]*0x280)
                struct.pack_into('>h',before,0x36,heading);struct.pack_into('>h',before,0xDE,heading)
                struct.pack_into('>f',before,0x224,phase);struct.pack_into('>h',before,0x22C,increment)
                debug.write_memory(actor,bytes(before))
                result=call(root+0x80932024-ram,[actor,bits(180.),bits(5.),bits(1.)],(root,bytes(live[:sections[0]])))
                next_phase=min(180.,phase+5.)
                expected=bytearray(before);struct.pack_into('>f',expected,0x224,next_phase)
                if next_phase>5:heading=wrap(heading+increment*(2 if gc else 1))
                elif next_phase==5:
                    old_heading=struct.unpack_from('>h',before,0x36)[0]
                    increment=int(wrap(increment-old_heading)/36)
                    struct.pack_into('>h',expected,0x22C,increment)
                struct.pack_into('>h',expected,0xDE,heading)
                done=int(next_phase==180.)
                if done:struct.pack_into('>h',expected,0x36,heading)
                if result!=done:raise ValueError('Native freshwater completion changed')
                speed=debug.read_memory(actor+0x74,4);expected[0x74:0x78]=speed
                if gc and speeds[(phase,struct.unpack_from('>h',before,0xDE)[0])]!=speed:
                    raise ValueError('GameCube heading adaptation changed swim speed')
                speeds[(phase,struct.unpack_from('>h',before,0xDE)[0])]=speed
                check(('GameCube' if gc else 'N64')+f' complete freshwater actor at phase {phase}',actor,bytes(expected))
            debug.write_memory(mode,struct.pack('>I',int(gc)))
            for origin in (0,1):
                value=bytearray(0x280);value[0x1DA]=origin;debug.write_memory(actor,bytes(value))
                result=call(helper,[actor],(helper,proof))
                if result!=int(gc):raise ValueError('Ocean mode did not include both fish origins')
                record(dict(fish_movement_mode=int(gc),origin=origin,assertion='passed'))
            check('complete loaded freshwater code retained',root,bytes(live))
        for at in (allocation,allocation+size-16):check('native fixture guard',at,edge)
        check('no native fault',0x8003CE34,bytes(4))
    finally:
        debug.write_memory(mode,saved_mode)
        call(0x8009C040,[allocation])
    return dict(fish_movement_native='passed',actor_cases=12,ocean_origin_cases=4,checks=checks,
        requires_checkpoint_restore=True,ordinary_fishing_or_hardware_tested=False)
