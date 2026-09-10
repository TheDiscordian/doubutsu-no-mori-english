"""Execute installed cartridge code in one reusable, isolated test allocation."""
import struct
from pathlib import Path
from dataclasses import replace
from aflib import sha256
from accent_mail_overlays import Overlay,FONT_POINTER
from accent_mail_font import HOOKS
from extended_font_cartridge import relocate as relocate_font
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_record import Record,Field,pack
from accent_mail_catalog import templates
from accent_mail_format import format_letter
from audit_mail_templates import template_fields

EDGE=b'ACNT'*4
def words(*v):return struct.pack('>'+'I'*len(v),*v)


def exercise(debug,request,record):
    read=debug.read_memory;calls=assertions=0;loaded_proof=None
    def write(at,data):
        debug.write_memory(at,data);record({'accent_write':f'{at:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,at,data):
        nonlocal assertions
        actual=read(at,len(data));assertions+=1
        record({'accent_check':label,'address':f'{at:08X}','bytes':len(data),
                'expected_sha256':sha256(data),'observed_sha256':sha256(actual),
                'assertion':'passed' if actual==data else 'failed'})
        if actual!=data:raise ValueError('Native accent mismatch: '+label)
    def call(at,args=(),expect=None):
        nonlocal calls
        proof=loaded_proof if loaded_proof and loaded_proof[0]<=at<loaded_proof[0]+len(loaded_proof[1]) else None
        if f'{at:08X}' in request['boot_helpers']:
            proof=(at,bytes.fromhex(request['boot_helpers'][f'{at:08X}']))
        value=debug.call(f'{at:08X}',list(args),verified_code=proof);record(value);calls+=1
        if expect is not None and value['return_value']!=expect:
            raise ValueError(f'Native accent call {at:08X} returned {value["return_value"]}, expected {expect}')
        return value['return_value']
    module=request['module'];font=module['extended_font']['font'];blob=bytes.fromhex(request['font_blob'])
    base=int.from_bytes(read(FONT_POINTER,4),'big')
    image=blob[:font['bytes']];fontrel=blob[font['bytes']:]
    expected=relocate_font(image,fontrel,base,mail_literals=True)
    immutable=sum(struct.unpack_from('>3I',fontrel))
    check('complete startup-owned immutable font and mail code',base,expected[:immutable])
    for address,(_,_,name) in HOOKS.items():
        target=base+font['symbols'][name]
        check('installed resident mail entry',address,words(0x08000000|((target>>2)&0x3FFFFFF),0))
    saved=read(SAVE_RAM,SAVE_BYTES);size=0x14000
    allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Native accent fixture allocation failed before any test writes')
    code=allocation+16;zone_end=allocation+0xF100
    capture=allocation+0xF120;selection=allocation+0xF2B0;text=allocation+0xF300
    mail=allocation+0xF400;work=allocation+0xF500
    wire=allocation+0x10800;native_record=allocation+0x10900;notice=allocation+0x10B00
    output=allocation+0x10C00
    guards=(allocation,zone_end,capture+368,selection+16,text+64,mail+164,
            work+4720,wire+128,native_record+384,notice+96,output+1040,
            allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x40)
    if code+max(len(bytes.fromhex(r['image']))+len(bytes.fromhex(r['relocations'])) for r in request['images'].values())>zone_end:
        raise ValueError('Native accent image and relocation exceed the disjoint test region')
    for at in guards:write(at,EDGE)
    catalog=Path('build/accent-mail-catalog/catalog.bin').read_bytes()
    def load(kind):
        nonlocal loaded_proof
        item=request['images'][kind];data=bytes.fromhex(item['image']);reloc=bytes.fromhex(item['relocations'])
        sections=struct.unpack_from('>5I',reloc);spec=Overlay(item['overlay']['ram'],len(data),sections)
        expected=relocate_verified_data(spec,data,reloc,code)
        call(0x80026B44,[code,item['vrom'],len(data)],0)
        call(0x80026B44,[code+len(data),item['relocation_vrom'],len(reloc)],0)
        call(0x8002B9C0,[code,code+len(data),spec.ram])
        call(0x8002FE00,[code,len(data)]);call(0x80034CE0,[code,len(data)])
        check('complete cartridge-loaded '+kind,code,expected)
        loaded_proof=(code,expected)
        return item['overlay']
    def check_letter(record_value,at):
        reference=format_letter(record_value,templates(catalog,record_value))
        chunks=(reference.header,reference.body,reference.footer)
        offsets=[0,0,0];payload=b''
        for index in ((0,1,2) if record_value.kind else (0,2,1)):
            offsets[index]=len(payload);payload+=chunks[index]
        expected=struct.pack('>7H2B',*offsets,*(len(s) for s in chunks),reference.header_split,
                             int(reference.final_capital),0)+payload.ljust(1024,b'\0')
        check('complete native English letter',at,expected)
    names=(b'caf\x80\x7c shirt',b'Pok\x80\x7cmon Pikachu',b'Caf\x80\x7c K.K.',b'Se\x80\x87or K.K.')
    owner=load('creator')
    seed=Record(5,0,(2,),())
    used=sorted(set().union(*(template_fields(p) for p in templates(catalog,seed).parts)))
    item_slot=7
    if item_slot not in used:raise ValueError('Native sale test lost its complete item field')
    for index,name in enumerate(names):
        fields=tuple((i,Field(name.ljust(16,b' ') if i==item_slot else b'friend')) for i in used)
        value=replace(seed,fields=fields)
        captured=bytearray(words(sum(1<<i for i in used),0)+bytes(360))
        for i,field in fields:
            captured[8+i*18:26+i*18]=bytes((len(field.text),field.article))+field.text.ljust(16,b'\0')
        write(capture,bytes(captured));write(text,name.ljust(16,b' '))
        call(code+owner['symbols']['af_mail_capture_set'],[capture,item_slot,text,16,0],1)
        check('complete native accented capture',capture,bytes(captured))
        write(selection,struct.pack('>HBB5H',4,0,0,2,0,0,0,0))
        write(mail,b'!'*164)
        call(code+owner['symbols']['af_mail_generate'],[mail,164,capture,selection,work],1)
        expected_mail=bytearray(b'!'*164);expected_mail[39]=128;expected_mail[42:]=pack(value)
        check('complete generated snapshot and metadata',mail,bytes(expected_mail))
        check_letter(value,work+3552)
        call(code+owner['symbols']['af_notice_item_article'],[(0x24A8,0x2505,0x2A31,0x2A33)[index],text],(1,1,0,0)[index])
    bad_before=read(capture,368);write(text,b'\x80')
    call(code+owner['symbols']['af_mail_capture_set'],[capture,item_slot,text,1,0],0)
    bad=bytearray(bad_before);struct.pack_into('>I',bad,0,int.from_bytes(bad[:4],'big')&~(1<<item_slot))
    check('invalid capture clears only its validity bit',capture,bytes(bad))
    treasure=Record(4,0,(0x1F0,),((1,Field(b'Bob')),(2,Field(names[-1],0)),(3,Field(b'1')),(4,Field(b'2'))))
    write(wire,pack(treasure));call(int(module['symbols']['af_mail_record_unpack'],16),[native_record,wire,122,4],1)
    before_record=read(native_record,384);write(notice,b'!'*96)
    call(code+owner['symbols']['af_notice_treasure_pack'],[notice,96,native_record],1)
    check('notice pack preserves original input record',native_record,before_record)
    treasure=replace(treasure,catalog=5);payload=pack(treasure)
    check('complete native notice envelope',notice,b'\x7fBN\x01'+payload[:92])
    call(code+owner['symbols']['af_notice_treasure_decode_parts'],[work,output,wire,notice,96],1)
    check_letter(treasure,output)
    owner=load('notice')
    call(code+owner['symbols']['af_notice_treasure_decode_parts'],[work,output,wire,notice,96],1)
    check_letter(treasure,output)
    owner=load('event');local=owner['accent_mail']['previous_overlay']['creator_offset']
    write(text,names[0].ljust(16,b' '));write(capture,bytes(captured))
    call(code+local+owner['creator']['symbols']['af_mail_capture_set'],[capture,item_slot,text,16,0],1)
    write(selection,struct.pack('>HBB5H',2,0,0,2,0,0,0,0))
    call(code+local+owner['creator']['symbols']['af_mail_generate'],[mail,164,capture,selection,work],1)
    fields=tuple((i,Field(names[0].ljust(16,b' ') if i==item_slot else b'friend')) for i in used)
    value=replace(seed,fields=fields);check('sale-event snapshot uses immutable accent catalogue',mail+42,pack(value))
    check_letter(value,work+3552)
    check('final complete cartridge code retained',*loaded_proof)
    for at in guards:check('retained allocation/stack guard',at,EDGE)
    check('complete saved payload unchanged',SAVE_RAM,saved)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    check('startup owner survives fixture release',FONT_POINTER,words(base))
    return {'accent_mail':'passed','native_calls':calls,'memory_assertions':assertions,
        'allocated_test_bytes':size,'image_uploads':0,'saved_layout_changed':False,'requires_checkpoint_restore':True}
