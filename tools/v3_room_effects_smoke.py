"""Focused current-cartridge checks of the shared native effect extension."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,TEST_STACK
from v3_npc_draw_smoke import boot_proofs
from v3_room_effects import RAM


def exercise(debug,rom_path,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed shared-effects cartridge')
    room=report['equipment_resources']['room_rigs'];effects=room['effects'];controller=effects['controller']
    files=by_vrom(image);blob=files[0x2200000].extract(image);boot=boot_proofs(image);assertions=0
    def check(label,at,want):
        nonlocal assertions
        actual=debug.read_memory(at,len(want));passed=actual==want
        record(dict(room_effect_check=label,address=f'{at:08X}',bytes=len(want),
            assertion='passed' if passed else 'failed',actual=actual.hex() if len(actual)<48 else sha256(actual)))
        if not passed:raise ValueError('Native shared effect mismatch: '+label)
        assertions+=1
    def call(at,args=(),proof=None):
        result=debug.call(f'{at:08X}',list(args),return_address=MODULE_RAM+0x6480,verified_code=proof or boot.get(at))
        record(result);return result['return_value']
    def put(at,*values):debug.write_memory(at,struct.pack('>'+str(len(values))+'I',*values))
    def word(at):return int.from_bytes(debug.read_memory(at,4),'big')
    def bounded(at,n):
        if at&15 or not MODULE_RAM+0x8000<=at<=0x80400000-n:
            raise ValueError('Effect fixture allocation escapes native heap')
        return at
    size=0x6A00;allocation=bounded(call(0x8009BFC0,[size]),size)
    work_size=0x3B00;work=bounded(call(0x8009BFC0,[work_size]),work_size)
    owner=allocation+16
    game,gfx,actor,xlu,bridge=(work+i for i in (16,0x2200,0x2600,0x2800,0x3900))
    debug.write_memory(allocation,bytes(size));debug.write_memory(work,bytes(work_size));edge=b'V3EF'*4
    guards=(allocation,work,gfx-16,actor-16,xlu-16,bridge-16,bridge+32,
            allocation+size-16,work+work_size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    state=report['save_runtime'];saved={at:debug.read_memory(at,n) for at,n in (
        (0x80126EA0,65536),(0x80136EA0,0x900),(0x8010EF90,4),(0x801010C0,4),
        (0x801458B8,4),(state['state_ram'],state['state_bytes']))}
    data,reloc=(files[controller[k]].extract(image) for k in ('vrom','reloc'))
    sections=struct.unpack_from('>5I',reloc)
    expected=relocate_verified_data(SimpleNamespace(ram=RAM,resident_bytes=len(data),sections=sections),data,reloc,owner)
    call(0x800262D0,[controller['vrom'],controller['vrom']+len(data),RAM,RAM+len(data),owner,owner+len(data),len(reloc)])
    check('complete actual native owner loading and relocation',owner,expected)
    proof=(owner,expected[:sections[0]])
    put(game,gfx)
    put(gfx+0x2A8,xlu,xlu+0x1000);put(0x8010EF90,game);put(0x801010C0,owner)
    put(0x80126EB4,20)
    identity=struct.pack('>16f',*(1.0 if i%5==0 else 0.0 for i in range(16)))
    debug.write_memory(game+0x1E5C,identity)
    # Use the native initializers and actual twelve program allocations. Scene
    # lighting/campsite setup is unchanged and not replayed by this fixture.
    call(owner+0x1404,proof=proof)
    call(owner+0x1604,proof=proof)
    call(owner+0x1668,[actor],proof)
    check('native public clip',0x80136F3C,struct.pack('>I',actor+0x174))
    check('native program capacity',owner+0x3924,struct.pack('>I',12))
    native_pools=[bounded(word(owner+0x37A4+i*32),0xC00) for i in range(12)]
    for row in effects['profiles']:
        index=call(owner+0xE9C,[row['id']],proof)
        if not 0<=index<12:raise ValueError('Native effect program was not allocated')
        payload=blob[row['blob_offset']:row['blob_offset']+32]
        check('complete imported profile in real native code pool',native_pools[index],payload)
        check('copied native callback/lifetime profile',owner+0x37AC+index*32,payload[:24])
        if call(owner+0xE9C,[row['id']],proof)!=index:raise ValueError('Native effect cache failed')
    packet=room['packet'];check('lazy-loaded complete room packet',packet['ram'],blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])
    # Original effect 17 exercises the retained ordinary ovlmgr path.
    index=call(owner+0xE9C,[17],proof)
    if not 0<=index<12:raise ValueError('Original effect program failed to load')
    original=struct.unpack_from('>5I',data,0x2A00+17*20)
    entry=files[original[0]];rel_entry=next(e for e in files.values() if e.index==entry.index+1)
    native_data,native_rel=entry.extract(image),rel_entry.extract(image)
    spec=SimpleNamespace(ram=original[2],resident_bytes=original[3]-original[2],sections=struct.unpack_from('>5I',native_rel))
    want=relocate_verified_data(spec,native_data,native_rel,native_pools[index])
    check('complete original program still uses native loader',native_pools[index],want)
    # The real public request drives both new initializers through the existing
    # 80-slot native pool; its controller then creates real native particles.
    call(owner+0x1028,[112,0,0,0,2,0,game,0xFFFF,0,0],proof)
    effect_base,active=owner+0x392C,owner+0x54AC
    # Native active bytes store request priority, not a boolean one.
    controller_index=next(i for i in range(80) if debug.read_memory(active+i,1)!=b'\0' and
        debug.read_memory(effect_base+i*88+2,2)==b'\x00\x70')
    controlled=effect_base+controller_index*88
    check('controller begins at complete source lifetime',controlled,struct.pack('>h',240))
    for frame in range(120):
        put(gfx+0x2A8,xlu,xlu+0x1000)
        call(owner+0x1CD8,[actor,game],proof)
        if frame==0:
            check('native owner and callback jointly advance two source ticks',controlled,struct.pack('>h',238))
            particles=[i for i in range(80) if debug.read_memory(active+i,1)!=b'\0' and
                debug.read_memory(effect_base+i*88+2,2)==b'\x00\x6f']
            if len(particles)!=1:raise ValueError('Native controller did not create its flash')
            # Use the actual native graphics loader for the complete new sprite.
            params=bridge
            call(owner+0x1FE0,[params,params+4,111],proof)
            check('native graphics range resolves complete donor sprite',params,
                struct.pack('>2I',effects['bank']['resource_vrom'],effects['bank']['resource_bytes']))
    check('all thirty source flashes emitted',controlled+0x4C,struct.pack('>h',30))
    check('controller expires in the native owner',active+controller_index,b'\0')
    check('all particles cleaned up by native pool',active,bytes(80))
    for p in native_pools:call(0x8009C040,[p])
    for at,want in saved.items():debug.write_memory(at,want)
    check('saved import state restored',state['state_ram'],saved[state['state_ram']])
    for at in guards:check('private work and stack guard',at,edge)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[work]);call(0x8009C040,[allocation])
    return dict(native_effect_loading=True,native_profile_cache=True,original_program_preserved=True,
        complete_controller_lifetime=True,assertions=assertions,requires_checkpoint_restore=True,
        gpu_or_hardware=False,ordinary_room=False,saved_data_written=False)
