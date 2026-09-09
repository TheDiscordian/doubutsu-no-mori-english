"""Native quest reply owner comparisons, complete readbacks, and failure retention."""
import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import HOME_MAILBOX,HOME_STRIDE
from post_office_smoke import CACHE_GUARDS
from quest_reply_letters import START
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0;original = 0;readbacks = 0
    original_bytes = bytes.fromhex(request['original_creator'])
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'quest_reply_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected: raise ValueError('Native quest reply mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None):
        verified = None
        if at==original: verified = (original,original_bytes)
        elif at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];data = read(at,size)
            if sha256(data)!=digest: raise ValueError('Changed quest reply cache helper')
            verified = (at,data)
        result = debug.call(f'{at:08X}',args,verified_code=verified);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Quest reply call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    symbols = request['module']['symbols']
    capital,session = (int(symbols[n],16) for n in ('af_mail_generation_capital','af_npc_mail_session'))
    for at,value in request['guards'].items(): check('installed quest code and native selectors',int(at,16),bytes.fromhex(value))
    check('creator detached at entry',session,bytes(4));saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((capital,4),(0x8003C590,4),(0x800419F0,4),
                                                    (0x80140680,200),(MODULE_RAM+68,4))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-8192:
        raise ValueError('Quest reply fixture allocation failed')
    original,letter,pid,animal,quest,metrics,work,text = (allocation+o for o in (16,336,528,560,592,656,704,4288))
    edges = (allocation,allocation+320,letter+176,pid+16,animal+16,quest+48,work-16,work+3552,
             text+1040,allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(original,original_bytes)
    call(0x8002FE00,[original,len(original_bytes)]);call(0x80034CE0,[original,len(original_bytes)])
    call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    home_players = (1,3,0,2)

    def fixture(case,home=0,slot=0,*,fault=None):
        state = bytearray(saved);state[0xEF5A] = 0x72;player = home_players[home]
        for i in range(4):
            at = 0x20+i*0xBD0;state[at:at+16] = identities[i]
            at = 0x3588+i*HOME_STRIDE;state[at:at+16] = identities[home_players[i]]
            at = HOME_MAILBOX-SAVE_RAM+i*HOME_STRIDE;state[at:at+1640] = bytes(occupied)*10
        at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE+slot*164
        if fault!='full': state[at:at+164] = cleared
        if fault=='wrong_home': state[0x3588+home*HOME_STRIDE:0x3588+home*HOME_STRIDE+16] = identities[(player+1)%4]
        identity = bytes(12)+b'\xff'*4 if fault=='null_player' else identities[player]
        if fault=='absent_player': identity = b'ABSENT'+b'TOWN  '+bytes.fromhex('12343005')
        contest = bytearray(36);contest[0:2] = bytes((0x86,8));contest[14:30] = identity
        contest[32] = case['rank'];contest[34:36] = struct.pack('>H',case['gift'])
        write(SAVE_RAM,state);write(pid,identity);write(animal,bytes.fromhex(case['animal']));write(quest,contest)
        write(letter,b'!'*164);write(capital,word(2 if fault=='capital' else case['capital']))
        write(0x80140680,globals_before[0x80140680]);write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        write(0x8003C590,globals_before[0x8003C590]);write(0x800419F0,globals_before[0x800419F0])
        if fault=='disabled': write(MODULE_RAM+68,bytes(4))
        return state,bytes(contest)

    def restore(case,at):
        nonlocal readbacks
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        check('complete delivered quest reply text',text,bytes.fromhex(case['text']));readbacks += 1

    for index,case in enumerate(request['cases']):
        home,slot = index%4,(index//4)%10;before,contest = fixture(case,home,slot)
        call(0x8009C384,[letter]);call(original,[letter,pid,animal,case['rank'],case['gift']])
        metadata = read(letter,42);native_fields = read(0x80140680,200)
        fixture(case,home,slot);call(0x800BB990,[quest,animal],1)
        at = HOME_MAILBOX+home*HOME_STRIDE+slot*164
        expected = bytearray(metadata+bytes.fromhex(case['wire']));expected[39] = 128
        state = bytearray(before);state[at-SAVE_RAM:at-SAVE_RAM+164] = expected
        check('only selected home slot changes',SAVE_RAM,state)
        check('original recipient sender gift font type paper',at,expected[:42])
        check('original quest and selected reward retained',quest,contest)
        check('original native temporary fields retained',0x80140680,native_fields)
        check('original animal identity retained',animal,bytes.fromhex(case['animal']))
        check('quest generation uses no new random selection',0x8003C590,globals_before[0x8003C590])
        check('quest generation retains random temporary',0x800419F0,globals_before[0x800419F0])
        check('final quest reply capitalization',capital,word(bytes.fromhex(case['text'])[14]))
        check('creator detaches after quest reply',session,bytes(4));restore(case,at)
        record({'native_quest_reply_case':case['template'],'capital':case['capital'],'home':home,'slot':slot,'passed':True})

    case = next(c for c in request['cases'] if c['template']==0x8D and c['capital']==1)
    for fault in ('disabled','capital','full','wrong_home','null_player','absent_player'):
        before,contest = fixture(case,fault=fault)
        call(0x800BB990,[quest,animal],0)
        check('quest failure retains save: '+fault,SAVE_RAM,before)
        check('quest failure retains selected inputs: '+fault,quest,contest)
        check('quest failure retains capitalization: '+fault,capital,word(2 if fault=='capital' else 1))
        check('quest failure detaches creator: '+fault,session,bytes(4))
        if fault in ('disabled','capital'):
            write(MODULE_RAM+68,globals_before[MODULE_RAM+68]);write(capital,word(1))
            call(0x800BB990,[quest,animal],1);restore(case,HOME_MAILBOX)
            check('resource retry retains original quest inputs',quest,contest)
        record({'native_quest_reply_fault':fault,'passed':True})

    for rank in (12,255,256,0xFFFFFFFF):
        fixture(case);call(START,[letter,pid,animal,rank,case['gift']],0)
        check('invalid full-width rank retains output',letter,b'!'*164)
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('quest creator heap retained',metrics,heap)
    for at in edges: check('quest fixture and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at,value in request['guards'].items(): check('quest code retained',int(at,16),bytes.fromhex(value))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('quest global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_quest_reply_cases':len(request['cases']),'full_readbacks':readbacks,
            'owner_fault_cases':6,'rank_rejections':4,'quest_reply_assertions':assertions,
            'debugger_uploaded_creator_bytes':0,'normal_conversation':False,'game_save_validation':False,
            'hardware_verified':False,'requires_checkpoint_restore':True}
