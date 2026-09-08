"""Complete fortune snapshots in owned N64 heap memory, with restored state."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_generate_probe import relocate
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    save = debug.read_memory(SAVE_RAM,SAVE_BYTES)
    rng = debug.read_memory(0x8003C590,4)
    free_strings = debug.read_memory(0x80140680,200)
    code,report,module = bytes.fromhex(request['code']),request['probe'],request['module']
    def write(at,value): debug.write_memory(at,value)
    def check(label,at,expected):
        actual = debug.read_memory(at,len(expected))
        record({'fortune_slip_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual != expected: raise ValueError('Native fortune-slip check failed: '+label)
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Fortune-slip call returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    size = 0x3000
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native fortune-slip fixture allocation failed')
    base = allocation+16
    words = (base+len(code)+31)&~15
    choice = words+1104
    capital,mail,work = choice+32,choice+64,choice+256
    if work+5280+16 > allocation+size-16: raise ValueError('Fortune-slip fixture exceeds owned allocation')
    guards = (allocation,words-16,words+1088,choice+16,capital+16,mail+176,work+5280,allocation+size-16)
    for at in guards: write(at,EDGE)
    write(TEST_STACK-0xA00,EDGE);write(TEST_STACK+0x30,EDGE)
    loaded = relocate(code,report,module,base,fortune_slip=True)
    write(base,loaded);write(words,bytes.fromhex(request['words']))
    for case in request['cases']:
        selected = bytes.fromhex(case['choice'])
        write(choice,selected);write(capital,case['capital'].to_bytes(4,'big'))
        write(mail,bytes(range(164))+b'!'*12);write(work,b'!'*5280)
        call(base+report['symbols']['af_fortune_slip_create'],
             [mail,164,choice,words,1088,capital,work],1,(base,loaded))
        check('complete saved slip and metadata',mail,bytes.fromhex(case['mail'])+b'!'*12)
        check('complete English text',work+560+3552,bytes.fromhex(case['text']))
        check('selected values retained',choice,selected)
        check('capital state',capital,case['capital'].to_bytes(4,'big'))
        for at in guards: check('owned allocation guard',at,EDGE)
    bad_choices = [bytes((16 if i == bad else 0 for i in range(4)))+bytes(4) for bad in range(4)]
    bad_choices += [bytes(4)+bytes((4,0,0,0)),bytes(4)+bytes((0,3,0,0)),
                    bytes(6)+bytes((1,0)),bytes(6)+bytes((0,1))]
    for selected in bad_choices:
        write(choice,selected);write(capital,b'\0\0\0\1');write(mail,bytes(range(164)))
        call(base+report['symbols']['af_fortune_slip_create'],
             [mail,164,choice,words,1088,capital,work],0,(base,loaded))
        check('rejected choice retains full mail',mail,bytes(range(164)))
        check('rejected choice retains capital',capital,b'\0\0\0\1')
    config = 0x80194924
    check('catalog configuration',config,bytes.fromhex('03000000'))
    write(config,bytes(4));write(choice,bytes(8))
    call(base+report['symbols']['af_fortune_slip_create'],
         [mail,164,choice,words,1088,capital,work],0,(base,loaded))
    check('disabled catalog retains full mail',mail,bytes(range(164)))
    check('disabled catalog retains capital',capital,b'\0\0\0\1')
    write(config,bytes.fromhex('03000000'))
    for case in request['old_cases']:
        wire = bytes.fromhex(case['wire']);write(mail,wire)
        call(int(module['symbols']['af_mail_restore'],16),[work+560+3552,mail,122,work+560],1)
        check('old catalog complete restored text',work+560+3552,bytes.fromhex(case['text']))
        check('old saved snapshot retained',mail,wire)
    check('restored catalog configuration',config,bytes.fromhex('03000000'))
    check('complete creator code retained',base,loaded)
    check('complete phrase resource retained',words,bytes.fromhex(request['words']))
    check('native RNG unchanged',0x8003C590,rng)
    check('native handbill fields unchanged',0x80140680,free_strings)
    check('complete live save unchanged',SAVE_RAM,save)
    for at in guards: check('final allocation guard',at,EDGE)
    check('lower stack guard',TEST_STACK-0xA00,EDGE)
    check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'native_fortune_slips':len(request['cases']),'rejected_choices':len(bad_choices),
            'old_catalog_reads':len(request['old_cases']),'native_actor_hook_installed':False,
            'requires_checkpoint_restore':True}
