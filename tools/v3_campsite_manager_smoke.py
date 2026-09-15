"""Native calendar-to-manager selection and real tent placement/removal calls."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom,sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_import_storage import jump
from v3_npc_draw_smoke import boot_proofs
import v3_campsite_manager as runtime


def exercise(debug,rom_path,record):
    path=Path(rom_path);rom=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(rom)!=report['output_sha256'] or report['runtime_abi']!=76:
        raise ValueError('Manager probe requires the current ABI 76 cartridge')
    files,boot=by_vrom(rom),boot_proofs(rom); manager_report=report['campsite_manager']
    data,reloc=files[runtime.VROM].extract(rom),files[runtime.RELOC].extract(rom)
    symbols=manager_report['code']['symbols']; live=0;expected=b''
    def check(label,address,value):
        actual=debug.read_memory(address,len(value))
        record(dict(manager_check=label,address=f'{address:08X}',bytes=len(value),
            assertion='passed' if actual==value else 'failed',expected_sha256=sha256(value),
            observed_sha256=sha256(actual),observed_hex=actual.hex() if len(actual)<=32 else None))
        if actual!=value: raise ValueError('Native camper manager mismatch: '+label)
    def call(address,args=(),want=None,proof=None):
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(address))
        if want is not None: result['assertion']='passed' if result['return_value']==want else 'failed'
        record(result)
        if want is not None and result['return_value']!=want:
            raise ValueError(f'Unexpected native manager return at {address:08X}')
        return result['return_value']
    def put(address,value): debug.write_memory(address,struct.pack('>I',value))
    def word(address): return struct.unpack('>I',debug.read_memory(address,4))[0]
    def owned(address,args=(),want=None):
        start=runtime.SIZE if address>=runtime.RAM+runtime.SIZE else 0
        proof=(live+start,expected[start:] if start else expected[:25424])
        return call(live+address-runtime.RAM,args,want,proof)
    check('current installed English manager descriptor',runtime.METADATA,bytes.fromhex(manager_report['metadata_after']))
    saved=debug.read_memory(0x80126EA0,65536)
    saved_lists=debug.read_memory(0x80137000,15*56);saved_runtime=debug.read_memory(0x8046C000,864)
    globals_before={at:debug.read_memory(at,n) for at,n in ((0x8013A248,4),(0x80106818,4),(0x80136FBE,6),
        (0x80126EB4,4),(0x80136EA4,4))}
    allocation=call(0x8009BFC0,[0xE000])
    if allocation&15 or not MODULE_RAM+0x8000<=allocation<=0x803F2000:
        raise ValueError('Current manager fixture allocation failed')
    live=allocation+16
    actor,field,blocks,grid,lots,bridge,schedule=(allocation+n for n in
        (0xB000,0xB300,0xB600,0xD000,0xD300,0xD500,0xD580))
    if live+len(data)+len(reloc)+16>actor: raise ValueError('Manager image overlaps fixture')
    edge=b'V3CM'*4
    for at in (allocation,live+len(data)+len(reloc),allocation+0xDFF0): debug.write_memory(at,edge)
    expected=relocate_verified_data(SimpleNamespace(ram=runtime.RAM,resident_bytes=len(data),
        sections=struct.unpack_from('>5I',reloc)),data,reloc,live)
    call(0x800262D0,[runtime.VROM,runtime.VROM+len(data),runtime.RAM,runtime.RAM+len(data),
                     live,live+len(data),len(reloc)])
    check('complete current English owner loaded and relocated',live,expected)
    check('complete merged native relocation directory',live+len(data),reloc)
    debug.write_memory(actor,bytes(592));debug.write_memory(field,bytes(0x300))
    debug.write_memory(blocks,bytes(4*0x614));debug.write_memory(grid,bytes(512));debug.write_memory(lots,bytes(256))
    put(field+0x148,blocks); debug.write_memory(field+0x166,b'\x02\x02')
    put(blocks+3*0x614+0x584,grid)
    debug.write_memory(field,bytes.fromhex('3012'));put(0x8013A248,field);put(0x80106818,lots)
    def upper(address):
        stub=struct.pack('>2I',jump(address),0);debug.write_memory(bridge,stub)
        call(0x8002FE00,[bridge,8]);call(0x80034CE0,[bridge,8])
        return call(bridge,proof=(bridge,stub))
    # Actual installed calendar populates type 70; include one unchanged native
    # event to verify the copied controls as well as the appended summer row.
    debug.write_memory(0x80136FBE,struct.pack('>BBBBH',9,6,6,6,2026))
    put(0x80126EB4,0);put(0x80136EA4,1)
    call(0x8007DBB0)
    calendar=report['campsite_calendar']['code']['symbols']
    upper(calendar['af_v3_campsite_today_init']); upper(calendar['af_v3_campsite_before_cleanup'])
    debug.write_memory(schedule,bytes.fromhex('06060000060600170000000e'))
    call(0x8007E264,[0x0606,schedule])
    owned(0x809612B0,want=1)
    table=live+manager_report['table']-runtime.RAM;control=table+28*32
    check('native today-directory count includes both events',live+0x80962458-runtime.RAM,struct.pack('>I',2))
    check('native original and summer control pointers',live+0x809623D8-runtime.RAM,struct.pack('>2I',table+20*32,control))
    # Force one unseen imported identity through the actual reset/shuffle/grow
    # operations. Its full native registration must use that saved selection.
    debug.write_memory(0x8013670C,b'\xFF'*32)
    debug.write_memory(0x8013670C+237//8,bytes([255^(1<<(237&7))]))
    put(0x80135CF4,0);call(0x800AA124);call(0x80080000,[70])
    debug.write_memory(0x804A1A10,b'\x01')
    call(0x8007FDA8,[70,1]);owned(0x80961004,[actor,control],1)
    call(0x8007FF08,[70,0x10],1);call(0x80080040,[70],1)
    selected=call(0x8008033C,[70,0])
    if selected not in (0x80135D00+i*48 for i in range(5)): raise ValueError('Invalid selected camper save area')
    check('real native selection stored complete Punchy identity',selected,bytes.fromhex('E0ED')+bytes(38))
    check('new selection clears first-greeting state',0x804A1A10,b'\x00')
    alias=call(0x800AA14C,[0xD08F])
    if alias not in (0x801375B0+i*12 for i in range(5)): raise ValueError('Invalid native camper alias')
    check('native masked registration uses selected real identity',alias,bytes.fromhex('D08FE0EDE0ED'))
    check('independent complete visitor identity',0x804A1A20,bytes.fromhex('E0ED'))
    history=debug.read_memory(0x8013670C,32)
    owned(symbols['af_v3_camper_event_start'],[actor,control],2)
    check('repeated start retains selected identity and payload',selected,bytes.fromhex('E0ED')+bytes(38))
    check('repeated start does not select another camper',0x8013670C,history)
    # Prepare one native outdoor block and an actual reserved common-place
    # record. This tests the real manager placement helper, not a mocked call.
    place=call(0x80080C68,[70,0x51])
    if not 0x80130000<=place<=0x80140000-20: raise ValueError('Native common-place allocation failed')
    debug.write_memory(place,struct.pack('>4iHH',1,1,8,0,0x5849,0))
    debug.write_memory(field,bytes(2));debug.write_memory(grid+2*(8*16),bytes.fromhex('5813'))
    call(0x80080000,[70]);call(0x8007FE74,[70,0x10])
    owned(0x80961004,[actor,control],0)
    call(0x80080040,[70],0);call(0x8007FF08,[70,0x10],0);call(0x8007FF08,[70,0x20],0)
    call(0x8007FF08,[70,1],1)
    debug.write_memory(place,struct.pack('>4iHH',1,1,8,8,0x5849,0))
    debug.write_memory(grid,bytes(512));debug.write_memory(grid+2*(8*16+8),bytes.fromhex('5813'))
    owned(0x80961004,[actor,control],1)
    call(0x80080040,[70],1);call(0x8007FF08,[70,0x10],1);call(0x8007FF08,[70,0x20],0)
    foreground=bytearray(512)
    for z in range(7,10):
        for x in range(7,10): struct.pack_into('>H',foreground,2*(z*16+x),0x5849 if (x,z)==(8,8) else 0xFFFF)
    check('real manager helper places complete nine-cell tent',grid,foreground)
    owned(symbols['af_v3_camper_event_start'],[actor,control],2)
    check('repeated outdoor start retains the same tent',grid,foreground)
    call(0x8007FE74,[70,1]);put(0x8013A248,0)
    owned(0x80961004,[actor,control],0)
    call(0x80080040,[70],1);call(0x8007FF08,[70,0x10],1)
    put(0x8013A248,field);owned(0x80961004,[actor,control],1)
    call(0x80080040,[70],0);call(0x8007FF08,[70,0x10],0);call(0x80080D68,[70,0x51],0)
    removed=debug.read_memory(grid,512);lot=struct.unpack_from('>H',removed,2*(8*16+8))[0]
    if not 0x5810<=lot<0x5825: raise ValueError('Manager stop did not restore the housing lot')
    cleared=bytearray(512);struct.pack_into('>H',cleared,2*(8*16+8),lot)
    check('real manager stop removes tent and restores the housing lot',grid,cleared)
    check('native original town Animals retained',0x80130DB8,saved[0x80130DB8-0x80126EA0:0x80130DB8-0x80126EA0+15*0x528])
    check('all native NpcLists retained',0x80137000,saved_lists)
    check('complete import save runtime retained',0x8046C000,saved_runtime)
    for at in (allocation,live+len(data)+len(reloc),allocation+0xDFF0): check('manager fixture guard',at,edge)
    for at,value in ((0x804A1F50,'AFCA11ED'),(0x804A2CF0,'AFC7CA1E'),(0x804A2FF0,'AFACC0DE'),(0x8019C8D0,'AF32C0DE')):
        check('retained owner/package guard',at,bytes.fromhex(value)*4)
    check('no faulted thread',0x8003CE34,bytes(4))
    debug.write_memory(0x80126EA0,saved)
    for at,value in globals_before.items(): debug.write_memory(at,value)
    call(0x8009C040,[allocation])
    return dict(native_complete_event_manager_relocation=True,native_calendar_to_control=True,
        native_camper_selection_and_registration=True,native_start_stop_and_retry=True,
        native_tent_placement_and_removal=True,constructed_scene_or_gpu=False,
        conversation_or_reward=False,flash_write_or_reload=False,requires_checkpoint_restore=True)
