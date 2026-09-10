"""Actual cartridge birthday loader and full native glyph output in owned test RAM."""
import struct
from aflib import sha256
from birthday_screen import OWNER,RELOC,ASSET,RAM,START,DRAW_SHA,PROMPT,MONTHS
from birthday_draw_scenario import CALLBACK
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from extended_font_test_scenario import texture_commands
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE=b'BDAY'*4
def words(*v):return struct.pack('>'+'I'*len(v),*v)
def floats(*v):return struct.pack('>'+'f'*len(v),*v)


def exercise(debug,request,record):
    read=debug.read_memory;calls=assertions=0
    def write(at,data):
        debug.write_memory(at,data)
        record({'birthday_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,value):
        nonlocal assertions
        actual=read(at,len(value));assertions+=1
        record({'birthday_check':label,'address':f'{at:08X}',
            'assertion':'passed' if actual==value else 'failed','bytes':len(value),
            'expected_sha256':sha256(value),'observed_sha256':sha256(actual)})
        if actual!=value:raise ValueError('Native birthday mismatch: '+label)
    def call(at,args=(),proof=None):
        nonlocal calls
        result=debug.call(f'{at:08X}',list(args),verified_code=proof);calls+=1;record(result)
        return result['return_value']
    data,reloc,asset=(bytes.fromhex(request['images'][f'{v:08X}']) for v in (OWNER,RELOC,ASSET))
    if sha256(data[START:START+800])!=DRAW_SHA or bytes.fromhex(request['matrix_callback'])!=CALLBACK:
        raise ValueError('Unapproved native birthday code fixture')
    saved=read(SAVE_RAM,SAVE_BYTES)
    allocations=[]
    for size in (0x12000,0x10000):
        base=call(0x8009BFC0,[size])
        if base&15 or not MODULE_RAM+RESERVATION<=base<=0x80400000-size:
            raise ValueError('Birthday fixture allocation failed')
        allocations.append(base)
    context,aux=allocations
    overlay=context+0x10;menu=context+0x10800;submenu=context+0x10880
    state=context+0x10900;game=context+0x10940
    base=aux+0x10;staging=aux+0x1000;callback=aux+0x1200
    assets=aux+0x1800;graph=aux+0x7000;arena=aux+0x7800;arena_end=aux+0xFFF0
    sections=struct.unpack_from('>5I',reloc);spec=Image(RAM,sum(sections[:4]),sections)
    if base+spec.resident_bytes>staging-16 or assets+len(asset)>graph-16:
        raise ValueError('Birthday fixture ranges overlap')
    guards=(context,overlay+0x10730,menu-16,menu+0x40,submenu-16,submenu+0x40,
        state-16,state+8,game-16,game+0x40,context+0x12000-16,aux,base+spec.resident_bytes,
        staging-16,staging+len(reloc),callback-16,callback+48,assets-16,assets+len(asset),
        graph-16,graph+0x300,arena-16,arena_end,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:write(at,EDGE)
    call(0x800262D0,[OWNER,OWNER+len(data),RAM,RAM+spec.resident_bytes,base,staging,len(reloc)],
         (0x800262D0,bytes.fromhex(request['loader'])))
    loaded=relocate_verified_data(spec,data,reloc,base);check('complete cartridge owner and BSS',base,loaded)
    write(callback,CALLBACK);write(assets,asset);write(overlay,bytes(0x10730))
    write(menu,bytes(0x40));write(submenu,bytes(0x40));write(game,bytes(0x40));write(graph,bytes(0x300))
    write(submenu+0x2C,words(overlay));write(menu+0x28,words(assets));write(game,words(graph))
    write(overlay+0x10710,words(state));write(overlay+0x106B4,words(callback))
    snapshot=read(overlay,0x10730);draws=[]
    for month,day,selection in ((9,30,0),(2,29,1),(1,10,2)):
        date=struct.pack('>2HI',month,day,selection);write(state,date)
        for offset in (0x290,0x2B0):write(graph+offset,words(arena_end-arena,arena,arena,arena_end))
        write(arena,bytes(arena_end-arena))
        call(base+START,[submenu,menu,game],(base,loaded[:sections[0]]))
        front,back=struct.unpack('>2I',read(graph+0x298,8))
        if not arena+56<front<back<arena_end:raise ValueError('Birthday graphics escape the owned arena')
        output=read(arena,front-arena)
        expected=PROMPT+MONTHS[month-1]+f'{day:02}'.encode()+b'OK'
        cursor=0
        for char in expected:
            glyph=texture_commands(0x8013A680,char)
            at=output.find(glyph,cursor)
            if at<0:raise ValueError(f'Missing ordered birthday glyph {char:02X} after {cursor:04X}')
            cursor=at+len(glyph)
        glyphs=sum(output[at:at+4]==bytes.fromhex('FD88005F') for at in range(0,len(output),8))
        if glyphs!=len(expected):raise ValueError('Birthday draws unexpected extra or missing glyphs')
        check('native background segment',arena,words(0xDB060030,assets))
        check('read-only selected birthday',state,date);check('read-only submenu context',overlay,snapshot)
        check('complete English strings and unchanged asset',assets,asset)
        draws.append({'month':month,'day':day,'selection':selection,'glyphs':glyphs,
            'display_list_bytes':front-arena,'back_bytes':arena_end-back,'complete_english':True})
        record({'birthday_native_draw':draws[-1]})
    check('complete live save retained',SAVE_RAM,saved);check('complete birthday code retained',base,loaded)
    check('native callback retained',callback,CALLBACK)
    for at in guards:check('owned buffer and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    for at in reversed(allocations):call(0x8009C040,[at])
    return {'birthday_calls':calls,'birthday_assertions':assertions,'draws':draws,
        'save_unchanged':True,'allocations_released':True,'renderer_loaded_from_cartridge':True,
        'native_matrix_callback_copied':True,'ordinary_menu_entry':False,'requires_checkpoint_restore':True}
