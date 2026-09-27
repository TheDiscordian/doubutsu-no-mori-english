"""Run the installed room callback through native prompt request, silently."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace
from aflib import by_vrom,sha256,CODE_RAM,CODE_VROM
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs
from v3_import_storage import ROWS_RAM,slot
import v3_console_room as console


def exercise(debug,rom_path,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed console-room test cartridge')
    files=by_vrom(image);blob=files[BLOB].extract(image);resources=report['equipment_resources']
    rows=console.checked_runtime(resources,blob,image);images=resources['console_images'];packet=images['packet']
    selected=[r for r in report['furniture']['imports'] if r.get('donor_item_id') in rows]
    if not selected:raise ValueError('Console room probe needs a selected complete console profile')
    row=selected[0];mapping=rows[row['donor_item_id']];index=row['runtime_index'];item=int(row['item_id'],16)
    proofs=boot_proofs(image);assertions=calls=0
    def check(label,address,wanted):
        nonlocal assertions
        actual=debug.read_memory(address,len(wanted));assertions+=1
        record(dict(console_room_check=label,address=f'{address:08X}',bytes=len(wanted),
                    assertion='passed' if actual==wanted else 'failed'))
        if actual!=wanted:raise ValueError('Native console room check failed: '+label)
    def call(address,args=(),proof=None):
        nonlocal calls
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,
            verified_code=proof or proofs.get(address));record(result);calls+=1;return result['return_value']
    def put(address,*words):debug.write_memory(address,struct.pack('>'+str(len(words))+'I',*words))
    check('complete console startup packet',packet['ram'],blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])
    check('selected profile identity',ROWS_RAM+slot(item)*80,struct.pack('>HHI',index,item,1))
    core=files[CODE_VROM].extract(image)
    def core_call(address,size,args=()):
        return call(address,args,(address,core[address-CODE_RAM:address-CODE_RAM+size]))
    current_game=int.from_bytes(debug.read_memory(0x8010EF90,4),'big')
    if current_game&3 or not 0x80000400<=current_game<=0x80400000-0xE0:
        raise ValueError('Invalid current native game arena owner')
    arena_header=debug.read_memory(current_game+0x78,16)
    arena_size,start,head,tail=struct.unpack('>4I',arena_header)
    record(dict(console_fixture_arena=dict(start=start,head=head,tail=tail,bytes=arena_size)))
    if not 0x80000400<=start<=head<=(tail&~15)-0x1E000<tail<=start+arena_size<=0x80400000:
        raise ValueError('Native game arena has insufficient checked fixture space')
    allocation=core_call(0x800D17D4,32,[current_game+0x78,0x1E000])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-0x1E000:
        raise ValueError('Native console room fixture allocation failed')
    owner=allocation+16;actor=allocation+0x1B000;room=allocation+0x1C000;bridge=allocation+0x1D000
    data,reloc=(files[v].extract(image) for v in (console.ROOM_VROM,0x844400))
    sections=struct.unpack_from('>5I',reloc);resident=len(data)+sections[3]
    if resident+len(reloc)>=actor-owner-16:raise ValueError('Native room fixture overlaps actor')
    loaded=relocate_verified_data(SimpleNamespace(ram=console.ROOM_RAM,resident_bytes=resident,sections=sections),data,reloc,owner)
    call(0x800262D0,[console.ROOM_VROM,console.ROOM_VROM+len(data),console.ROOM_RAM,
        console.ROOM_RAM+resident,owner,owner+resident,len(reloc)])
    check('complete relocated native room',owner,loaded)
    edge=b'CNRM'*4
    guards=(allocation,actor-16,actor+0xA10,room-16,room+0x4E0,bridge+16,allocation+0x1E000-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:debug.write_memory(at,edge)
    debug.write_memory(actor,bytes(0xA10));debug.write_memory(room,bytes(0x4E0))
    saved=debug.read_memory(0x80136F2C,4)
    window=core_call(0x8009D1F0,16)
    if core_call(0x8009E970,32,[window])!=1:raise ValueError('Native fixture requires the hidden message window')
    start=0x80939050-console.ROOM_RAM
    call(owner+start,[room],(owner+start,loaded[start:start+332]))
    check('native clip pointer',0x80136F2C,struct.pack('>I',room+0x2E8))
    check('native console callback',room+0x33C,struct.pack('>I',owner+0x8093BD60-console.ROOM_RAM))
    target=images['room']['compiled']['symbols']['af_v3_console_room_move']
    stub=struct.pack('>2I',0x08000000|(target>>2&0x3FFFFFF),0)
    debug.write_memory(bridge,stub);call(0x8002FE00,[bridge,32]);call(0x80034CE0,[bridge,32])
    debug.write_memory(actor,struct.pack('>H',index));debug.write_memory(actor+0x12D,b'\x01')
    call(bridge,[actor,room,room,0],(bridge,stub))
    check('native play prompt requested',room+0x3E8,struct.pack('>H',31))
    check('native request/game/explanation/port fields',room+0x47C,struct.pack('>4I',1,mapping['game_index'],0,0))
    # A second interaction cannot replace an in-progress native prompt.
    put(room+0x480,7);call(bridge,[actor,room,room,0],(bridge,stub))
    check('busy native prompt retained',room+0x480,struct.pack('>I',7))
    put(room+0x47C,0,0,0,0);debug.write_memory(actor+0x12D,b'\x00')
    call(bridge,[actor,room,room,0],(bridge,stub))
    check('unchanged switch does not request launch',room+0x47C,bytes(16))
    for at in guards:check('fixture/stack guard',at,edge)
    debug.write_memory(0x80136F2C,saved);debug.write_memory(current_game+0x78,arena_header)
    check('native game arena restored',current_game+0x78,arena_header)
    return dict(console_room_native='passed',native_calls=calls,memory_assertions=assertions,
        native_prompt_request=True,game_index=mapping['game_index'],emulator_gameplay_tested=False)
