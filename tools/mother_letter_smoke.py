"""Actual cartridge creator, native Mom delivery, and complete reader batch."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import QUEUE,HOME_MAILBOX,HOME_STRIDE
from mother_letters import START,POST,STAGING
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'mother_letter_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('Native Mom-letter mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None):
        result = debug.call(f'{at:08X}',args);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Mom call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module = request['module'];symbols = module['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    check('installed Mom creator and both delivery gates',START,bytes.fromhex(request['code']))
    check('no previous creator session',session,bytes(4))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in
                      ((STAGING,164),(capital,4),(0x8003C590,4),(0x80140680,200),(MODULE_RAM+68,4))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-8192:
        raise ValueError('Mom-letter fixture allocation failed')
    letter,pid,metrics,work,text = (allocation+at for at in (16,208,240,272,3840))
    edges = (allocation,letter+176,pid+16,work-16,work+3552,text+1040,
             allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(letter,bytes(164));call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    homes = (2,0,3,1)

    def fixture(case,player=0,slot=0,*,owner=True,counts=0):
        state = bytearray(saved)
        state[0xEF5A] = 2 | (3<<4) | (1<<6)
        for index in range(4):
            home = homes[index]
            at = 0x3588+home*HOME_STRIDE
            state[at:at+16] = identities[index]
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE
            state[at:at+1640] = bytes(occupied)*10
        at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slot*164
        if slot < 10: state[at:at+164] = cleared
        if not owner: state[0x3588+homes[player]*HOME_STRIDE:0x358E+homes[player]*HOME_STRIDE] = b'OTHER '
        state[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+820] = cleared*5
        state[QUEUE-SAVE_RAM-8:QUEUE-SAVE_RAM] = struct.pack('>4H',counts,0,0,0)
        write(SAVE_RAM,state);write(pid,identities[player]);write(STAGING,b'!'*164)
        write(capital,word(case['capital']))
        return state

    def expected_mail(case,player):
        mail = bytearray(164);mail[:16] = identities[player]
        mail[18:30] = b' '*12;mail[30:35] = b'\xff'*5
        mail[36:38] = struct.pack('>H',case['gift'])
        mail[39:42] = bytes((128,4,case['paper']));mail[42:] = bytes.fromhex(case['wire'])
        return bytes(mail)

    for index,case in enumerate(request['cases']):
        player,slot = index%4,index%10
        before = fixture(case,player,slot)
        call(POST,[pid,player,case['gift'],case['paper'],case['template']],1)
        mail = expected_mail(case,player)
        at = HOME_MAILBOX+homes[player]*HOME_STRIDE+slot*164
        expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
        check('only selected home and slot receive complete Mom letter',SAVE_RAM,expected)
        check('complete staging metadata and text',STAGING,mail)
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        expected_text = bytes.fromhex(case['text'])
        check('complete delivered Mom letter reconstructs',text,expected_text)
        check('shared final capitalization',capital,word(expected_text[14]))
        check('recipient input retained',pid,identities[player])
        check('creator session detached',session,bytes(4))
        record({'native_mother_letter':case['template'],'home':homes[player],'slot':slot,'passed':True})

    first = request['cases'][0]
    for fault in ('unavailable','disabled','full_mailbox','full_queue','owner','bad_paper','bad_template'):
        case = dict(first)
        if fault == 'unavailable': case['template'] = 0x136
        if fault == 'bad_paper': case['paper'] = 64
        if fault == 'bad_template': case['template'] = 0x10000+0x12C
        before = fixture(case,slot=10 if fault in ('full_mailbox','full_queue') else 0,
                         owner=fault != 'owner',counts=5 if fault == 'full_queue' else 0)
        if fault == 'disabled': write(MODULE_RAM+68,bytes(4))
        call(POST,[pid,0,case['gift'],case['paper'],case['template']],0)
        check('rejected delivery retains the whole save',SAVE_RAM,before)
        # Vanilla receipt rejects a full home even when its five-slot queue is
        # empty. Preserve that policy; do not claim a successful queued delivery.
        created = fault == 'full_mailbox'
        check('failed creation never publishes stale staging',STAGING,expected_mail(case,0) if created else b'!'*164)
        expected_capital = bytes.fromhex(case['text'])[14] if created else case['capital']
        check('failure capitalization follows completed creation only',capital,word(expected_capital))
        check('failure detaches creator session',session,bytes(4))
        write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        if fault == 'disabled':
            # Retry the retained caller inputs without modifying its mailbox.
            call(POST,[pid,0,case['gift'],case['paper'],case['template']],1)
            check('restored resource permits complete retry',HOME_MAILBOX+homes[0]*HOME_STRIDE,expected_mail(case,0))
        record({'native_mother_rejection':fault,'passed':True})
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('native heap accounting retained',metrics,heap)
    for at in edges: check('fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    check('installed code retained',START,bytes.fromhex(request['code']))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items():
        if at in (0x8003C590,0x80140680): check('RNG and native handbill fields unchanged',at,value)
        write(at,value);check('original global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_mother_templates':len(request['cases']),'mother_rejections':7,'complete_retry':True,
            'mother_assertions':assertions,'debugger_uploaded_creator_bytes':0,
            'normal_scheduling':False,'hardware_verified':False,'requires_checkpoint_restore':True}
