"""Native departed-letter selection, cartridge creation, and actual receipt."""

import struct

from aflib import sha256
from departed_letters import START,POST
from departed_letter_scenario import PID,expected_record
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_record import unpack,pack
from mail_runtime_test_scenario import output_bytes
from mail_storage import QUEUE,HOME_MAILBOX,HOME_STRIDE
from mother_letters import STAGING
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
RNG,FREE,PLAYER = (0x8003C590,0x800419F0),0x80140680,0x80136EA3


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'departed_letter_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('Departed letter mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Departed call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module = request['module'];symbols = module['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    check('installed departed creator and retention gates',START,bytes.fromhex(request['installed_code']))
    check('no previous capture scope',session,bytes(4))
    for at,value in request['guards'].items(): check('original cache/RNG helper',int(at,16),bytes.fromhex(value))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in
                      ((STAGING,164),(capital,4),(FREE,200),(PLAYER,1),(MODULE_RAM+68,4),*((at,4) for at in RNG))}
    size = 0x4000
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Departed-letter fixture allocation failed')
    base,private,baseline,destination,metrics,work,text = (allocation+at for at in
                                                        (0x10,0x200,0xE00,0xEC0,0xF80,0x1000,0x1DF0))
    memory = private+0xAE4
    edges = (allocation,base+384,private-16,private+0xBD0,baseline-16,baseline+176,
             destination+176,work-16,work+3552,text+1040,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    old_code = bytes.fromhex(request['original_creator']);write(base,old_code)
    for at in (0x8002FE00,0x80034CE0):
        call(at,[base,len(old_code)],proof=(at,bytes.fromhex(request['guards'][f'{at:08X}'])))
    write(baseline,bytes(164));call(0x8009C384,[baseline]);cleared = read(baseline,164)
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    catalog = bytes.fromhex(request['catalog'])
    def fixture(case):
        value = bytearray(b'!'*0xBD0);value[:16] = PID
        value[0xAE4:0xAEC] = struct.pack('>H',case['npc'])+b'AWAY  '
        write(private,value);write(baseline,cleared);write(destination,b'!'*164)
        write(STAGING,b'!'*164);write(FREE,b'!'*200)
        write(RNG[0],word(case['seed']));write(RNG[1],bytes(4));write(capital,word(case['capital']))
        return value
    baselines = {}
    for index,case in enumerate(request['cases']):
        before = fixture(case)
        call(base,[baseline,private,memory],proof=(base,old_code))
        old = read(baseline,164);fields = read(FREE,200);rng = {at:read(at,4) for at in RNG}
        baselines[index] = old,fields,rng
        fixture(case)
        call(START,[destination,private,memory],destination)
        expected = bytearray(old);expected[39] = 128;expected[42:] = bytes.fromhex(case['wire'])
        check('original complete metadata and full English snapshot',destination,expected)
        check('original native temporary fields',FREE,fields)
        for at,value in rng.items(): check('original selection and stationery RNG retained',at,value)
        check('entire original private input retained',private,before)
        check('whole live save retained during creation',SAVE_RAM,saved)
        call(int(symbols['af_mail_restore'],16),[text,destination+42,122,work],1)
        expected_text = bytes.fromhex(case['text'])
        check('complete departed header body and footer',text,expected_text)
        check('shared final capitalization',capital,word(expected_text[14]))
        check('creator detached',session,bytes(4))
        record({'native_departed_comparison':index,'template':case['template'],'npc':case['npc'],'passed':True})

    occupied = bytearray(cleared);occupied[16] = 3;occupied[38] = 3
    def post_fixture(case,slot=0,*,full_home=False,full_queue=False,owner=True,visitor=False):
        value = fixture(case)
        state = bytearray(saved)
        for home in range(4):
            at = 0x3588+home*HOME_STRIDE;state[at:at+16] = b'\xff'*16
        if owner: state[0x3588:0x3598] = PID
        at = HOME_MAILBOX-SAVE_RAM
        state[at:at+1640] = (bytes(occupied) if full_home else cleared)*10
        at = QUEUE-SAVE_RAM;state[at:at+820] = bytes(occupied)*5
        if not full_queue: state[at+slot*164:at+(slot+1)*164] = cleared
        state[at-8:at] = struct.pack('>4H',5 if full_queue else 4,0,0,0)
        write(SAVE_RAM,state);write(PLAYER,bytes((4 if visitor else 0,)))
        return value,state

    for index in range(0,len(request['cases']),2):
        case = request['cases'][index];slot=(index//2)%5
        private_before,before = post_fixture(case,slot)
        call(POST,[private])
        mail = bytearray(baselines[index][0]);mail[39] = 128;mail[42:] = bytes.fromhex(case['wire'])
        expected = bytearray(before);at = QUEUE-SAVE_RAM+slot*164;expected[at:at+164] = mail
        expected[QUEUE-SAVE_RAM-8:QUEUE-SAVE_RAM-2] = struct.pack('>3H',5,0,1)
        check('only native queue and counters change on successful receipt',SAVE_RAM,expected)
        private_expected = bytearray(private_before);private_expected[0xAE4:0xAEC] = b'\xff\xff'+b' '*6
        check('remembered villager cleared only after receipt',private,private_expected)
        check('staging cleared after successful native receipt',STAGING,cleared)
        call(int(symbols['af_mail_restore'],16),[text,QUEUE+slot*164+42,122,work],1)
        check('complete delivered queue letter reconstructs',text,bytes.fromhex(case['text']))
        call(POST,[private]);check('cleared memory prevents duplicate delivery',SAVE_RAM,expected)
        record({'native_departed_delivery':case['template'],'queue_slot':slot,'passed':True})

    first = request['cases'][0]
    for fault in ('disabled','owner','full_home','full_queue','visitor','invalid_id'):
        private_before,before = post_fixture(first,full_home=fault=='full_home',full_queue=fault=='full_queue',
                                            owner=fault!='owner',visitor=fault=='visitor')
        if fault == 'disabled': write(MODULE_RAM+68,bytes(4))
        if fault == 'invalid_id':
            private_before[0xAE4:0xAE6] = b'\xe0\xd8';write(private,private_before)
        call(POST,[private])
        check('failed creation or receipt retains remembered villager',private,private_before)
        check('failed creation or receipt retains whole save',SAVE_RAM,before)
        if fault in ('disabled','full_queue','visitor','invalid_id'):
            check('failed or skipped creation retains old staging',STAGING,b'!'*164)
            check('failed or skipped creation retains capital',capital,word(first['capital']))
        check('failure detaches capture scope',session,bytes(4))
        write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        if fault == 'disabled':
            # The retained villager, not a rolled-back RNG/template, is retried.
            call(POST,[private])
            mail = read(QUEUE,164);snapshot = unpack(mail[42:],expected_catalog=2)
            if not 0xFC+first['looks']*3 <= snapshot.templates[0] < 0xFF+first['looks']*3:
                raise ValueError('Retry changed the remembered personality group')
            expected = expected_record(catalog,snapshot.templates[0],bytes.fromhex(first['name']),first['capital'])
            check('complete retried fields retain original identities',QUEUE+42,pack(expected))
            call(int(symbols['af_mail_restore'],16),[text,QUEUE+42,122,work],1)
            check('complete retry reconstructs',text,output_bytes(expected,templates(catalog,expected)))
            check('successful retry clears remembered villager',memory,b'\xff\xff'+b' '*6)
        record({'native_departed_rejection':fault,'passed':True})
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('native heap accounting retained',metrics,heap)
    check('original baseline code retained',base,old_code)
    check('installed departed code retained',START,bytes.fromhex(request['installed_code']))
    for at in edges: check('fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('original global restored',at,value)
    call(0x8009C040,[allocation])
    return {'departed_native_comparisons':36,'departed_delivered_templates':18,'departed_rejections':6,
            'complete_retry':True,'departed_assertions':assertions,'creator_uploaded_bytes':0,
            'baseline_original_uploaded_bytes':len(old_code),'normal_scheduling':False,
            'hardware_verified':False,'requires_checkpoint_restore':True}
