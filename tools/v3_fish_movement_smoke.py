"""Actual native freshwater patrol and shared ocean mode checks."""
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
    if world.get('freshwater'):
        return exercise_complete(debug,image,report,record)
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


def exercise_complete(debug,image,report,record):
    """Execute the installed six-callback port and retained native alternative."""
    import math
    world=report['equipment_resources']['creature_fish']['world'];fresh=world['freshwater']
    files=by_vrom(image);boot=boot_proofs(image)
    row=next(r for r in report['equipment_resources']['creature_fish']['owners'] if r['name']=='river')
    data=files[row['vrom']].extract(image);rel=files[row['reloc']].extract(image);ram=row['ram']
    if sha256(data)!=row['sha256'] or sha256(rel)!=row['reloc_sha256']:
        raise ValueError('Changed complete freshwater owner or relocation')
    checks=cases=0
    def check(label,at,want):
        nonlocal checks
        passed=debug.read_memory(at,len(want))==want
        record(dict(fish_movement_check=label,address=f'{at:08X}',assertion='passed' if passed else 'failed'))
        if not passed:raise ValueError('Native freshwater mismatch: '+label)
        checks+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=TEST_RETURN,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    size=0x9000;allocation=call(0x8009BFC0,[size])
    scene=report['equipment_resources']['scene_arena'];workspace=scene['workspace']
    lower=0x801A0000<=allocation<=0x80400000-size
    upper=(debug.read_memory(scene['borrowed_state']['ram'],4)==struct.pack('>I',1) and
        workspace['free_block']+16<=allocation<=workspace['end_guard']-size)
    if allocation&15 or not(lower or upper):
        raise ValueError('Freshwater fixture exceeds the native heap')
    if upper:
        for at in (workspace['front_guard'],workspace['end_guard']):
            check('exclusive scene-workspace guard',at,bytes.fromhex('AF53434E')*4)
    root=allocation+16;actor=allocation+0x3000;player=allocation+0x4000
    bobber=allocation+0x5400;game=allocation+0x6000;edge=b'FISH'*4
    debug.write_memory(allocation,edge+bytes(size-32)+edge)
    sections=struct.unpack_from('>5I',rel)
    loaded=relocate_verified_data(SimpleNamespace(ram=ram,resident_bytes=len(data),sections=sections),data,rel,root,
        memory_end=0x80800000 if upper else 0x80400000)
    call(0x800262D0,[row['vrom'],row['vrom']+len(data),ram,ram+len(data),root,root+len(data),len(rel)])
    check('complete selected freshwater DMA and relocation',root,loaded)
    p=world['packet'];packet=files[BLOB].extract(image)[p['blob_offset']:p['blob_offset']+p['bytes']]
    proofs={}
    for fragment in fresh['code']['fragments']:
        a=fragment['ram'];raw=packet[a-p['ram']:a-p['ram']+fragment['bytes']]
        if sha256(raw)!=fragment['sha256']:raise ValueError('Changed complete freshwater fragment')
        check('actual startup loaded complete freshwater code',a,raw)
        for name,address in fresh['code']['symbols'].items():
            if a<=address<a+len(raw):proofs[address]=(a,raw)
    for reservation in fresh['reservations']:
        check('freshwater installed guard',reservation['guard'],struct.pack('>4I',*([reservation['guard_value']]*4)))
    callback={name:fresh['code']['symbols']['af_v3_freshwater_'+name]
        for name in ('swim','wait','escape','swim_init','wait_init','escape_init')}
    native={name:root+before-ram for (_,before,name) in __import__('v3_freshwater_movement').BINDINGS}
    owner_proof=(root,loaded[:sections[0]])
    saved={a:debug.read_memory(a,n) for a,n in ((0x8010EF90,4),(0x8003C590,4),(world['patrol_mode']['ram'],4))}
    def seed():debug.write_memory(0x8003C590,struct.pack('>I',0x12345678))
    def state(kind=0,phase=90.,work=20,fish=0):
        a=bytearray(0x280)
        struct.pack_into('>I',a,0x244,root);struct.pack_into('>I',a,0x1D4,fish)
        struct.pack_into('>h',a,0x1D8,0);struct.pack_into('>I',a,0x1DC,2)
        struct.pack_into('>2h',a,0x22C,400,-32000)
        struct.pack_into('>f',a,0x224,phase);struct.pack_into('>i',a,0x214,work)
        struct.pack_into('>f',a,0x74,2.0);a[0x23E]=kind
        return a
    def tables(gc):
        for address,before,name in __import__('v3_freshwater_movement').BINDINGS:
            target=callback[name] if gc else root+before-ram
            debug.write_memory(root+address-ram,struct.pack('>I',target))
    try:
        g=bytearray(0x1E00);struct.pack_into('>I',g,0x1C90,player)
        debug.write_memory(game,g);debug.write_memory(0x8010EF90,struct.pack('>I',game))
        pl=bytearray(0x12D8);struct.pack_into('>3f',pl,0x28,9999.,0.,9999.)
        debug.write_memory(player,pl)
        # All six selected pointers reach the donor functions. N64 composition
        # preservation is separately checked over the complete owner/relocation.
        for address,_,name in __import__('v3_freshwater_movement').BINDINGS:
            check('selected '+name+' callback',root+address-ram,struct.pack('>I',callback[name]))
        # Initializers have matching native platform rules for the three donor
        # swimming kinds. Compare full actors and exact random consumption.
        for name in ('swim_init','wait_init','escape_init'):
            for kind in range(3):
                a=state(kind);debug.write_memory(actor,a);seed();tables(False)
                call(native[name],[actor],owner_proof)
                expected=debug.read_memory(actor,len(a));rng=debug.read_memory(0x8003C590,4)
                debug.write_memory(actor,a);seed();tables(True)
                call(callback[name],[actor],proofs[callback[name]])
                check('complete donor '+name+' kind '+str(kind),actor,expected)
                check('initializer exact RNG',0x8003C590,rng);cases+=1
        # Swimming speed/phase retains elapsed native units. Only the donor
        # curved-heading additions differ, and no native instruction is patched.
        for kind,phase in ((0,90.),(1,90.),(2,90.),(2,0.)):
            a=state(kind,phase);debug.write_memory(actor,a)
            old=0x80932024 if kind==2 else 0x80931FAC
            bits=lambda f:int.from_bytes(struct.pack('>f',f),'big')
            call(root+old-ram,[actor,bits(180. if kind else 360.),bits(5.),bits(1. if kind==2 else .5)],owner_proof)
            expected=bytearray(debug.read_memory(actor,len(a)))
            if kind==2 and phase==90.:struct.pack_into('>h',expected,0xDE,800)
            debug.write_memory(actor,a);tables(True)
            call(callback['swim'],[actor,game],proofs[callback['swim']])
            # Ordinary bobber search sets the real linked-actor field to NULL.
            check('complete donor swimming kind '+str(kind)+' phase '+str(phase),actor,bytes(expected));cases+=1
        # Completion must select the donor WAIT initializer through the actual
        # relocated action table, not leave an old callback installed.
        for kind,phase in ((0,355.),(1,175.),(2,175.)):
            debug.write_memory(actor,state(kind,phase));seed();tables(True)
            call(callback['swim'],[actor,game],proofs[callback['swim']])
            check('donor swimming completes in WAIT',actor+0x1DC,struct.pack('>2I',1,callback['wait']))
            check('wait clears linked flag',actor+0x23C,bytes(2));cases+=1
        # Source wall handling sets ESCAPE and executes its donor initializer.
        a=state();struct.pack_into('>I',a,0x98,(1<<21)|(1<<18))
        debug.write_memory(actor,a);tables(True)
        call(callback['swim'],[actor,game],proofs[callback['swim']])
        check('wall escape callback and initializer',actor+0x1DC,struct.pack('>2I',2,callback['escape']))
        check('wall escape elapsed timer',actor+0x214,struct.pack('>I',50));cases+=1
        # Use the actual native current reader to face the actual fishing float.
        debug.write_memory(actor,state())
        current=call(root+0x80932188-ram,[actor],owner_proof)&65535
        signed=(current+32768)%65536-32768
        uk=bytearray(0x500);struct.pack_into('>h',uk,0,111)
        theta=signed*(2*math.pi/65536)
        struct.pack_into('>3f',uk,0x28,math.sin(theta)*25.,0.,math.cos(theta)*25.)
        debug.write_memory(bobber,uk);struct.pack_into('>I',g,0x1CA0,bobber);debug.write_memory(game,g)
        for fish in (0,36):
            for gc in (False,True):
                a=state(fish=fish);struct.pack_into('>h',a,0x36,signed);struct.pack_into('>h',a,0xDE,signed)
                debug.write_memory(actor,a);tables(gc)
                entry=callback['escape'] if gc else native['escape']
                call(entry,[actor,game],proofs[entry] if gc else owner_proof)
                check(('GameCube' if gc else 'N64')+' escape float transition fish '+str(fish),
                    actor+0x1DC,struct.pack('>I',3 if gc else 2));cases+=1
            # A WAIT that expires enters SWIM without immediately searching for
            # the float. This is the source branch, unlike the native sequence.
            a=state(work=1,fish=fish);struct.pack_into('>h',a,0x36,signed);struct.pack_into('>h',a,0xDE,signed)
            debug.write_memory(actor,a);seed();tables(True)
            call(callback['wait'],[actor,game],proofs[callback['wait']])
            check('donor WAIT completes in SWIM fish '+str(fish),actor+0x1DC,struct.pack('>2I',0,callback['swim']))
            check('expired WAIT does not search float',actor+0x1C8,bytes(4));cases+=1
        # With no float, the complete donor escape decelerates for two elapsed
        # donor ticks and then invokes WAIT when its timer expires.
        struct.pack_into('>I',g,0x1CA0,0);debug.write_memory(game,g)
        for work in (20,1):
            debug.write_memory(actor,state(work=work));seed();tables(True)
            call(callback['escape'],[actor,game],proofs[callback['escape']])
            if work==1:check('escape completion uses donor WAIT',actor+0x1DC,struct.pack('>2I',1,callback['wait']))
            else:
                speed=struct.unpack('>f',debug.read_memory(actor+0x74,4))[0]
                if abs(speed-1.96)>1e-6:raise ValueError('Donor escape deceleration is not frame adapted')
                check('donor escape timer',actor+0x214,struct.pack('>I',19))
            cases+=1
        helper=world['compiled']['symbols']['donor'];mode=world['patrol_mode']['ram']
        proof=(helper,packet[helper-p['ram']:helper-p['ram']+36])
        for gc in (0,1):
            debug.write_memory(mode,struct.pack('>I',gc))
            for origin in (0,1):
                a=state();a[0x1DA]=origin;debug.write_memory(actor,a)
                if call(helper,[actor],proof)!=gc:raise ValueError('Shared ocean movement lost an original/imported fish')
        tables(True)
        check('complete retained native freshwater code',root,loaded[:sections[0]])
        for at in (allocation,allocation+size-16):check('native fixture guard',at,edge)
        check('no native fault',0x8003CE34,bytes(4))
    finally:
        for at,value in saved.items():debug.write_memory(at,value)
        call(0x8009C040,[allocation])
    return dict(fish_movement_native='passed',complete_callback_cases=cases,ocean_origin_cases=4,checks=checks,
        requires_checkpoint_restore=True,ordinary_fishing_or_hardware_tested=False)
