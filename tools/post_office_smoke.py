"""Native cartridge creation, original metadata, and pending postal delivery."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import HOME_MAILBOX,HOME_STRIDE
from post_office_letters import START,END
from post_office_scenario import case as make_case
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
CACHE_GUARDS = {
    0x8002FE00:(116,'5306341d7122fdbbae63d48917c76f7f6c2ee0321e490862302581561bf0474c'),
    0x80034CE0:(116,'713e7b78373df6fbf3d030b5237e9c1e2148c9443cbfdf938f2e8ffdf8e2d326'),
}


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0;original = 0
    original_bytes = bytes.fromhex(request['original_creator'])
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'post_office_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value!=expected: raise ValueError('Native post-office mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None):
        verified = None
        if at == original: verified = (original,original_bytes)
        elif at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];data = read(at,size)
            if sha256(data)!=digest: raise ValueError('Changed native postal cache helper')
            verified = (at,data)
        result = debug.call(f'{at:08X}',args,verified_code=verified);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Postal call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    module = request['module'];symbols = module['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    for at,value in request['guards'].items(): check('installed postal code and original loops',int(at,16),bytes.fromhex(value))
    check('no previous creator session',session,bytes(4))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((capital,4),(0x8003C590,4),(0x80140680,200),(MODULE_RAM+68,4))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-8192:
        raise ValueError('Postal fixture allocation failed')
    original,letter,pid,order,metrics,work,text = (allocation+at for at in (16,192,384,416,448,480,4096))
    edges = (allocation,allocation+144,letter+176,pid-16,pid+16,order+16,work+3552,text+1040,
             allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    # letter+176 and pid-16 intentionally name the same boundary.
    for at in set(edges): write(at,EDGE)
    write(original,bytes.fromhex(request['original_creator']))
    call(0x8002FE00,[original,END-START]);call(0x80034CE0,[original,END-START])
    call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    catalog,items = bytes.fromhex(request['catalog']),bytes.fromhex(request['items'])

    def fixture(player=0,home=0,slots=(0,)):
        state = bytearray(saved)
        for i in range(4):
            at = 0x20+i*0xBD0;state[at:at+16] = identities[i]
            state[0xA94+i*0xBD0] = 1
            state[at+0xA94:at+0xA94+20] = bytes(20)
            state[at+0x32:at+0x34] = bytes(2)
            at = HOME_MAILBOX-SAVE_RAM+i*HOME_STRIDE
            state[at:at+1640] = bytes(occupied)*10
        for slot in slots:
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE+slot*164;state[at:at+164] = cleared
        write(SAVE_RAM,state);write(pid,identities[player]);write(letter,b'!'*164)
        return state

    def expected_mail(case,player):
        mail = bytearray(164);mail[:16] = identities[player]
        mail[18:30] = b' '*12;mail[30:35] = b'\xff'*5
        mail[36:38] = struct.pack('>H',case['gift']);mail[39:42] = bytes((128,7,55))
        mail[42:] = bytes.fromhex(case['wire']);return bytes(mail)

    def restore_mail(case,at):
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        check('complete delivered postal text',text,bytes.fromhex(case['text']))

    for index,case in enumerate(request['cases']):
        player,home,slot = index%4,(index//4)%4,index%10
        before = fixture(player,home,(slot,));write(capital,word(case['capital']))
        # Original native creator runs from a copied original function, not a
        # replacement mock. All its external calls retain their native targets.
        call(0x8009C384,[letter]);call(original,[letter,case['template'],case['gift'],pid])
        metadata = read(letter,42)
        write(capital,word(case['capital']));write(letter,b'!'*164)
        call(START,[letter,case['template'],case['gift'],pid],1)
        expected = expected_mail(case,player)
        check('complete postal metadata and packed letter',letter,expected)
        check('native recipient sender gift and font retained',letter,metadata[:39])
        check('native postal type and paper retained',letter+40,metadata[40:42])
        check('final postal capitalization',capital,word(bytes.fromhex(case['text'])[14]))
        check('creator session detached',session,bytes(4))
        if case['template']==0x57:
            call(0x800B6D80,[home,pid,case['gift']],1)
        else:
            write(order,struct.pack('>HBB',case['gift'],case['template']-0x49,0))
            call(END,[home,pid,order],1)
        # The templates end in a stable capitalization state. Recreate the
        # expected saved record using the capital immediately before delivery.
        delivered = make_case(catalog,items,case['template'],case['gift'],bytes.fromhex(case['text'])[14])
        at = HOME_MAILBOX+home*HOME_STRIDE+slot*164;expected_save = bytearray(before)
        expected_save[at-SAVE_RAM:at-SAVE_RAM+164] = expected_mail(delivered,player)
        check('only selected home slot receives the letter',SAVE_RAM,expected_save)
        restore_mail(delivered,at)
        check('recipient input retained',pid,identities[player])
        record({'native_post_office_case':case['template'],'gift':case['gift'],'passed':True})

    loop_cases = 0
    for kind in ('orders','tickets'):
        for fault in ('none','disabled','full','partial','absent'):
            player,home = 2,3;slots = () if fault=='full' else (0,) if fault=='partial' else tuple(range(10))
            state = fixture(player,home,slots);p = 0x20+player*0xBD0
            if fault=='absent': state[0xA94+player*0xBD0] = 0
            if kind=='orders':
                orders = [(0x11FC,i%4) for i in range(5)]
                for i,(gift,level) in enumerate(orders): state[p+0xA94+i*4:p+0xA98+i*4] = struct.pack('>HBB',gift,level,0)
                count = 5;entry = 0x800B6C88
            else:
                state[p+0x32:p+0x34] = bytes((9,13));count = 3;entry = 0x800B6DCC
            write(SAVE_RAM,state);write(capital,bytes(4))
            if fault=='disabled': write(MODULE_RAM+68,bytes(4))
            call(entry,[home,player]);expected = bytearray(state)
            delivered = 0 if fault in ('disabled','full','absent') else 1 if fault=='partial' else count
            next_cap = 0;remaining = 13
            for i in range(delivered):
                if kind=='orders':
                    gift,level = orders[i];number = 0x49+level
                    expected[p+0xA94+i*4:p+0xA96+i*4] = bytes(2)
                else:
                    batch = min(5,remaining);gift = 0x2C40+batch-1;number = 0x57;remaining -= batch
                case = make_case(catalog,items,number,gift,next_cap)
                next_cap = bytes.fromhex(case['text'])[14]
                at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE+i*164
                expected[at:at+164] = expected_mail(case,player)
            if kind=='tickets': expected[p+0x33] = remaining
            check('native pending '+kind+' receipt and retention: '+fault,SAVE_RAM,expected)
            check('pending loop detaches creator session',session,bytes(4))
            if fault=='disabled':
                write(MODULE_RAM+68,globals_before[MODULE_RAM+68]);call(entry,[home,player])
                if kind=='orders':
                    for i in range(5): check('restored order resource permits receipt',SAVE_RAM+p+0xA94+i*4,bytes(2))
                else: check('restored ticket resource permits receipt',SAVE_RAM+p+0x33,bytes(1))
            record({'native_post_office_loop':kind,'fault':fault,'passed':True});loop_cases += 1
    for number,gift in ((0x48,0x11FC),(0x4D,0x11FC),(0x49,0),(0x57,0x2C05),(0x57,0x2C60)):
        fixture();write(capital,word(1));call(START,[letter,number,gift,pid],0)
        check('invalid postal request retains destination',letter,b'!'*164)
        check('invalid postal request retains capitalization',capital,word(1))
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('postal heap accounting retained',metrics,heap)
    for at in set(edges): check('postal fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at,value in request['guards'].items(): check('postal code retained',int(at,16),bytes.fromhex(value))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    check('native RNG retained',0x8003C590,globals_before[0x8003C590])
    for at,value in globals_before.items(): write(at,value);check('postal global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_postal_cases':len(request['cases']),'postal_loop_cases':loop_cases,'postal_assertions':assertions,
            'debugger_uploaded_creator_bytes':0,'original_comparison_bytes':END-START,
            'normal_scheduling':False,'hardware_verified':False,'requires_checkpoint_restore':True}
