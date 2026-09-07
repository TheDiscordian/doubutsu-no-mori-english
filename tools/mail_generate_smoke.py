"""Isolated native generation transaction and capture tests, never real saves."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_generate_probe import relocate
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    original_save = debug.read_memory(SAVE_RAM,SAVE_BYTES)
    code,report,module = bytes.fromhex(request['code']),request['probe'],request['module']
    def write(at,value):
        debug.write_memory(at,value)
        record({'generation_fixture_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        value = debug.read_memory(at,len(expected))
        record({'generation_check':label,'address':f'{at:08X}',
                'assertion':'passed' if value == expected else 'failed','bytes':len(value),
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('Native generation check failed: '+label)
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native generation {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    # One allocation includes every byte of code and data. No native save/global
    # field is substituted to exercise these purely caller-owned transactions.
    size = 0x2000
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native generation fixture allocation failed')
    base = allocation+16
    capture = (base+len(code)+31)&~15
    selection,mail,work = capture+384,capture+416,capture+608
    input_text = work+4736
    if input_text+48 > allocation+size-16: raise ValueError('Generation fixture overlaps its guards')
    guards = (allocation,capture-16,selection-16,mail-16,work-16,work+4720,input_text+32,allocation+size-16)
    for at in guards: write(at,EDGE)
    write(TEST_STACK-0xA00,EDGE)
    write(TEST_STACK+0x30,EDGE)
    loaded = relocate(code,report,module,base)
    write(base,loaded)
    check('complete original generation code',base,loaded)
    def native(name,args,expected=None):
        return call(base+report['symbols'][name],args,expected,proof=(base,loaded))
    state = bytearray(368)
    write(capture,b'!'*368)
    native('af_mail_capture_reset',[capture])
    check('complete capture reset',capture,state)
    for slot,size_field in [(i,i%17) for i in range(20)]+[(17,i) for i in range(17)]:
        value = (b'field with space').ljust(16,b' ')[:size_field]
        write(input_text,value.ljust(32,b'!'))
        native('af_mail_capture_set',[capture,slot,input_text,size_field,slot%5],1)
        valid = int.from_bytes(state[:4],'big')|(1<<slot)
        state[:4] = valid.to_bytes(4,'big')
        state[8+slot*18:8+(slot+1)*18] = bytes((size_field,slot%5))+value.ljust(16,b'\0')
        check('full capture and other slots',capture,state)
        check('capture source retained',input_text,value.ljust(32,b'!'))
    for value,length,article in ((b'\x7f',1,0),(b'\x80',1,0),(b'x'*17,17,0),(b'x',1,5)):
        write(input_text,value.ljust(32,b'!'))
        native('af_mail_capture_set',[capture,17,input_text,length,article],0)
        state[:4] = (int.from_bytes(state[:4],'big')&~(1<<17)).to_bytes(4,'big')
        check('invalid replacement cannot reuse old slot',capture,state)
    native('af_mail_capture_set',[capture,20,input_text,1,0],0)
    check('invalid index retains capture',capture,state)
    for case in request['cases']:
        write(capture,bytes.fromhex(case['capture']))
        write(selection,bytes.fromhex(case['selection'])+b'!!')
        write(mail,bytes(range(164))+b'!'*12)
        write(work,b'!'*4720)
        native('af_mail_generate',[mail,164,capture,selection,work],int(case['success']))
        check('complete published or retained letter',mail,bytes.fromhex(case['mail'])+b'!'*12)
        check('complete retained capture and capital state',capture,bytes.fromhex(case['after_capture']))
        check('immutable selection',selection,bytes.fromhex(case['selection'])+b'!!')
        if case['success']: check('complete English generated text',work+3552,bytes.fromhex(case['text']))
        for at in guards: check('allocation guard',at,EDGE)
        record({'native_generation_case':case['label'],'success_expected':case['success'],'passed':True})
    case = next(row for row in request['cases'] if row['success'])
    write(capture,bytes.fromhex(case['capture']))
    write(selection,bytes.fromhex(case['selection']))
    write(mail,bytes(range(164)))
    check('original catalog configuration',request['configuration_ram'],bytes.fromhex(request['configuration']))
    write(request['configuration_ram'],bytes(4))
    native('af_mail_generate',[mail,164,capture,selection,work],0)
    check('disabled resource retains letter',mail,bytes(range(164)))
    check('disabled resource retains capture',capture,bytes.fromhex(case['capture']))
    write(request['configuration_ram'],bytes.fromhex(request['configuration']))
    check('restored catalog configuration',request['configuration_ram'],bytes.fromhex(request['configuration']))
    check('original generation code retained',base,loaded)
    check('entire live save payload unchanged',SAVE_RAM,original_save)
    check('lower stack guard',TEST_STACK-0xA00,EDGE)
    check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'native_generation_cases':len(request['cases']),'native_capture_cases':42,
            'production_generation_enabled':False,'requires_checkpoint_restore':True}
