"""Native museum creation, delivery, and retained notice/fossil eligibility."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import QUEUE,HOME_MAILBOX,HOME_STRIDE
from museum_letters import START,END,STAGING,FOSSILS
from museum_scenario import case as make_case
from post_office_smoke import CACHE_GUARDS
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0;original = 0
    original_bytes = bytes.fromhex(request['original_creator'])
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'museum_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value!=expected: raise ValueError('Native museum mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None):
        verified = None
        if at == original: verified = (original,original_bytes)
        elif at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];data = read(at,size)
            if sha256(data)!=digest: raise ValueError('Changed native museum cache helper')
            verified = (at,data)
        result = debug.call(f'{at:08X}',args,verified_code=verified);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Museum call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module = request['module'];symbols = module['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    for at,value in request['guards'].items(): check('installed museum code and original selection',int(at,16),bytes.fromhex(value))
    check('no previous creator session',session,bytes(4))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in
                      ((STAGING,164),(capital,4),(0x8003C590,4),(0x80140680,200),(MODULE_RAM+68,4))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-8192:
        raise ValueError('Museum fixture allocation failed')
    original,letter,pid,metrics,work,text,gift_out = (allocation+at for at in (16,192,384,432,464,4096,5280))
    edges = (allocation,allocation+160,letter+176,pid+16,work-16,work+3552,text+1040,
             gift_out-16,gift_out+16,allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(original,original_bytes)
    call(0x8002FE00,[original,END-START]);call(0x80034CE0,[original,END-START])
    call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    homes = (2,0,3,1);catalog = bytes.fromhex(request['catalog'])

    def fixture(player=0,slots=(0,),*,owner=True,queue_full=False):
        state = bytearray(saved);state[0xEF5A] = 2 | (3<<4) | (1<<6)
        for index in range(4):
            at = 0x20+index*0xBD0;state[at:at+16] = identities[index];state[at+0x13] = 0
            at = 0x3588+homes[index]*HOME_STRIDE;state[at:at+16] = identities[index]
            at = HOME_MAILBOX-SAVE_RAM+homes[index]*HOME_STRIDE
            state[at:at+1640] = bytes(occupied)*10
        for slot in slots:
            at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slot*164;state[at:at+164] = cleared
        if not owner: state[0x3588+homes[player]*HOME_STRIDE:0x358E+homes[player]*HOME_STRIDE] = b'OTHER '
        state[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+820] = (bytes(occupied) if queue_full else cleared)*5
        state[QUEUE-SAVE_RAM-8:QUEUE-SAVE_RAM] = struct.pack('>4H',5 if queue_full else 0,0,0,0)
        write(SAVE_RAM,state);write(pid,identities[player]);write(letter,b'!'*164);write(STAGING,b'!'*164)
        return state

    def expected_mail(case,player):
        mail = bytearray(164);mail[:16] = identities[player]
        mail[18:24] = bytes.fromhex('1907F81105C3');mail[24:30] = b' '*6
        mail[30:34] = b'\xff'*4;mail[34] = 2
        mail[36:38] = struct.pack('>H',case['gift']);mail[39:42] = bytes((128,0,24))
        mail[42:] = bytes.fromhex(case['wire']);return bytes(mail)

    def restore_mail(case,at):
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        check('complete delivered museum text',text,bytes.fromhex(case['text']))

    for index,case in enumerate(request['cases']):
        player,slot = index%4,index%10
        before = fixture(player,(slot,));write(capital,word(case['capital']))
        call(original,[letter,pid,case['gift'],case['template']]);metadata = read(letter,42)
        rng = read(0x8003C590,4)
        write(capital,word(case['capital']));write(letter,b'!'*164)
        call(START,[letter,pid,case['gift'],case['template']],letter)
        check('complete museum metadata and packed letter',letter,expected_mail(case,player))
        check('native recipient sender gift and font retained',letter,metadata[:39])
        check('native museum type and paper retained',letter+40,metadata[40:42])
        check('museum creation retains native RNG',0x8003C590,rng)
        write(capital,word(case['capital']))
        call(0x800A35C8,[pid,player,case['gift'],case['template']],1)
        at = HOME_MAILBOX+homes[player]*HOME_STRIDE+slot*164;expected = bytearray(before)
        expected[at-SAVE_RAM:at-SAVE_RAM+164] = expected_mail(case,player)
        check('only selected museum home slot changes',SAVE_RAM,expected)
        restore_mail(case,at)
        check('final museum capitalization',capital,word(bytes.fromhex(case['text'])[14]))
        check('museum recipient input retained',pid,identities[player])
        check('museum creator session detached',session,bytes(4))
        record({'native_museum_case':case['template'],'gift':case['gift'],'capital':case['capital'],'passed':True})

    # A deliberately mismatched initial player index selects another house.
    # Native fallback then finds the correct owner and enqueues the complete
    # letter. This exercises the fallback contract, not normal scheduling.
    first = request['cases'][0]
    for fault in ('none','disabled','full_queue','full_home','owner'):
        player = 2;before = fixture(player,() if fault=='full_home' else (0,),
                                   owner=fault!='owner',queue_full=fault=='full_queue')
        write(capital,bytes(4))
        if fault=='disabled': write(MODULE_RAM+68,bytes(4))
        call(0x800A35C8,[pid,0,0,0xBD],int(fault=='none'))
        expected = bytearray(before)
        if fault=='none':
            expected[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+164] = expected_mail(first,player)
            expected[0xEF64:0xEF66] = bytes((0,1));expected[0xEF68:0xEF6A] = bytes((0,1<<homes[player]))
        check('native museum fallback receipt or retained failure: '+fault,SAVE_RAM,expected)
        check('museum fallback detaches creator session',session,bytes(4))
        if fault=='none': restore_mail(first,QUEUE);check('native queue receipt clears staging',STAGING,cleared)
        if fault=='disabled':
            check('disabled fallback retains staging',STAGING,b'!'*164)
            write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
            call(0x800A35C8,[pid,0,0,0xBD],1)
            check('restored museum resource permits fallback retry',QUEUE,expected_mail(first,player))
        record({'native_museum_fallback':fault,'passed':True})

    loop_cases = 0
    for kind in ('intro','wrong','fossils','combined'):
        for fault in ('none','disabled','full','partial','absent'):
            player = 2;slots = () if fault=='full' else (0,) if fault=='partial' else tuple(range(10))
            before = fixture(player,slots);p = 0x20+player*0xBD0
            before[p+0x13] = {'intro':0x65,'wrong':0xC0,'fossils':0x9F,'combined':0xDF}[kind]
            if fault=='absent': before[p:p+16] = b' '*12+b'\xff'*4
            write(SAVE_RAM,before);write(capital,bytes(4));write(0x8003C590,word(0x13579BDF))
            if fault=='disabled': write(MODULE_RAM+68,bytes(4))
            entry = 0x800A36CC if kind=='intro' else 0x800A3810

            def expected_loop(state,enabled):
                expected = bytearray(state);deliveries = [];next_cap = 0
                # Predict selection by calling the unchanged native fossil
                # routine from the same seed, then restore the seed before
                # executing the real pending loop. Failed fossil attempts
                # consume their original RNG draw but retain the saved count.
                seed = read(0x8003C590,4)
                if fault!='absent':
                    planned = [0xBD] if kind=='intro' else [0xBE] if kind=='wrong' else [None]*3 if kind=='fossils' else [0xBE,None,None]
                    for number in planned:
                        gift = 0
                        if number is None:
                            call(0x800A3784,[gift_out]);gift = int.from_bytes(read(gift_out,2),'big')
                            number = call(0x800A37D0,[gift])
                            if not 0x1E3C<=gift<0x1EA0 or number!=FOSSILS[(gift-0x1E3C)//4]:
                                raise ValueError('Native fossil choice is outside the verified museum table')
                        if not enabled: break
                        if len(deliveries)>=len(slots):
                            # Intro has only the direct home path. Other museum
                            # letters complete creation in fallback even when
                            # native receipt subsequently rejects a full home.
                            if kind!='intro':
                                c = make_case(catalog,number,gift,next_cap)
                                next_cap = bytes.fromhex(c['text'])[14]
                            break
                        c = make_case(catalog,number,gift,next_cap);next_cap = bytes.fromhex(c['text'])[14]
                        at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slots[len(deliveries)]*164
                        expected[at:at+164] = expected_mail(c,player);deliveries.append((c,SAVE_RAM+at))
                        flags = expected[p+0x13]
                        expected[p+0x13] = (flags|0x80)&0xDF if number==0xBD else flags&0xBF if number==0xBE else (flags&0xE0)|((flags-1)&0x1F)
                end_rng = read(0x8003C590,4);write(0x8003C590,seed)
                return expected,deliveries,end_rng,next_cap

            expected,deliveries,end_rng,next_cap = expected_loop(before,fault!='disabled')
            call(entry)
            check('museum pending flags counts and receipts: '+kind+': '+fault,SAVE_RAM,expected)
            check('museum loop preserves original fossil RNG sequence',0x8003C590,end_rng)
            check('museum pending loop detaches creator session',session,bytes(4))
            check('museum pending loop capitalization',capital,word(next_cap))
            for c,at in deliveries: restore_mail(c,at)
            if fault=='disabled':
                write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
                expected,deliveries,end_rng,next_cap = expected_loop(before,True)
                call(entry)
                check('museum pending resource retry succeeds: '+kind,SAVE_RAM,expected)
                check('museum retry preserves original fossil RNG sequence',0x8003C590,end_rng)
                for c,at in deliveries: restore_mail(c,at)
            if kind in ('intro','wrong') and fault in ('none','partial'):
                call(entry);check('museum notice is not sent twice',SAVE_RAM,expected)
            record({'native_museum_loop':kind,'fault':fault,'passed':True});loop_cases += 1

    for number,gift in ((0xBC,0),(0xBD,0x1E3C),(0x10E,0),(0x10E,0x1EA0),(0x10F,0x1E3C)):
        fixture();write(capital,word(1));call(START,[letter,pid,gift,number],0)
        check('invalid museum request retains destination',letter,b'!'*164)
        check('invalid museum request retains capitalization',capital,word(1))
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('museum heap accounting retained',metrics,heap)
    for at in edges: check('museum fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at,value in request['guards'].items(): check('museum code retained',int(at,16),bytes.fromhex(value))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    check('museum retains native handbill fields',0x80140680,globals_before[0x80140680])
    for at,value in globals_before.items(): write(at,value);check('museum global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_museum_cases':len(request['cases']),'museum_loop_cases':loop_cases,'museum_assertions':assertions,
            'museum_fallback_cases':5,'debugger_uploaded_creator_bytes':0,'original_comparison_bytes':END-START,
            'normal_scheduling':False,'hardware_verified':False,'requires_checkpoint_restore':True}
