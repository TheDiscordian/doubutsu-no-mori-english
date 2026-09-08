"""Isolated native shop preparation and insertion using cartridge-loaded actors."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from shop_units import SHOPS,FIRST,END,PRICE_BIASES,verify_shop,unit_id
from textcodec import tokenize

WINDOW,EDGE=0x80142410,b'EDGE'*4
ITEMS=(0x1000,0x2000,0x2400,0x2200,0x2F00,0x2300,0x2901,0x2900)


def relocated(spec,data,reloc,base):
    verify_shop(spec,data,reloc)
    return relocate_verified_data(spec,data,reloc,base,
                                  address_constants=(PRICE_BIASES[spec.vrom],))


def exercise(debug,request,record):
    read=debug.read_memory;assertions=0;preparations=0;insertions=0
    def write(at,value):
        debug.write_memory(at,value)
        record({'shop_unit_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        nonlocal assertions
        actual=read(at,len(expected))
        record({'shop_unit_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Native shop-unit mismatch: '+label)
        assertions+=1
    def call(at,args=(),expected=None,proof=None):
        result=debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Native shop-unit return differs')
        return result['return_value']
    def insert(data,cursor,entry,code,value):
        nonlocal insertions
        tokens=[t for t in tokenize(entry,request['info']) if t.kind=='cmd' and t.data[1]==code]
        if len(tokens)!=1:raise ValueError('Shop fixture requires exactly one selected field')
        token=tokens[0];write(cursor,struct.pack('>I',token.offset));write(WINDOW+0x28C,bytes(4))
        call(0x800A21C0,[WINDOW,cursor],0)
        expected=entry[:token.offset]+value+entry[token.offset+2:]
        header=read(data,16)
        if struct.unpack_from('>I',header,8)[0]!=len(expected):
            raise ValueError('Shop insertion length differs')
        check('complete field insertion and surrounding text',data+16,expected)
        insertions+=1
        return expected

    saved=read(SAVE_RAM,SAVE_BYTES)
    entries=[bytes.fromhex(value) for value in request['units']]
    for name,spec in SHOPS.items():
        source=request['actors'][name]
        original,reloc=bytes.fromhex(source['data']),bytes.fromhex(source['reloc'])
        verify_shop(spec,original,reloc)
        size=0x8000;allocation=call(0x8009BFC0,[size])
        if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
            raise ValueError('Shop fixture allocation failed')
        base,data,staging,cursor=(allocation+o for o in (0x10,0x7000,0x7480,0x74C0))
        relocation_buffer=base+spec.resident_bytes
        if relocation_buffer+len(reloc)+16>data-16:
            raise ValueError('Shop fixture relocation workspace overlaps its message buffer')
        edges=(allocation,relocation_buffer+len(reloc),data-16,data+0x410,staging-16,staging+32,
               cursor-16,cursor+16,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x30)
        for at in edges:write(at,EDGE)
        call(0x800262D0,[spec.vrom,spec.vrom+spec.file_bytes,spec.ram,spec.ram+spec.resident_bytes,
                        base,relocation_buffer,len(reloc)],
             proof=(0x800262D0,bytes.fromhex(request['loader'])))
        loaded=relocated(spec,original,reloc,base)
        check('complete original cartridge actor and relocation',base,loaded)
        check('complete original relocation workspace',relocation_buffer,reloc)
        proof=(base,loaded[:spec.sections[0]])
        if name=='cranny':
            for index,value in enumerate(entries):
                write(staging,b'G'*32);call(0x800C3F70,[staging,10,FIRST+index])
                check('complete counter load including explicit empty values',staging,value.ljust(10,b' ')+b'G'*22)
        write(WINDOW+12,struct.pack('>I',data))
        for item in ITEMS:
            # The independent native name load supplies only the compatibility
            # field expected from this unchanged preparer, not a wider-name claim.
            write(staging,b'G'*32);call(0x80096740,[staging,item])
            item_name=read(staging,10)
            check('native name loader preserves adjacent staging',staging+10,b'G'*22)
            for count in (1,2,15):
                selected=unit_id(spec,original,reloc,item,count);value=entries[selected-FIRST]
                before=read(WINDOW,0x330)
                call(base+spec.handler-spec.ram,[item,count],proof=proof)
                expected=bytearray(before)
                expected[0x38+70:0x38+80]=str(count).encode().ljust(10,b' ')
                expected[0x38+80:0x38+90]=value.ljust(10,b' ')
                expected[0x114:0x11E]=item_name
                check('preparer changes only count unit and item compatibility fields',WINDOW,expected)
                check('complete ten-byte native local',TEST_STACK-56+0x2C,value.ljust(10,b' '))
                fixture=b'N=\x7f\x2b U=\x7f\x2c!\x7f\x00'
                write(data,struct.pack('>4I',1,0,len(fixture),0)+fixture)
                after=insert(data,cursor,fixture,0x2C,value)
                insert(data,cursor,after,0x2B,str(count).encode())
                record({'shop_unit_case':name,'item':f'{item:04X}','count':count,
                        'string_id':f'{selected:04X}','empty_counter':not value,'passed':True})
                preparations+=1
        # Full installed shop wording intentionally omits the unit field, just
        # like its supplied English reference. Do not reinsert it for visibility.
        for number,raw in request['messages'].items():
            entry=bytes.fromhex(raw);id=int(number,16)
            call(0x8009E558,[data,id,0],1)
            check('complete unchanged shop message from cartridge',data,struct.pack('>4I',1,id,len(entry),0)+entry)
            insert(data,cursor,entry,0x2B,b'15')
        check('complete saved game retained',SAVE_RAM,saved)
        check('complete actor including BSS retained',base,loaded)
        check('complete relocation workspace retained',relocation_buffer,reloc)
        for at in edges:check('heap and native stack guard',at,EDGE)
        check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
        call(0x8009C040,[allocation])
    return {'shop_unit_native_preparations':preparations,'shop_unit_insertions':insertions,
            'shop_unit_complete_loads':120,'shop_unit_assertions':assertions,
            'normal_transactions':False,'requires_checkpoint_restore':True}
