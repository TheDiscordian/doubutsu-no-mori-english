"""Execute the native submission gate with fault injection and real receipt.

Only the creator is a fixture. The submission wrapper is copied to owned heap
memory with its original relative branches and native count/receipt targets.
All modified save RAM is restored; no cartridge or Controller Pak writes occur.
"""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import QUEUE,HOME_MAILBOX
from npc_mail_delivery import START,END,STAGING,patch,creator_fixture
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
COUNTERS,HOME_ID = QUEUE-8,0x8012A428
PID = b'READER'+b'NEWTWN'+bytes.fromhex('12343001')


def exercise(debug,request,record):
    read = debug.read_memory
    def write(address,value):
        debug.write_memory(address,value)
        record({'npc_delivery_fixture_write':f'{address:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,address,expected):
        value = read(address,len(expected))
        record({'npc_delivery_check':label,'address':f'{address:08X}','bytes':len(value),
                'assertion':'passed' if value == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('NPC delivery gate mismatch: '+label)
    def call(address,args=(),expected=None,proof=None):
        result = debug.call(f'{address:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'NPC delivery {address:08X} returned {result["return_value"]}, expected {expected}')
        return result
    original = bytes.fromhex(request['function'])
    for address,value in request['guards'].items():
        check('original native instructions',int(address,16),bytes.fromhex(value))
    check('complete original submission wrapper',START,original)
    saved,staged = read(SAVE_RAM,SAVE_BYTES),read(STAGING,164)
    allocation = call(0x8009BFC0,[1024])['return_value']
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-1024:
        raise ValueError('NPC delivery fixture allocation failed')
    base,creator,log,letter = allocation+16,allocation+160,allocation+240,allocation+304
    guards = (allocation,allocation+144,allocation+224,allocation+288,allocation+480,allocation+1008)
    for at in guards: write(at,EDGE)
    write(TEST_STACK-0x800,EDGE)
    write(TEST_STACK+0x30,EDGE)
    loaded,stub = patch(original,creator),creator_fixture(log)
    if len(loaded) != END-START or len(stub) != 64: raise ValueError('Delivery fixture layout changed')
    write(base,loaded)
    write(creator,stub)
    write(letter,b'!'*164)
    call(0x8009C384,[letter])
    cleared = read(letter,164)
    if cleared[38] != 255 or cleared[42:] != b' '*122:
        raise ValueError('Unexpected native cleared letter')
    occupied = bytearray(cleared);occupied[38] = 3
    write(HOME_ID,PID)
    write(HOME_MAILBOX,cleared*10)
    cases = []
    for counts in ((0,0),(4,0),(0,4),(2,2),(5,0),(0,5),(2,3),(3,3)):
        for success in (False,True):
            cases.append({'counts':counts,'creator':success,'free':0,'kind':0,'foreign':0,
                          'good':1,'invalid_recipient':True,'home_full':False})
    for kind in range(2):
        for foreign in range(2):
            for free in range(6):
                cases.append({'counts':(0,0),'creator':True,'free':free,'kind':kind,'foreign':foreign,
                              'good':kind,'invalid_recipient':False,'home_full':False})
    cases += [{'counts':(0,0),'creator':True,'free':0,'kind':0,'foreign':1,'good':0,
               'invalid_recipient':False,'home_full':True}]
    successes = 0
    for index,case in enumerate(cases):
        counts = case['counts']
        mail = bytearray(cleared)
        mail[:16],mail[16] = PID,3 if case['invalid_recipient'] else 0
        mail[18:24] = b'SENDER'
        mail[36:42] = bytes.fromhex('100100800005')
        mail[42:] = bytes.fromhex(request['letters'][case['kind']])
        if len(mail) != 164: raise ValueError('Invalid complete delivery fixture')
        queue = bytearray(bytes(occupied)*5)
        if case['free'] < 5: queue[case['free']*164:(case['free']+1)*164] = cleared
        write(QUEUE,queue)
        write(COUNTERS,struct.pack('>4H',*counts,0,0))
        write(HOME_MAILBOX,(bytes(occupied) if case['home_full'] else cleared)*10)
        write(letter,mail)
        stale = bytes(mail[:42])+b'OLD STAGED LETTER'.ljust(122,b' ')
        write(STAGING,stale)
        configured = letter if case['creator'] else 0
        write(log,bytes(28)+configured.to_bytes(4,'big'))
        before = read(SAVE_RAM,SAVE_BYTES)
        reached = sum(counts) < 5
        accepted = reached and case['creator'] and not case['invalid_recipient'] and case['free'] < 5 and not case['home_full']
        # A poisoned high portion verifies the original fifth-argument byte
        # load; the creator sees exactly the low byte in its sixth argument.
        args = [allocation+512,allocation+544,allocation+576,case['good'],0xAABBCC00|case['foreign']]
        result = call(base,args,int(accepted),proof=(base,loaded))
        expected_log = (struct.pack('>6I',STAGING,*args[:4],case['foreign']) if reached else bytes(24))
        expected_log += struct.pack('>2I',int(reached),configured)
        check('six creator arguments and exact invocation count',log,expected_log)
        if reached and not case['creator'] and result['return_value_v1'] != 0x5A5A:
            raise ValueError('Creator rejection did not retain the poisoned v1 witness')
        after = bytearray(before)
        if accepted:
            at = QUEUE-SAVE_RAM+case['free']*164
            after[at:at+164] = mail
            at = COUNTERS-SAVE_RAM
            after[at:at+6] = struct.pack('>3H',counts[0]+1,counts[1],1)
            successes += 1
        check('complete save changes restricted to successful native receipt',SAVE_RAM,after)
        check('returned complete letter cleared only after successful receipt',letter,cleared if accepted else mail)
        check('older global staging letter never submitted or changed',STAGING,stale)
        check('creator fixture remains unchanged',creator,stub)
        record({'npc_delivery_case':index,**case,'accepted':accepted,'passed':True})
    check('copied submission instructions remain unchanged',base,loaded)
    check('original submission remains unpatched',START,original)
    write(SAVE_RAM,saved)
    write(STAGING,staged)
    check('entire original save restored',SAVE_RAM,saved)
    check('entire original staging record restored',STAGING,staged)
    for at in guards: check('heap guard',at,EDGE)
    check('lower stack guard',TEST_STACK-0x800,EDGE)
    check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'native_npc_delivery_cases':len(cases),'native_receipt_successes':successes,
            'creator_is_fixture':True,'production_hook_installed':False,'requires_checkpoint_restore':True}
