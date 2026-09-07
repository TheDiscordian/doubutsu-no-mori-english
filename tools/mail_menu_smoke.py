"""Run original menu selectors on isolated RAM fixtures, without UI-flow claims."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_menu import (VROM,RAM,SIZE,BSS,SELECT,MAX_LABEL,FUNCTION_ENDS,definitions,
                       cases,relocated)
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    data,reloc = bytes.fromhex(request['data']),bytes.fromhex(request['relocation'])
    rows = definitions(data)
    if request['cases'] != cases(): raise ValueError('Native menu case matrix changed')
    read = debug.read_memory
    def write(address,value):
        debug.write_memory(address,value)
        record({'mail_menu_fixture_write':f'{address:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,address,expected):
        observed = read(address,len(expected))
        if observed != expected:
            record({'mail_menu_check':label,'assertion':'failed','address':f'{address:08X}',
                    'expected_sha256':sha256(expected),'observed_sha256':sha256(observed)})
            raise ValueError('Native mail menu mismatch: '+label)
        record({'mail_menu_check':label,'assertion':'passed','bytes':len(expected),'sha256':sha256(observed)})
    def call(address,args=(),expected=None,proof=None):
        result = debug.call(f'{address:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Menu call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    for address,value in request['guards'].items():
        check('native resident instruction guard',int(address,16),bytes.fromhex(value))
    original_save = read(SAVE_RAM,SAVE_BYTES)
    original_private,original_field = read(0x80136FD8,4),read(0x80136EA1,1)
    # The complete synthetic overlay structure is allocated; no fabricated
    # pointer relies on an unallocated 64 KiB prefix to reach its late fields.
    size = 0x1C760
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native mail-menu fixture allocation failed')
    base,overlay,tag = allocation+16,allocation+0xB040,allocation+0x1B780
    submenu,menu,private = allocation+0x1BAC0,allocation+0x1BB10,allocation+0x1BB70
    if base+SIZE+BSS+len(reloc)+16 != overlay:
        raise ValueError('Native tag loader scratch overlaps fixture')
    write(overlay,bytes(size-(overlay-allocation)))
    guards = (allocation,overlay-16,tag-16,submenu-16,menu-16,private-16,allocation+size-16)
    for address in guards: write(address,EDGE)
    write(TEST_STACK-0x800,EDGE)
    write(TEST_STACK+0x30,EDGE)
    call(0x800262D0,[VROM,VROM+SIZE,RAM,RAM+SIZE+BSS,base,base+SIZE+BSS,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    loaded = relocated(data,reloc,base)
    check('complete original tag relocation and cleared BSS',base,loaded)
    def native(function,args,expected):
        proof = loaded[function-RAM:FUNCTION_ENDS[function]-RAM]
        return call(base+function-RAM,args,expected,proof=(base+function-RAM,proof))
    write(submenu+0x2C,struct.pack('>I',overlay))
    write(overlay+0x106D0,struct.pack('>I',tag))
    write(tag+0x3C,struct.pack('>I',3))
    write(0x80136FD8,struct.pack('>I',private))
    letter = private+0x40A
    for case in request['cases']:
        mail = bytearray(164)
        mail[0:6],mail[18:24] = b'PLAYER',b'SENDER'
        mail[36:38] = case['present'].to_bytes(2,'big')
        mail[38:42] = bytes((case['font'],case['split'],0,0))
        # The marker case deliberately uses opaque non-text bytes. This test
        # checks menu discrimination, not envelope checksum/decoder acceptance.
        mail[42:] = bytes(range(122)) if case['split'] else b' '*122
        write(letter,mail)
        write(menu,struct.pack('>I',case['menu']))
        write(menu+0x38,struct.pack('>I',case['mode']))
        write(0x80136EA1,bytes((case['field'],)))
        native(SELECT,[submenu,menu,tag+8],case['expected'])
        check('complete letter retained by menu selection',letter,mail)
        record({'mail_menu_case_passed':case})
    for definition in rows:
        address = base+definition['pointer']-RAM if definition['count'] else 0
        native(MAX_LABEL,[address,definition['count']],definition['max_length'])
        record({'native_static_tag_label_maximum':definition['type'],'count':definition['count'],
                'length':definition['max_length']})
    check('original tag image remains unchanged',base,loaded)
    write(0x80136FD8,original_private)
    write(0x80136EA1,original_field)
    check('restored current-private pointer',0x80136FD8,original_private)
    check('restored field type',0x80136EA1,original_field)
    check('unchanged complete live save payload',SAVE_RAM,original_save)
    for address in guards: check('heap fixture guard',address,EDGE)
    check('lower call stack guard',TEST_STACK-0x800,EDGE)
    check('upper call stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,GUARD_WORD.to_bytes(4,'big')*4)
    call(0x8009C040,[allocation])
    return {'native_mail_menu_cases':len(request['cases']),'static_label_definitions':len(rows),
            'normal_menu_gameplay':False,'requires_checkpoint_restore':True}
