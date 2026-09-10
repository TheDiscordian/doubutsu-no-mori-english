"""Exercise the actual cartridge editor and matcher in isolated owned RAM."""
import struct
from aflib import sha256
from apology_overlay import APPROVED, RAM, previous
from hboard_overlay import Image
from apology_targets import TARGETS
from npc_mail_show import relocate_verified_data
from extended_font_test_scenario import texture_commands
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
import resetti_replies as actor_spec

EDGE=b'APOL'*4
def words(*v):return struct.pack('>'+'I'*len(v),*v)
def half(*v):return struct.pack('>'+'h'*len(v),*v)
def floating(v):return struct.unpack('>I',struct.pack('>f',v))[0]


def exercise(debug,request,record):
    read=debug.read_memory;assertions=0;calls=0
    def write(at,data):
        debug.write_memory(at,data)
        record({'apology_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,data):
        nonlocal assertions
        actual=read(at,len(data));assertions+=1
        record({'apology_check':label,'address':f'{at:08X}','bytes':len(data),
                'expected_sha256':sha256(data),'observed_sha256':sha256(actual),
                'assertion':'passed' if actual==data else 'failed'})
        if actual!=data:raise ValueError('Apology native mismatch: '+label)
    def call(at,args=(),expect=None,proof=None):
        nonlocal calls
        value=debug.call(f'{at:08X}',list(args),verified_code=proof);record(value);calls+=1
        if expect is not None and value['return_value']!=expect:
            raise ValueError(f'Apology call {at:08X} returns {value["return_value"]}, expected {expect}')
        return value['return_value']
    saved=read(SAVE_RAM,SAVE_BYTES);size=0x30000
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Apology native fixture allocation failed')
    # Each loader owns image + complete BSS + relocation staging. The submenu
    # owner's 67,376-byte BSS is distinct from our synthetic editing context.
    base,owner_base,actor_base=allocation+16,allocation+0x6400,allocation+0x1A000
    ovl,submenu,menu,ed,text=allocation+0x1B000,allocation+0x2B800,allocation+0x2B900,allocation+0x2BA00,allocation+0x2BB00
    actor,staging,game,graph,gfx=allocation+0x2BC00,allocation+0x2C600,allocation+0x2C800,allocation+0x2C900,allocation+0x2D000
    loaded={}
    def load(vrom,relv,ram,destination):
        data,reloc=(bytes.fromhex(request['images'][f'{v:08X}']) for v in (vrom,relv))
        sections=struct.unpack_from('>5I',reloc);resident=sum(sections[:4])
        spec=Image(ram,resident,sections)
        expected=relocate_verified_data(spec,data,reloc,destination)
        call(0x800262D0,[vrom,vrom+len(data),ram,ram+resident,destination,destination+resident,len(reloc)],
             proof=(0x800262D0,bytes.fromhex(request['loader'])))
        check('complete cartridge image and relocation',destination,expected)
        loaded[vrom]=(expected,sections)
    ranges=[]
    for vrom,relv,start in ((previous.NEW_VROM,previous.NEW_RELOCATION,base),
            (previous.OWNER,previous.OWNER_RELOC,owner_base),(actor_spec.VROM,actor_spec.RELOC_VROM,actor_base)):
        rel=bytes.fromhex(request['images'][f'{relv:08X}'])
        ranges.append((start,start+sum(struct.unpack_from('>4I',rel))+len(rel)))
    if any(end+16>next_start-16 for (_,end),(next_start,_) in zip(ranges,ranges[1:])) or ranges[-1][1]+16>ovl-16:
        raise ValueError('Native apology loader workspace overlaps a fixture region')
    guards=(allocation,*(end for _,end in ranges),owner_base-16,actor_base-16,ovl-16,
            ovl+0x10700,submenu-16,submenu+0x40,menu-16,menu+0x48,ed-16,ed+0x34,
            text-16,text+10,actor-16,actor+0x958,staging-16,staging+32,game-16,
            graph-16,graph+0x300,gfx-16,gfx+0x1000,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x40)
    for at in guards:write(at,EDGE)
    load(previous.NEW_VROM,previous.NEW_RELOCATION,RAM,base)
    load(previous.OWNER,previous.OWNER_RELOC,0x8085BAC0,owner_base)
    load(actor_spec.VROM,actor_spec.RELOC_VROM,actor_spec.RAM,actor_base)
    expected=loaded[previous.NEW_VROM][0]
    native_proof=(base,expected[:0x33C0])
    appended=(base+APPROVED['prefix_bytes'],expected[APPROVED['prefix_bytes']:APPROVED['code_end']])
    actor_proof=(actor_base,loaded[actor_spec.VROM][0][:3280])
    write(ovl,bytes(0x10700));write(submenu,bytes(0x40));write(menu,bytes(0x48));write(ed,bytes(0x34))
    write(submenu+0x2C,words(ovl));write(menu+0x38,words(3,10,text))
    write(ovl+0x101E0,words(3));write(ovl+0x101E8,words(text))
    write(ovl+0x106E0,words(ed));write(ovl+0x106B0,words(owner_base+0x8085D4D4-0x8085BAC0))
    symbols={name:base+at for name,at in APPROVED['symbols'].items()}
    def init(kind=3):
        write(ovl+0x101E0,words(kind));write(text,b' '*10)
        call(symbols['af_apology_editor_init'],[submenu,menu],proof=appended)
        check('native initial cursor/capacity/row/length',ed+0x16,half(0,10,1,0))
        write(ed+4,b'\1')
    def command(number,code=0):
        write(ed+0x11,bytes((number,0,code)))
        call(symbols['af_apology_editor_command'],[submenu,menu],proof=appended)
    cuts=read(0x80106AF4,256)
    font=request['module']['extended_font']['font']
    font_base=int.from_bytes(read(int(request['module']['symbols']['af_extended_font_image'],16),4),'big')
    texture=font_base+font['symbols']['af_font_resource']+64
    for id,(_,_,target,_) in TARGETS.items():
        init()
        for token in (list(b'U R my ')+[0x84,ord('!')] if id.endswith('048E') else list(b'Reset ')+[0x85,32,0x81]):
            command(8,token)
        check('complete entered apology and adjacent guard',text,target+EDGE)
        check('complete ten-byte cursor and length',ed+0x16,half(10,10,1,10))
        command(8,ord('X'));check('full input rejects overrun',text,target+EDGE)
        command(1)
        boundary=9 if id.endswith('048E') else 8
        check('left moves to complete token boundary',ed+0x16,half(boundary))
        if boundary==9:
            call(symbols['af_apology_editor_exchange'],[ed],0xFFFFFFFF,appended)
            command(6);check('backspace removes whole sun and keeps exclamation',text,b'U R my !  '+EDGE)
            command(8,0x84)
        else:
            command(4);command(6);check('backspace removes whole skull',text,b'Reset =   '+EDGE)
            command(8,0x81)
        check('symbol reinsertion restores exact target',text,target+EDGE)
        write(staging,bytes(32))
        call(symbols['af_apology_editor_cursor'],[ed,staging,staging+2,10],proof=appended)
        check('native cursor output remains byte indexed',staging,half(10,0))
        width=sum(12-cuts[c] for c in target if c not in (0x80,0xA7,0xBA))+12
        call(0x800902CC,[text,10,1],(width+1)&~1)
        command(5);check('Done follows original menu close callback',menu+0x30,words(4,6))
        check('Done retains complete apology',text,target+EDGE)
        state=bytearray(0x958);state[0x94C:0x956]=read(text,10);state[0x956]=int(id[7:],16)-0x484
        write(actor,state)
        call(actor_base+0x809B4D08-actor_spec.RAM,[actor],0,actor_proof)
        check('exact comparison retains actor and reply',actor,state)
        state[0x955]=ord('Z');write(actor,state)
        call(actor_base+0x809B4D08-actor_spec.RAM,[actor],2,actor_proof)
    # Execute the real keyboard key drawer, which traverses the installed hook.
    # No rendered window or screenshot is needed: inspect emitted texture commands.
    for key,slot in ((0x84,2),(0x81,4),(0x85,None)):
        write(staging,bytes((key,)));write(game,words(graph));write(graph,bytes(0x300))
        write(gfx,bytes(0x1000));write(graph+0x298,words(gfx));write(graph+0x29C,words(gfx+0xF00))
        call(base+0x80887768-RAM,[game,staging,floating(100),floating(100),floating(1),0],proof=native_proof)
        end=int.from_bytes(read(graph+0x298,4),'big')
        if not gfx<end<gfx+0x800:raise ValueError('Apology key drawing escapes the owned display list')
        commands=texture_commands(texture if slot is not None else 0x8013A680,slot if slot is not None else ord('='))
        output=read(gfx,end-gfx)
        if commands not in output:raise ValueError('Apology key uses the wrong glyph texture')
        record({'apology_key_draw':key,'expected_glyph_slot':slot,'display_list_bytes':len(output),'passed':True})
    init(0);command(8,0x84)
    check('ordinary name retains native Japanese punctuation',text,b'\x84'+b' '*9+EDGE)
    call(symbols['af_apology_editor_destruct'],[submenu],proof=appended)
    check('original destructor clears editor ownership',ovl+0x106E0,words(0))
    check('complete live save retained',SAVE_RAM,saved)
    check('editor native instructions retained',base,native_proof[1])
    check('appended editor instructions retained',appended[0],appended[1])
    for at in guards:check('owned buffer and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'apology_calls':calls,'apology_assertions':assertions,'exact_targets':2,'native_key_draws':3,
            'save_unchanged':True,'fixture_released':True,'code_uploaded':False,'requires_checkpoint_restore':True}
