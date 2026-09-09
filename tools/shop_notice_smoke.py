"""Native shop owners, complete readbacks, and failed-preparation retention."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import HOME_MAILBOX,HOME_STRIDE
from post_office_smoke import CACHE_GUARDS
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from shop_notice_letters import START,END

EDGE = b'EDGE'*4
LEAFLET,LEAFLET_COUNT,NOTICE,WORKING = 0x80136140,0x80136288,0x80135C12,0x8013A0E4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0;original = 0;readbacks = 0
    original_bytes = bytes.fromhex(request['original'])
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'shop_notice_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected: raise ValueError('Native shop notice mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None):
        verified = None
        if original<=at<original+len(original_bytes): verified = (original,original_bytes)
        elif at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];data = read(at,size)
            if sha256(data)!=digest: raise ValueError('Changed shop notice cache helper')
            verified = (at,data)
        result = debug.call(f'{at:08X}',args,verified_code=verified);record(result)
        if expected is not None and result['return_value']!=expected: raise ValueError('Unexpected shop notice call result')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    symbols = request['module']['symbols']
    capital,session = (int(symbols[n],16) for n in ('af_mail_generation_capital','af_npc_mail_session'))
    for at,value in request['guards'].items(): check('installed shop owners and selectors',int(at,16),bytes.fromhex(value))
    check('detached creator at entry',session,bytes(4))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((capital,4),(0x8003C590,4),(0x80140680,200),
                                                    (MODULE_RAM+68,4),(WORKING,4))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-8192:
        raise ValueError('Shop notice fixture allocation failed')
    original,letter,pid,descriptor,metrics,work,text = (allocation+at for at in (16,1536,1728,1760,1808,1856,5440))
    edges = (allocation,allocation+1456,letter+176,pid+16,descriptor+16,work-16,work+3552,
             text+1040,allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(original,original_bytes)
    call(0x8002FE00,[original,len(original_bytes)]);call(0x80034CE0,[original,len(original_bytes)])
    call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    home_players = (1,3,0,2)

    def fixture(shop=0,*,full=False,absent=False,working=False,pending=True,event=False):
        state = bytearray(saved);state[0xEF5A] = 2 | (3<<4) | (1<<6)
        for player in range(4):
            at = 0x20+player*0xBD0;state[at:at+16] = identities[player];state[at+0x13] = 0
        for home,player in enumerate(home_players):
            at = 0x3588+home*HOME_STRIDE;state[at:at+16] = identities[player]
            if absent: state[at+14:at+16] = b'\xff'*2
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE
            state[at:at+1640] = bytes(occupied)*10
            if not full: state[at+home*164:at+(home+1)*164] = cleared
        state[LEAFLET-SAVE_RAM:LEAFLET-SAVE_RAM+164] = b'!'*164
        state[LEAFLET_COUNT-SAVE_RAM:LEAFLET_COUNT-SAVE_RAM+2] = b'\x12\x34'
        state[NOTICE-SAVE_RAM] = 0xD7|(0x20 if pending else 0)
        state[0x80135C14-SAVE_RAM:0x80135C18-SAVE_RAM] = word((0,25000,90000,240000)[shop])
        state[0x80135C28-SAVE_RAM:0x80135C2C-SAVE_RAM] = word(1)
        write(SAVE_RAM,state);write(WORKING,word((0x3C if working else 0)|(1 if event else 0)))
        write(0x80140680,globals_before[0x80140680]);write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        write(letter,b'!'*164);write(pid,identities[0])
        return state

    def mail(case,player=None):
        value = bytearray(cleared)
        if player is not None: value[:17] = identities[player]+b'\0'
        value[38:42] = bytes((0,128,2,55));value[42:] = bytes.fromhex(case['wire'])
        return bytes(value)

    def restore(case,at):
        nonlocal readbacks
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        check('complete delivered shop text',text,bytes.fromhex(case['text']));readbacks += 1

    for index,case in enumerate(request['cases']):
        home = index%4;player = home_players[home]
        at = HOME_MAILBOX+home*HOME_STRIDE+home*164 if case['mode'] else LEAFLET
        args = [home,case['shop'],case['item'],case['kind'],case['mode']]
        before = fixture(case['shop']);call(original,args);metadata = read(at,42)
        fixture(case['shop']);write(capital,word(case['capital']));call(START,args)
        expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail(case,player if case['mode'] else None)
        if not case['mode']: expected[LEAFLET_COUNT-SAVE_RAM:LEAFLET_COUNT-SAVE_RAM+2] = bytes(2)
        check('only spotlight receipt changes save state',SAVE_RAM,expected)
        check('spotlight native identities font and gift',at,metadata[:39])
        check('spotlight native type and paper',at+40,metadata[40:42]);restore(case,at)
        check('spotlight complete capital state',capital,word(bytes.fromhex(case['text'])[14]))
        check('spotlight preserves unrelated native fields',0x80140680,globals_before[0x80140680])
        record({'native_shop_spotlight':index,'template':case['template'],'mode':case['mode'],'passed':True})

    for index,case in enumerate(request['reopening']):
        before = fixture(case['shop']);call(original+0x398)
        metadata = [read(HOME_MAILBOX+home*HOME_STRIDE+home*164,42) for home in range(4)]
        fixture(case['shop']);write(capital,word(case['capital']));call(0x800C1230)
        expected = bytearray(before);expected[NOTICE-SAVE_RAM] &= ~0x20
        for home,player in enumerate(home_players):
            at = HOME_MAILBOX+home*HOME_STRIDE+home*164
            expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail(case,player)
            check('reopening native identities font and gift',at,metadata[home][:39])
            check('reopening native type and paper',at+40,metadata[home][40:42]);restore(case,at)
        check('reopening complete homes and original notification bit',SAVE_RAM,expected)
        check('reopening original capitalization unchanged',capital,word(case['capital']))
        record({'native_shop_reopening':index,'shop':case['shop'],'template':case['template'],'passed':True})

    for mode in (0,1):
        case = next(c for c in request['cases'] if c['shop']==2 and c['kind']==1 and c['mode']==mode and c['capital']==1)
        for fault in ('disabled','capital','full','absent','working'):
            before = fixture(2,full=fault=='full',absent=fault=='absent',working=fault=='working')
            write(capital,word(2 if fault=='capital' else 1))
            if fault=='disabled': write(MODULE_RAM+68,bytes(4))
            call(START,[0,2,case['item'],1,mode]);expected = bytearray(before)
            if fault=='full' and not mode:
                expected[LEAFLET-SAVE_RAM:LEAFLET-SAVE_RAM+164] = mail(case)
                expected[LEAFLET_COUNT-SAVE_RAM:LEAFLET_COUNT-SAVE_RAM+2] = bytes(2)
            check('spotlight fault retains original publication policy: '+fault,SAVE_RAM,expected)
            check('spotlight fault detaches creator',session,bytes(4))
            record({'native_shop_fault':'spotlight','mode':mode,'fault':fault,'passed':True})

    for fault in ('disabled','capital','full','absent','working','not_pending','event'):
        before = fixture(2,full=fault=='full',absent=fault=='absent',working=fault=='working',
                         pending=fault!='not_pending',event=fault=='event')
        write(capital,word(2 if fault=='capital' else 1))
        if fault=='disabled': write(MODULE_RAM+68,bytes(4))
        call(0x800C1230);expected = bytearray(before)
        if fault in ('full','absent','working'): expected[NOTICE-SAVE_RAM] &= ~0x20
        check('reopening notification after fault: '+fault,SAVE_RAM,expected)
        check('reopening fault detaches creator',session,bytes(4))
        if fault in ('disabled','capital'):
            write(MODULE_RAM+68,globals_before[MODULE_RAM+68]);write(capital,word(1))
            call(0x800C1230);case = next(c for c in request['reopening'] if c['shop']==2 and c['capital']==1)
            expected[NOTICE-SAVE_RAM] &= ~0x20
            for home,player in enumerate(home_players):
                at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE+home*164;expected[at:at+164] = mail(case,player)
            check('reopening resource retry completes all homes',SAVE_RAM,expected)
            call(0x800C1230);check('reopening pending bit prevents duplicate notices',SAVE_RAM,expected)
        record({'native_shop_fault':'reopening','fault':fault,'passed':True})

    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('shop creator heap retained',metrics,heap)
    for at in edges: check('shop fixture and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at,value in request['guards'].items(): check('shop code retained',int(at,16),bytes.fromhex(value))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('shop global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_spotlight_cases':32,'complete_reopening_cases':8,'full_readbacks':readbacks,
            'owner_fault_cases':17,'shop_notice_assertions':assertions,'debugger_uploaded_creator_bytes':0,
            'normal_scheduling':False,'hardware_verified':False,'requires_checkpoint_restore':True}
