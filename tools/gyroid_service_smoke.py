"""Native complete gyroid responses, safe callback, and full font output."""
import struct

from aflib import sha256
from birthday_draw_scenario import CALLBACK
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from extended_font_test_scenario import texture_commands
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from submenu_text_scenario import LOADER_SHA
from gyroid_service_scenario import ROM_SHA
import gyroid_service as gyroid

EDGE=b'GYRO'*4
def words(*values):return struct.pack('>'+'I'*len(values),*values)


def exercise(debug,request,record):
    read=debug.read_memory;calls=assertions=0
    def write(at,data):
        debug.write_memory(at,data);record({'gyroid_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,value):
        nonlocal assertions
        actual=read(at,len(value));assertions+=1
        record({'gyroid_check':label,'address':f'{at:08X}','bytes':len(value),
            'assertion':'passed' if actual==value else 'failed',
            'expected_sha256':sha256(value),'observed_sha256':sha256(actual)})
        if actual!=value:raise ValueError('Native gyroid service mismatch: '+label)
    def call(at,args=(),proof=None):
        nonlocal calls
        result=debug.call(f'{at:08X}',list(args),verified_code=proof);calls+=1;record(result)
        return result['return_value']
    data=bytes.fromhex(request['owner']);reloc=bytes.fromhex(request['relocation']);loader=bytes.fromhex(request['loader'])
    if (request['rom_sha256']!=ROM_SHA or sha256(loader)!=LOADER_SHA
            or sha256(data)!='b5458f2112195fe92d1571396448d64814df7f9869f949258fea716808ec686d'
            or sha256(reloc)!='5e5b4495d5b40c6a595d52d29019f7521addbc32ba7d557bc7aba5a54466a8fa'
            or bytes.fromhex(request['matrix_callback'])!=CALLBACK):
        raise ValueError('Unapproved gyroid native fixture')
    saved=read(SAVE_RAM,SAVE_BYTES);price_at=0x8012AF0C;old_price=read(price_at,2);allocations=[]
    for size in (0x12000,0x10000):
        address=call(0x8009BFC0,[size])
        if address&15 or not MODULE_RAM+RESERVATION<=address<=0x80400000-size:
            raise ValueError('Gyroid fixture allocation failed')
        allocations.append(address)
    context,aux=allocations;overlay=context+16;menu=context+0x10800
    submenu=context+0x10880;game=context+0x10900;tag=context+0x10980
    base=aux+16;staging=aux+0x2000;callback=aux+0x2400
    graph=aux+0x3000;arena=aux+0x4000;arena_end=aux+0xFFF0
    sections=struct.unpack_from('>5I',reloc);spec=Image(gyroid.RAM,len(data),sections)
    guards=(context,overlay+0x10730,menu-16,menu+0x40,submenu-16,submenu+0x40,
        game-16,game+0x40,tag-16,tag+0x100,context+0x12000-16,aux,base+len(data),
        staging-16,staging+len(reloc),callback-16,callback+48,graph-16,graph+0x300,
        arena-16,arena_end,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:write(at,EDGE)
    call(0x800262D0,[gyroid.NEW_VROM,gyroid.NEW_VROM+len(data),gyroid.RAM,gyroid.RAM+len(data),
        base,staging,len(reloc)],(0x800262D0,loader))
    loaded=relocate_verified_data(spec,data,reloc,base)
    check('complete cartridge owner and old/new zeroed state',base,loaded)
    write(callback,CALLBACK);write(overlay,bytes(0x10730));write(menu,bytes(0x40))
    write(submenu,bytes(0x40));write(game,bytes(0x40));write(tag,bytes(0x100));write(graph,bytes(0x300))
    state=base+gyroid.STATE;message=state+gyroid.BUFFER
    write(submenu+0x2C,words(overlay));write(game,words(graph))
    write(overlay+0x106F0,words(state));write(overlay+0x106D0,words(tag));write(overlay+0x106B4,words(callback))
    write(state+0x20,b'OLD-MESSAGE!');write(state+0x2C,words(base));write(message+22,b'G'*10)
    snapshot=read(overlay,0x10730);proof=(base,loaded[:gyroid.SECTIONS[0]]);draws=[];compositions=[]
    cases=[(i,0) for i in range(12)]+[(11,65535)]
    for index,price in cases:
        write(price_at,struct.pack('>H',price))
        call(base+0x8088CCF4-gyroid.RAM,[submenu,index],proof)
        expected=gyroid.ROWS[index][1]
        if index==11:expected=gyroid.PREFIX+str(price).encode()+expected
        expected=expected.ljust(22,b' ')
        check('complete selected English response',message,expected)
        check('original message slot retained',state+0x20,b'OLD-MESSAGE!')
        check('native interrupt callback retained',state+0x2C,words(base))
        check('new message upper guard',message+22,b'G'*10)
        if index==11:check('native selected price cache',state+0x18,words(price))
        compositions.append({'state':index,'price':price if index==11 else None,'text':expected.decode().rstrip()})
        if index==6 or index==11 and price==65535:
            write(state+0x14,words(22))
            for offset in (0x290,0x2B0):write(graph+offset,words(arena_end-arena,arena,arena,arena_end))
            write(arena,bytes(arena_end-arena));before_state=read(state,80)
            call(base+0x8088D5D0-gyroid.RAM,[submenu,game,menu],proof)
            front,back=struct.unpack('>2I',read(graph+0x298,8))
            if not arena<front<back<arena_end:raise ValueError('Gyroid graphics escape the owned arena')
            output=read(arena,front-arena);cursor=0
            for char in expected:
                glyph=texture_commands(0x8013A680,char);at=output.find(glyph,cursor)
                if at<0:raise ValueError(f'Missing ordered gyroid glyph {char:02X} after {cursor:04X}')
                cursor=at+len(glyph)
            glyphs=sum(output[at:at+4]==bytes.fromhex('FD88005F') for at in range(0,len(output),8))
            if glyphs!=22:raise ValueError('Gyroid font omitted part of the expanded message')
            check('read-only drawing state',state,before_state)
            draws.append({'state':index,'glyphs':glyphs,'display_list_bytes':front-arena,'back_bytes':arena_end-back})
            record({'gyroid_native_draw':draws[-1]})
    write(price_at,old_price);check('complete live save restored',SAVE_RAM,saved)
    check('native code and old tables retained',base,loaded[:gyroid.STATE])
    check('English source pool retained',base+gyroid.STATE+80,loaded[gyroid.STATE+80:])
    check('read-only submenu context',overlay,snapshot);check('read-only native tag',tag,bytes(0x100))
    check('native callback retained',callback,CALLBACK)
    for at in guards:check('owned buffer and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    for at in reversed(allocations):call(0x8009C040,[at])
    return {'gyroid_calls':calls,'gyroid_assertions':assertions,'compositions':compositions,'draws':draws,
        'save_restored':True,'allocations_released':True,'owner_loaded_from_cartridge':True,
        'sales_invoked':False,'persistent_writes':False,'ordinary_menu_entry':False,'requires_checkpoint_restore':True}
