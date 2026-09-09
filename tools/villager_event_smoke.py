"""Native event choice/metadata comparisons and complete mailbox readback batch."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_record import pack,unpack
from mail_runtime_test_scenario import output_bytes
from mail_storage import HOME_MAILBOX,HOME_STRIDE,QUEUE
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from villager_event_scenario import IDENTITIES,expected_record

EDGE = b'EDGE'*4
STAGING,FREE,TOWN = 0x80142F80,0x80140680,0x80129E00
RNG = (0x8003C590,0x800419F0)
CREATORS = {'event':0x800A94C8,'birthday':0x800A99B8,'goodbye':0x800AC284,'christmas':0x800A9CD4}
POST = {'event':0x800A956C,'birthday':0x800A9A98,'goodbye':0x800AC358,'christmas':0x800A9D68}


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'villager_event_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('Native villager-event mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Villager-event call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module = request['module'];symbols = module['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    check('no preceding capture scope',session,bytes(4))
    for at,value in request['patches'].items(): check('installed complete creator and gates',int(at,16),bytes.fromhex(value))
    for at,value in request['guards'].items(): check('original cache and RNG helpers',int(at,16),bytes.fromhex(value))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in (
        (0x80142F40,0xE4),(FREE,200),(capital,4),(MODULE_RAM+56,4),(MODULE_RAM+68,4),*((at,4) for at in RNG))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-8192:
        raise ValueError('Villager-event native fixture allocation failed')
    pid,animal,baseline,destination,metrics,work,text = (allocation+at for at in (0x420,0x450,0x480,0x540,0x600,0x620,0x1410))
    edges = (allocation,allocation+0x410,pid+16,animal+16,baseline+176,destination+176,
             work-16,work+3552,text+1040,allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    copies = {};cursor = allocation+16
    for family,entry in request['originals'].items():
        data = bytearray.fromhex(entry['data']);rewritten = 0
        for offset in range(0,len(data),4):
            if struct.unpack_from('>I',data,offset)[0] == 0x0C02A4EB:
                if family not in ('event','birthday','goodbye'): raise ValueError('Unexpected original common creator call')
                struct.pack_into('>I',data,offset,0x0C000000|((copies['common'][0]>>2)&0x03FFFFFF));rewritten += 1
        if rewritten != int(family in ('event','birthday','goodbye')):
            raise ValueError('Original event caller no longer has exactly one shared creation call')
        copies[family] = cursor,bytes(data);write(cursor,data);cursor += (len(data)+15)&~15
    if cursor > allocation+0x400: raise ValueError('Original comparison copies exceed their owned region')
    for at in (0x8002FE00,0x80034CE0):
        call(at,[allocation+16,cursor-allocation-16],proof=(at,bytes.fromhex(request['guards'][f'{at:08X}'])))
    write(baseline,bytes(164));call(0x8009C384,[baseline]);cleared = read(baseline,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    catalog,names = bytes.fromhex(request['catalog']),bytes.fromhex(request['items'])
    homes = (2,0,3,1)

    def fixture(case,player,slot,cap,*,owner=True,full_home=False,full_queue=False):
        state = bytearray(saved);state[0xEF5A] = 2|(3<<4)|(1<<6)
        state[TOWN-SAVE_RAM:TOWN-SAVE_RAM+6] = b'HERE  '
        for index,home in enumerate(homes):
            at = 0x3588+home*HOME_STRIDE;state[at:at+16] = IDENTITIES[index]
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE;state[at:at+1640] = bytes(occupied)*10
        if not full_home:
            at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slot*164;state[at:at+164] = cleared
        if not owner:
            at = 0x3588+homes[player]*HOME_STRIDE;state[at:at+6] = b'OTHER '
        state[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+820] = cleared*5
        state[QUEUE-SAVE_RAM-8:QUEUE-SAVE_RAM] = struct.pack('>4H',5 if full_queue else 0,0,0,0)
        write(SAVE_RAM,state);write(pid,IDENTITIES[player]);write(animal,bytes.fromhex(case['identity']))
        write(baseline,cleared);write(destination,b'!'*164);write(STAGING,b'!'*164);write(FREE,b'!'*200)
        write(RNG[0],word(case['seed']));write(RNG[1],bytes(4));write(capital,word(cap))
        return state

    def creator_args(case,target):
        family = case['family']
        return [target,pid]+([] if family == 'christmas' else [animal])+([case['choice'],case['looks']] if family == 'event' else [])

    def post_args(case,player):
        family = case['family']
        if family == 'goodbye': return [STAGING,pid,player,animal]
        return [pid,player]+([] if family == 'christmas' else [animal])+([case['choice']] if family == 'event' else [])

    comparisons,delivered = 0,0
    for index,case in enumerate(request['cases']):
        player,slot = index%4,index%10;family = case['family']
        for cap in (0,1):
            state = fixture(case,player,slot,cap)
            old_address,old_code = copies[family]
            call(old_address,creator_args(case,baseline),proof=(old_address,old_code))
            old = read(baseline,164);old_fields = read(FREE,200);old_rng = {at:read(at,4) for at in RNG}
            gift = int.from_bytes(old[36:38],'big')
            snapshot = expected_record(catalog,names,case,player,gift,cap)
            wanted = bytearray(old);wanted[39] = 128;wanted[42:] = pack(snapshot)
            wanted_text = output_bytes(snapshot,templates(catalog,snapshot))
            fixture(case,player,slot,cap)
            call(CREATORS[family],creator_args(case,destination),1 if family == 'goodbye' else destination)
            check('complete native metadata and English snapshot',destination,wanted)
            check('original temporary text fields retained',FREE,old_fields)
            for at,value in old_rng.items(): check('original selection and gift RNG retained',at,value)
            check('creation retains whole save',SAVE_RAM,state)
            check('recipient retained',pid,IDENTITIES[player]);check('villager identity retained',animal,bytes.fromhex(case['identity']))
            call(int(symbols['af_mail_restore'],16),[text,destination+42,122,work],1)
            check('complete creator letter reconstructs',text,wanted_text)
            check('complete creator capitalization',capital,word(wanted_text[14]));check('capture detached',session,bytes(4))
            comparisons += 1
            before = fixture(case,player,slot,cap)
            call(POST[family],post_args(case,player),1)
            at = HOME_MAILBOX+homes[player]*HOME_STRIDE+slot*164
            expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = wanted
            check('only selected mailbox receives complete event letter',SAVE_RAM,expected)
            check('complete delivered staging',STAGING,wanted)
            for address,value in old_rng.items(): check('delivery retains original choice and gift RNG',address,value)
            call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
            check('complete delivered letter reconstructs',text,wanted_text)
            check('delivered capitalization',capital,word(wanted_text[14]));check('delivery detached',session,bytes(4))
            delivered += 1
        record({'native_villager_event_template':case['template'],'family':family,'home':homes[player],'slot':slot,'passed':True})

    rejected = 0
    for family in CREATORS:
        case = next(c for c in request['cases'] if c['family'] == family)
        for fault in ('disabled','owner','full_home','full_queue'):
            before = fixture(case,0,0,1,owner=fault!='owner',full_home=fault in ('full_home','full_queue'),full_queue=fault=='full_queue')
            if fault == 'disabled': write(MODULE_RAM+68,bytes(4))
            call(POST[family],post_args(case,0),0)
            check('refused publication retains whole save',SAVE_RAM,before)
            check('refusal detaches capture',session,bytes(4))
            if fault != 'full_home' or family == 'christmas':
                check('failed or skipped creation retains staging',STAGING,b'!'*164)
                check('failed or skipped creation retains capital',capital,word(1))
            write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
            if fault == 'disabled':
                call(POST[family],post_args(case,0),1)
                at = HOME_MAILBOX+homes[0]*HOME_STRIDE;mail = read(at,164);snapshot = unpack(mail[42:],expected_catalog=request.get('catalog_id',2))
                selected = snapshot.templates[0]
                if not case['template'] <= selected < case['template']+(1 if family == 'christmas' else 3):
                    raise ValueError('Resource retry changed the event/personality group')
                retry_case = {**case,'template':selected}
                expected = expected_record(catalog,names,retry_case,0,int.from_bytes(mail[36:38],'big'),1)
                check('retry retains complete selected identities',at+42,pack(expected))
                call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
                check('complete resource retry reconstructs',text,output_bytes(expected,templates(catalog,expected)))
            rejected += 1;record({'native_villager_event_rejection':fault,'family':family,'passed':True})
    unavailable = dict(next(c for c in request['cases'] if c['template'] == 0xF7))
    unavailable.update(template=0xF6,choice=0,seed=request['cases'][0]['seed'])
    failures = [(next(c for c in request['cases'] if c['template'] == 0xEF),'items')]
    if request.get('catalog_id',2)==2: failures.insert(0,(unavailable,'semicolon'))
    for case,fault in failures:
        before = fixture(case,0,0,1)
        if fault == 'items': write(MODULE_RAM+56,bytes(4))
        call(POST['birthday'],post_args(case,0),0)
        check('unavailable complete birthday retains save',SAVE_RAM,before)
        check('unavailable complete birthday retains staging',STAGING,b'!'*164)
        check('unavailable birthday retains capital',capital,word(1))
        write(MODULE_RAM+56,globals_before[MODULE_RAM+56]);rejected += 1
        record({'native_villager_event_rejection':fault,'family':'birthday','passed':True})
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('native heap accounting retained',metrics,heap)
    for at,value in copies.values(): check('owned original comparison code retained',at,value)
    for at,value in request['patches'].items(): check('installed creator and gates retained',int(at,16),bytes.fromhex(value))
    for at in edges: check('fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('original globals restored',at,value)
    call(0x8009C040,[allocation])
    return {'villager_event_comparisons':comparisons,'complete_delivered_readbacks':delivered,
            'templates':len(request['cases']),'rejections':rejected,'resource_retries':4,
            'assertions':assertions,'creator_uploaded_bytes':0,'original_comparison_bytes':sum(len(v) for _,v in copies.values()),
            'normal_scheduling':False,'hardware_verified':False,'requires_checkpoint_restore':True}
