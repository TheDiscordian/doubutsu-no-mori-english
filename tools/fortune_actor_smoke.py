"""Real Miko callbacks, cartridge relocation, and complete pocket-to-reader checks."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from fortune_actor import ActorImage,RAM,NEW_VROM,METADATA,INSTANCE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE = b'EDGE'*4
PRIVATE,RNG,RNG_TEMP,FREE,DEMO = 0x80136FD8,0x8003C590,0x800419F0,0x80140680,0x80139C50


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'fortune_actor_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual != expected: raise ValueError('Native fortune hand-off mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Fortune actor {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((PRIVATE,4),(RNG,4),(RNG_TEMP,4),(FREE,200),(DEMO,200))}
    for at,value in request['guards'].items(): check('native helper retained',int(at,16),bytes.fromhex(value))
    check('native demo pointer',0x80104A70,word(DEMO-16))
    check('installed actor ownership',METADATA,bytes.fromhex(request['metadata']))
    report,module = request['report'],request['module']
    data,reloc = bytes.fromhex(request['data']),bytes.fromhex(request['relocation'])
    size = 0x7000
    allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Fortune actor fixture allocation failed')
    base = allocation+16;relocation_at = base+len(data)
    actor,player,stage,arena,work,shim = (allocation+offset for offset in (0x2200,0x2C00,0x3C20,0x3D00,0x4000,0x3D40))
    edges = (allocation,relocation_at+len(reloc),actor-16,actor+INSTANCE_BYTES,
             player-16,player+4096,stage+176,arena+16,work-16,work+4720,allocation+size-16,
             TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    spec = ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc))
    loaded = relocate_verified_data(spec,data,reloc,base)
    call(0x800262D0,[NEW_VROM,NEW_VROM+len(data),RAM,RAM+len(data),base,relocation_at,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    check('complete cartridge relocation including native prefix and appended code',base,loaded)
    check('complete merged relocation records',relocation_at,reloc)
    proof = (base,loaded[:report['text_bytes']])
    init = base+report['symbols']['af_miko_fortune_init']
    give = base+report['symbols']['af_miko_fortune_give']
    abort = base+report['symbols']['af_miko_fortune_abort']
    # Enter the real original payment/effect tail with its original frame and
    # actor argument, then let that tail restore the frame and return normally.
    # This executes the installed original call site, not just the new callee.
    tail = base+0x728
    shim_code = struct.pack('>8I',0x27BDFFE0,0xAFBF0014,0xAFA40020,
                            0x08000000|((tail>>2)&0x3FFFFFF),0,0,0,0)
    write(shim,shim_code)
    capital = int(module['symbols']['af_mail_generation_capital'],16)
    globals_before[capital] = read(capital,4)
    call(0x8009C0C0,[arena,arena+4,arena+8]);heap_before = read(arena,12)
    player_bytes = bytearray((i%251 for i in range(4096)))
    player_bytes[:16] = b'PLAYER' + b'TOWN  ' + bytes.fromhex('12343001')
    player_bytes[0x14:0x3C] = bytes(0x28)
    struct.pack_into('>I',player_bytes,0x38,500)
    # All ten slots start occupied. One explicit received-status FF frees the
    # selected slot without touching any real player's inventory or identity.
    for slot in range(10): player_bytes[0x40A+slot*164+0x26] = 0
    write(player,player_bytes);write(PRIVATE,word(player))
    write(stage,bytes(164));call(0x8009C384,[stage]);call(0x8009C4A0,[stage,player])
    prepared = read(stage,164)
    before_orders = globals_before[DEMO]
    def orders(ready=True):
        result = bytearray(before_orders)
        struct.pack_into('>H',result,(4*10+9)*2,int(ready))
        return result
    def setup(case,slot,money=500,bag=None):
        fixture = bytearray(player_bytes)
        struct.pack_into('>I',fixture,0x38,money)
        if bag is not None:
            kind,pocket = bag
            struct.pack_into('>H',fixture,0x14+pocket*2,(0x2103,0x2100,0x2101,0x2102)[kind])
        if slot is not None: fixture[0x40A+slot*164+0x26] = 0xFF
        write(player,fixture);write(actor,b'!'*INSTANCE_BYTES)
        write(actor+0x938,word(2));write(capital,word(case['capital']))
        write(RNG,word(case['seed']));write(DEMO,orders())
        call(init,[actor,0],proof=proof)
        check('native one-draw outcome',actor+0x940,word(bytes.fromhex(case['choice'])[4]))
        check('original outcome RNG progression',RNG,word(case['rng_states'][0]))
        check('per-instance initialization',actor+0x948,bytes(8)+word(1)+word(0)+word(player)+bytes(4))
        write(actor+0x938,word(3))
        call(shim,[actor],proof=(shim,shim_code))
        fixture[0xA8E] = (0,3,4,5)[bytes.fromhex(case['choice'])[4]]
        payment = 0xA5000000|money
        balance = money-50
        if money < 50:
            kind,pocket = bag
            balance += (100,1000,10000,30000)[kind]
            struct.pack_into('>H',fixture,0x14+pocket*2,0)
            payment |= ((pocket+1)<<17)|(kind<<21)
        struct.pack_into('>I',fixture,0x38,balance)
        check('original native price, bag consumption, and luck store',player,fixture)
        check('recorded payment identity',actor+0x95C,word(payment))
        return fixture
    def expected(case,fixture,slot):
        mail = bytearray(prepared);mail[38:42] = bytes((0,128,5,25));mail[42:] = bytes.fromhex(case['wire'])
        result = bytearray(fixture);at = 0x40A+slot*164;result[at:at+164] = mail
        return result
    for index,case in enumerate(request['cases']):
        slot = index%10;fixture = setup(case,slot)
        call(give,[actor,0],proof=proof)
        check('whole player changes only by one complete fortune letter',player,expected(case,fixture,slot))
        check('original six-draw RNG progression',RNG,word(case['rng_states'][-1]))
        check('complete pending choices and delivered state',actor+0x948,
              bytes.fromhex(case['choice'])+word(3)+word(case['capital'])+word(player)+bytes(4))
        check('native action zero and callback',actor+0x938,word(0)+word(0x8009AC74))
        expected_orders = orders(False)
        for group,entry,value in ((4,1,2),(5,0,0x2513),(5,1,7),(5,2,0)):
            struct.pack_into('>H',expected_orders,(group*10+entry)*2,value)
        check('all five native hand-off orders and other orders retained',DEMO,expected_orders)
        wire_at = player+0x40A+slot*164+42
        call(int(module['symbols']['af_mail_restore'],16),[work+3552,wire_at,122,work],1)
        check('complete cartridge-backed pocket-to-reader text',work+3552,bytes.fromhex(case['text']))
        for at in edges: check('owned actor, player, work, and stack guard',at,EDGE)
    case = request['cases'][0]
    fixture = setup(case,None)
    call(give,[actor,0],proof=proof)
    check('full pocket retains complete player',player,fixture)
    check('full pocket makes no further selections',RNG,word(case['rng_states'][0]))
    check('full pocket retains hand-off orders',DEMO,orders())
    fixture = setup(case,0)
    write(0x80194924,bytes(4))
    call(give,[actor,0],proof=proof)
    pending = read(actor+0x948,24)
    check('disabled catalog retains full player',player,fixture)
    check('disabled catalog retains pending choices',actor+0x948,
          bytes.fromhex(case['choice'])+word(2)+word(case['capital'])+word(player)+word(0xA5000000|500))
    for _ in range(3): call(give,[actor,0],proof=proof)
    check('retries retain exact selections',actor+0x948,pending)
    check('retries consume no additional RNG',RNG,word(case['rng_states'][-1]))
    check('retries do not announce delivery',DEMO,orders())
    write(capital,word(1));write(0x80194924,bytes.fromhex('03000000'))
    call(give,[actor,0],proof=proof)
    check('successful retry publishes the same complete letter',player,expected(case,fixture,0))
    check('successful retry retains current shared capitalization',capital,word(1))
    write(actor+0x938,word(3));write(DEMO,orders())
    call(give,[actor,0],proof=proof)
    check('repeated delivered callback cannot duplicate the letter',player,expected(case,fixture,0))
    check('repeated delivered callback cannot reroll',RNG,word(case['rng_states'][-1]))
    check('repeated delivered callback cannot announce another hand-off',DEMO,orders())
    # Exact interruption recovery across every native bag denomination and all
    # pocket positions. Keep the already revealed luck and all unrelated bytes.
    recoveries = 0
    for kind in range(4):
        for pocket in range(15):
            money = (0,1,49)[pocket%3]
            fixture = setup(case,0,money,(kind,pocket))
            expected_refund = bytearray(fixture)
            struct.pack_into('>I',expected_refund,0x38,money)
            struct.pack_into('>H',expected_refund,0x14+pocket*2,(0x2103,0x2100,0x2101,0x2102)[kind])
            if pocket in (0,14):
                write(0x80194924,bytes(4));call(give,[actor,0],proof=proof)
                write(0x80194924,bytes.fromhex('03000000'))
            rng = read(RNG,4)
            call(abort,[actor],1,proof)
            check('exact original wallet and consumed bag restored',player,expected_refund)
            check('refund leaves RNG unchanged',RNG,rng)
            check('refunded payment is cleared',actor+0x95C,bytes(4))
            check('refunded state prevents another delivery',actor+0x950,word(4))
            call(abort,[actor],1,proof)
            check('repeated interruption cannot duplicate money or bag',player,expected_refund)
            recoveries += 1
    for money in (50,51,500,99999):
        fixture = setup(case,0,money)
        struct.pack_into('>I',fixture,0x38,money)
        call(abort,[actor],1,proof)
        check('wallet-only payment restored exactly',player,fixture)
        recoveries += 1
    call(0x8009C0C0,[arena,arena+4,arena+8])
    check('all temporary actor work is freed',arena,heap_before)
    check('complete native save retained',SAVE_RAM,saved)
    check('native handbill table retained',FREE,globals_before[FREE])
    check('complete loaded image retained',base,loaded)
    check('native payment-tail shim retained',shim,shim_code)
    for at in edges: check('final allocation and stack guard',at,EDGE)
    check('resident guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at,value in globals_before.items(): write(at,value);check('restored temporary global',at,value)
    call(0x8009C040,[allocation])
    return {'complete_fortune_hand_off_cases':len(request['cases']),'fortune_actor_assertions':assertions,
            'failed_resource_retries':4,'pocket_to_reader_cases':len(request['cases']),
            'exact_payment_recoveries':recoveries,
            'allocation_freed':f'{allocation:08X}','normal_gameplay':False,
            'cleanup_hook_routing':'source_and_host_verified','normal_scene_removal':'not_verified',
            'requires_checkpoint_restore':True}
