"""Actual native growth, saved visitor exclusion, and refused inbound transfer."""
import json
from pathlib import Path
import struct
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_import_storage import jump
from v3_npc_draw_smoke import boot_proofs


def exercise(debug,rom_path,record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=77:
        raise ValueError('Camper move-in probe requires the current ABI 77 cartridge')
    files,boot=by_vrom(rom),boot_proofs(rom);guard=report['camper_movein'];symbols=guard['code']['symbols']
    prefix=files[BLOB].extract(rom)[:0xC000]
    def check(label,address,value):
        actual=debug.read_memory(address,len(value))
        record(dict(camper_movein_check=label,address=f'{address:08X}',bytes=len(value),
            assertion='passed' if actual==value else 'failed',expected_sha256=sha256(value),
            observed_sha256=sha256(actual)))
        if actual!=value: raise ValueError('Native camper move-in mismatch: '+label)
    def call(address,args=(),want=None,proof=None):
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(address))
        if want is not None: result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:
            raise ValueError(f'Unexpected native camper move-in return at {address:08X}')
        return result['return_value']
    check('current complete installed prefix',0x80460000,prefix)
    saved=debug.read_memory(0x80126EA0,65536)
    other={at:debug.read_memory(at,n) for at,n in ((0x80136EA3,1),(0x80464700,32),(0x8003C590,4))}
    allocation=call(0x8009BFC0,[0x1800])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FE800:
        raise ValueError('Camper move-in fixture allocation failed')
    animal,bridge=allocation+16,allocation+0x1000;edge=b'V3MI'*4
    for at in (allocation,allocation+0x17F0): debug.write_memory(at,edge)
    def upper(address,args,want):
        stub=struct.pack('>2I',jump(address),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,args,want,(bridge,stub))
    debug.write_memory(0x80130DB8,bytes(15*0x528));debug.write_memory(0x80135CF4,bytes(4))
    history=bytearray(b'\xFF'*32);history[237//8]&=~(1<<(237&7))
    debug.write_memory(0x8013670C,history)
    personality=next(r['personality'] for r in report['villager_text']['imports'] if r['actor_id']=='E0ED')
    call(0x800AD6D4,[personality],237)
    selected=call(0x80080080,[70,0])
    if selected not in (0x80135D00+i*48 for i in range(5)): raise ValueError('Invalid native event save area')
    debug.write_memory(selected,bytes.fromhex('E0ED')+bytes(38))
    call(0x800AD6D4,[personality],0xFFFFFFFF)
    check('saved camper is excluded even when unseen',0x80464700,bytes(32))
    # The all-appeared reset is an ordinary caller of the actual native reset.
    debug.write_memory(0x8013670C,b'\xFF'*32);call(0x800AA49C)
    check('actual all-appeared reset runs without resident changes',0x8013670C,bytes(32))
    chosen=call(0x800AD6D4,[personality])
    native_looks=files[CODE_VROM].extract(rom)[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
    expected=bytearray(32)
    for i,p in enumerate(native_looks):
        if p==personality: expected[i//8]|=1<<(i&7)
    for row in report['villager_text']['imports']:
        i=int(row['actor_id'],16)&255
        if row['personality']==personality and i!=237: expected[i//8]|=1<<(i&7)
    check('whole native and selected-import candidate set excludes active camper',0x80464700,expected)
    if chosen>=238 or not expected[chosen//8]&(1<<(chosen&7)):
        raise ValueError('Native grow returned a camper or unavailable identity')
    candidate=bytes.fromhex('E0ED')+bytes(0x526);debug.write_memory(animal,candidate)
    upper(symbols['af_v3_camper_transfer_blocked'],[animal],1)
    # Real native incoming transfer: player kind 4 is visiting, not moving out.
    debug.write_memory(0x80136EA3,b'\x04');debug.write_memory(0x80135B10,bytes(2))
    call(0x800AC57C,[animal,0])
    check('full native transfer leaves all town Animals untouched',0x80130DB8,bytes(15*0x528))
    check('full native transfer does not consume or mark the incoming Animal',animal,candidate)
    check('full native transfer retains saved camper payload',selected,bytes.fromhex('E0ED')+bytes(38))
    for id,want in ((0xE000,1),(0xD08F,0),(0xE0EA,0)):
        debug.write_memory(selected,struct.pack('>H',id))
        debug.write_memory(animal,bytes.fromhex('E000'))
        upper(symbols['af_v3_camper_transfer_blocked'],[animal],want)
    call(0x800804AC,[70,0]);debug.write_memory(0x8013670C,history)
    call(0x800AD6D4,[personality],237)
    check('camper becomes eligible again after event save release',0x80464700,bytes(29)+b'\x20\0\0')
    debug.write_memory(0x80126EA0,saved)
    for at,value in other.items(): debug.write_memory(at,value)
    check('complete saved town restored',0x80126EA0,saved)
    check('complete prefix restored',0x80460000,prefix)
    for at in (allocation,allocation+0x17F0): check('move-in fixture guard',at,edge)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4));call(0x8009C040,[allocation])
    return dict(native_natural_growth=True,actual_appearance_reset=True,
        full_native_inbound_transfer_refused=True,ordinary_arrival_or_persistence=False,
        saved_data_written=False,requires_checkpoint_restore=True)
