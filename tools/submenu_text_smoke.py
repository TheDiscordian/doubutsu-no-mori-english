"""Execute native menu loaders/drawers in owned RAM and verify complete glyphs."""
import struct

from aflib import sha256
from birthday_draw_scenario import CALLBACK
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from extended_font_test_scenario import texture_commands
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from submenu_text_scenario import ROM_SHA,LOADER_SHA
import editor_confirmation as confirmation
import embedded_warnings as warning

EDGE=b'MENU'*4
def words(*values):return struct.pack('>'+'I'*len(values),*values)
def floats(*values):return struct.pack('>'+'f'*len(values),*values)


def exercise(debug,request,record):
    read=debug.read_memory;calls=assertions=0
    def write(at,data):
        debug.write_memory(at,data)
        record({'submenu_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,value):
        nonlocal assertions
        actual=read(at,len(value));assertions+=1
        record({'submenu_check':label,'address':f'{at:08X}',
            'assertion':'passed' if actual==value else 'failed','bytes':len(value),
            'expected_sha256':sha256(value),'observed_sha256':sha256(actual)})
        if actual!=value:raise ValueError('Native embedded menu mismatch: '+label)
    def call(at,args=(),proof=None):
        nonlocal calls
        result=debug.call(f'{at:08X}',list(args),verified_code=proof);calls+=1;record(result)
        return result['return_value']
    loader=bytes.fromhex(request['loader'])
    if (request['rom_sha256']!=ROM_SHA or sha256(loader)!=LOADER_SHA
            or bytes.fromhex(request['matrix_callback'])!=CALLBACK):
        raise ValueError('Unapproved native menu code fixture')
    images={int(v,16):bytes.fromhex(data) for v,data in request['images'].items()}
    saved=read(SAVE_RAM,SAVE_BYTES);segment=read(0x801458D0,4);allocations=[]
    for size in (0x12000,0x10000):
        address=call(0x8009BFC0,[size])
        if address&15 or not MODULE_RAM+RESERVATION<=address<=0x80400000-size:
            raise ValueError('Embedded menu fixture allocation failed')
        allocations.append(address)
    context,aux=allocations
    overlay=context+0x10;menu=context+0x10800;submenu=context+0x10880
    state=context+0x10900;game=context+0x10940
    base=aux+0x10;staging=aux+0x2000;callback=aux+0x2400
    assets=aux+0x3000;graph=aux+0x5800;arena=aux+0x6000;arena_end=aux+0xFFF0
    guards=(context,overlay+0x10730,menu-16,menu+0x40,submenu-16,submenu+0x40,
        state-16,state+16,game-16,game+0x40,context+0x12000-16,aux,
        staging-16,callback-16,callback+48,assets-16,graph-16,graph+0x300,
        arena-16,arena_end,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:write(at,EDGE)
    write(callback,CALLBACK);draws=[];loaded_owners=[]
    owners=((confirmation.VROM,confirmation.RELOC,confirmation.RAM,None,0),
        (warning.WARNING.new_vrom,warning.WARNING.new_relocation,warning.WARNING.ram,warning.WARNING,0xACA000),
        (warning.PAK.new_vrom,warning.PAK.new_relocation,warning.PAK.ram,warning.PAK,0xB17000))
    for vrom,reloc_vrom,ram,owner,asset_vrom in owners:
        data=images[vrom];reloc=images[reloc_vrom];asset=images[asset_vrom] if asset_vrom else b''
        sections=struct.unpack_from('>5I',reloc);spec=Image(ram,sum(sections[:4]),sections)
        if base+spec.resident_bytes>staging-16 or assets+len(asset)>graph-16 or len(reloc)>0x300:
            raise ValueError('Embedded menu fixture buffers overlap')
        local_guards=(base+spec.resident_bytes,staging+len(reloc),assets+len(asset))
        for at in local_guards:write(at,EDGE)
        call(0x800262D0,[vrom,vrom+len(data),ram,ram+spec.resident_bytes,base,staging,len(reloc)],
            (0x800262D0,loader))
        loaded=relocate_verified_data(spec,data,reloc,base)
        check('complete cartridge owner and native BSS',base,loaded)
        if asset:write(assets,asset)
        write(overlay,bytes(0x10730));write(menu,bytes(0x40))
        write(submenu,bytes(0x40));write(game,bytes(0x40));write(graph,bytes(0x300))
        write(submenu+0x2C,words(overlay));write(menu+0x28,words(assets));write(game,words(graph))
        write(overlay+0x106B4,words(callback))
        state_offset=0x106F8 if owner is None else 0x106FC if owner==warning.WARNING else 0x10718
        write(overlay+state_offset,words(state));snapshot=read(overlay,0x10730)
        cases=(0,) if owner is None else (0,2) if owner==warning.WARNING else (0,8,9)
        for window in cases:
            state_data=bytes((1,2,0,0))+floats(1.0)+bytes(8) if owner is None else (
                bytes(4)+floats(1.0)+bytes(8) if owner==warning.WARNING else
                bytes((0,255,0,0,0,1,0,0))+floats(1.0,1.0 if window in (8,9) else 0.0))
            write(state,state_data);write(menu+0x38,words(window));menu_data=read(menu,0x40)
            for offset in (0x290,0x2B0):write(graph+offset,words(arena_end-arena,arena,arena,arena_end))
            write(arena,bytes(arena_end-arena))
            proof=(base,loaded[:sections[0]])
            if owner is None:
                call(base+0x8089646C-ram,[submenu,graph,game,0,0],proof)
                call(base+0x8089652C-ram,[submenu,graph,game,0,0,base+0xB50+36],proof)
                expected=b''.join(row[-1] for row in confirmation.ROWS)
            elif owner==warning.WARNING:
                call(base+0x8089700C-ram,[submenu,game,menu,base+owner.table+window*16],proof)
                expected=''.join(warning.WARNING_TEXT[window]).encode()
            else:
                call(base+0x808A37F0-ram,[submenu,menu,game],proof)
                expected=''.join(warning.PAK_TEXT[window]).encode()
                if window in (8,9):expected+=''.join(warning.PAK_TEXT[11 if window==8 else 12]).encode()
            front,back=struct.unpack('>2I',read(graph+0x298,8))
            if not arena<front<back<arena_end:raise ValueError('Menu graphics escape the owned arena')
            output=read(arena,front-arena);cursor=0
            for char in expected:
                glyph=texture_commands(0x8013A680,char);at=output.find(glyph,cursor)
                if at<0:raise ValueError(f'Missing ordered menu glyph {char:02X} after {cursor:04X} in {vrom:08X}/{window}')
                cursor=at+len(glyph)
            glyphs=sum(output[at:at+4]==bytes.fromhex('FD88005F') for at in range(0,len(output),8))
            if glyphs!=len(expected):raise ValueError('Embedded menu draws unexpected extra or missing glyphs')
            check('read-only warning/selection state',state,state_data)
            check('read-only menu descriptor',menu,menu_data);check('read-only submenu context',overlay,snapshot)
            if asset:check('complete native asset retained',assets,asset)
            draws.append({'owner':f'{vrom:08X}','window':window,'glyphs':glyphs,
                'display_list_bytes':front-arena,'back_bytes':arena_end-back,'complete_english':True})
            record({'submenu_native_draw':draws[-1]})
        check('complete native owner retained',base,loaded)
        for at in local_guards:check('owner, relocation, and asset guard',at,EDGE)
        loaded_owners.append(f'{vrom:08X}')
    check('complete live save retained',SAVE_RAM,saved);check('native callback retained',callback,CALLBACK)
    for at in guards:check('owned buffer and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    write(0x801458D0,segment)
    for at in reversed(allocations):call(0x8009C040,[at])
    return {'submenu_calls':calls,'submenu_assertions':assertions,'draws':draws,
        'save_unchanged':True,'allocations_released':True,'owners_loaded_from_cartridge':loaded_owners,
        'pak_operations_invoked':False,'ordinary_menu_entry':False,'requires_checkpoint_restore':True}
