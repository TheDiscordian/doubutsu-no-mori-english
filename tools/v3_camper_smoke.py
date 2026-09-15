"""Native camper defaults, masked readers, and town/save isolation in RAM."""
import json
from pathlib import Path
import struct
from aflib import by_vrom,sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs
import v3_camper as runtime


def exercise(debug,rom_path,record):
    path=Path(rom_path); rom=path.read_bytes()
    report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=74:
        raise ValueError('Camper probe requires the current ABI 74 cartridge')
    blob=by_vrom(rom)[BLOB].extract(rom); boot=boot_proofs(rom)
    def check(label,address,expected):
        actual=debug.read_memory(address,len(expected))
        record(dict(camper_check=label,address=f'{address:08X}',bytes=len(expected),
            assertion='passed' if actual==expected else 'failed',
            expected_sha256=sha256(expected),observed_sha256=sha256(actual),
            observed_hex=actual.hex() if len(actual)<=32 else None))
        if actual!=expected: raise ValueError('Native camper mismatch: '+label)
    def call(address,args,expected=None,proof=None):
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion']='passed' if result['return_value']==expected else 'failed'
        record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Unexpected native camper return')
        return result['return_value']
    for address,size in ((runtime.REGISTER,report['camper']['registration']['bytes']),
                         (runtime.READER,report['camper']['reader']['bytes']),
                         (runtime.OWNER,runtime.OWNER_SIZE),(runtime.TRAMPOLINE,16)):
        at=runtime.PACKAGE+address-runtime.PACKAGE_RAM
        check('installed complete owner/code',address,blob[at:at+size])
    original_save=debug.read_memory(0x80126EA0,65536)
    original_list=debug.read_memory(0x80137000,15*56)
    original_runtime=debug.read_memory(0x8046C000,864)
    allocation=call(0x8009BFC0,[0xA00])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803FF600:
        raise ValueError('Camper fixture allocation failed')
    bridge,actor,expected_animal,out,private= (allocation+n for n in (0x10,0x40,0x200,0x800,0x900))
    edge=b'V3CP'*4
    debug.write_memory(allocation,edge); debug.write_memory(allocation+0x9F0,edge)
    actor_bytes=bytearray(0x180); actor_bytes[2]=3; actor_bytes[6:8]=bytes.fromhex('D08F')
    debug.write_memory(actor,actor_bytes)
    def upper(address,args,expected=None):
        stub=struct.pack('>2I',runtime.jump(address),0)
        debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]); call(0x80034CE0,[bridge,8])
        return call(bridge,args,expected,(bridge,stub))
    def register(npc,cloth=0,expected=1):
        return upper(runtime.REGISTER,[0xD08F,npc,cloth],expected)
    animal=runtime.OWNER+0x20
    # Real native defaults (including DMA for native villagers), not mocks.
    for npc in (0xE000,0xE0DA,0xE0EA,0xE0ED):
        call(0x800AA124,[])
        call(0x800A7A04,[expected_animal]); call(0x800AD8C4,[expected_animal,npc-0xE000])
        expected=debug.read_memory(expected_animal,0x528)
        register(npc)
        check(f'complete default Animal {npc:04X}',animal,expected)
        alias=call(0x800AA14C,[0xD08F])
        if alias not in (0x801375B0+i*12 for i in range(5)):
            raise ValueError('Camper alias outside native five slots')
        check('actual native alias identity and default outfit',alias,
            struct.pack('>3H',0xD08F,npc,npc)+expected[0x520:0x522]+b'\x00\x01\x00\x00')
        call(runtime.NPC_INFO,[actor,0])
        check('camper gets independent Animal and no town list',actor+0x174,struct.pack('>2I',animal,0))
        # Registration is idempotent; do not clear memories under a live actor.
        debug.write_memory(animal+0x30,b'\xA5'); register(npc)
        check('existing visitor memory is retained',animal+0x30,b'\xA5')
        if npc>=0xE0DA:
            call(0x80195D20,[out,actor])
            at=0x2C00+(npc-0xE0DA)*32
            check('actual English actor-name reader',out,blob[at+8:at+16])
            upper(report['asset']['symbols']['af_v3_npc_draw'],[out,0xD08F],1)
            at=0x2000+(npc-0xE0DA)*104+4
            check('masked appearance resolves the imported draw record',out,blob[at:at+100])
    register(0xE0EA,expected=0) # Cannot replace active Punchy with Cheri.
    call(0x800AA124,[]); call(runtime.NPC_INFO,[actor,0])
    check('cleared mask does not borrow the supplied town index',actor+0x174,bytes(8))
    for npc in (0xE0D8,0xE0D9,0xE0EE): register(npc,expected=0)
    debug.write_memory(0x80461E60,b'\x00'); register(0xE0DA,expected=0)
    debug.write_memory(0x80461E60,b'\x01')
    for i in range(5): call(0x800AA028,[0xD000+i,0xE000,0xE000,0x2400],1)
    before=debug.read_memory(animal,0x528); register(0xE0DA,expected=0)
    check('full native alias table leaves owner unchanged',animal,before)
    call(0x800AA124,[])
    # GC re-registration restores this player's memory after the first greeting.
    saved_private=debug.read_memory(0x80136FD8,4)
    identity=b'TesterCamper'+struct.pack('>HH',0x1234,0x5678)
    debug.write_memory(private,identity)
    debug.write_memory(0x80136FD8,struct.pack('>I',private))
    debug.write_memory(runtime.OWNER+0x10,b'\x01')
    register(0xE0DA,0xFFFF)
    check('native memory receives complete current personal ID',animal+16,identity)
    check('native Animal alignment padding retained',animal+12,bytes(4))
    check('native initial remembered friendship',animal+16+0x28,b'\x01')
    alias=call(0x800AA14C,[0xD08F])
    check('invalid explicit outfit uses native fallback',alias+6,bytes.fromhex('2400'))
    debug.write_memory(0x80136FD8,saved_private)
    debug.write_memory(runtime.OWNER+0x10,b'\x00')
    # Unrelated original attachment executes its preserved full prologue/body.
    debug.write_memory(actor+6,bytes.fromhex('E000')); call(runtime.NPC_INFO,[actor,0])
    check('native resident retains its original Animal and list',actor+0x174,
          struct.pack('>2I',0x80130DB8,0x80137000))
    check('complete native save remains unchanged',0x80126EA0,original_save)
    check('all town NpcLists remain unchanged',0x80137000,original_list)
    check('complete import save runtime unchanged',0x8046C000,original_runtime)
    for at in (allocation,allocation+0x9F0): check('fixture guard',at,edge)
    check('visitor guard',runtime.OWNER+0x550,bytes.fromhex('AFCA11ED')*4)
    at=runtime.PACKAGE+0x804A1FF0-runtime.PACKAGE_RAM
    check('scene packet guard',0x804A1FF0,blob[at:at+16])
    check('package guard',0x804A2FF0,bytes.fromhex('AFACC0DE')*4)
    check('translation guard',0x8019C8D0,bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    call(0x8009C040,[allocation])
    return dict(native_camper_owner=True,native_defaults=True,native_actor_name=True,
        town_slots_used=0,flash_write_or_reload=False,npc_constructor_or_gpu=False,
        manager_or_conversation=False,requires_checkpoint_restore=True)
