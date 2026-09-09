"""One silent cartridge actor, original selection, native receipt, and reader batch."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_storage import QUEUE,HOME_MAILBOX,HOME_STRIDE
from npc_mail_show import relocate_verified_data
from post_office_smoke import CACHE_GUARDS
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from snowman_actor import ActorImage,RAM,NEW_VROM,METADATA,START,END

EDGE = b'EDGE'*4
PRIVATE,PLAYER,RNG,RNG_TEMP,FREE = 0x80136FD8,0x80136EA3,0x8003C590,0x800419F0,0x80140680


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0;proofs = []
    def check(label,at,expected):
        nonlocal assertions
        actual = read(at,len(expected))
        record({'snowman_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected: raise ValueError('Native Snowman mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        if proof is None:
            proof = next(((base,data) for base,data in proofs if base<=at<base+len(data)),None)
        if at in CACHE_GUARDS:
            size,digest = CACHE_GUARDS[at];value = read(at,size)
            if sha256(value)!=digest: raise ValueError('Changed Snowman cache helper')
            proof = at,value
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Snowman call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(v): return struct.pack('>I',v)
    module,report = request['module'],request['report'];symbols = module['symbols']
    capital = int(symbols['af_mail_generation_capital'],16)
    for at,value in request['guards'].items(): check('unchanged native ownership helpers',int(at,16),bytes.fromhex(value))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in
                      ((capital,4),(PRIVATE,4),(PLAYER,1),(RNG,4),(RNG_TEMP,4),(FREE,200),(MODULE_RAM+68,4))}
    data,reloc,original,original_reloc = (bytes.fromhex(request[k]) for k in
                                        ('data','relocation','original','original_relocation'))
    size = 0xB000;allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Snowman fixture allocation failed')
    base = allocation+16;relocation_at = base+len(data);old = allocation+0x5000
    letter,pid,metrics,work,text = (allocation+at for at in (0x9500,0x9600,0x9620,0x9640,0xA440))
    if (relocation_at+len(reloc)+16>old or old+len(original)+16>letter
            or work+3552+16>text or text+1040+16>allocation+size):
        raise ValueError('Snowman fixture ranges overlap')
    edges = (allocation,relocation_at+len(reloc),old-16,old+len(original),letter-16,letter+176,
             pid+16,work-16,work+3552,text+1040,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    loaded = relocate_verified_data(ActorImage(RAM,len(data),struct.unpack_from('>5I',reloc)),data,reloc,base)
    loaded_original = relocate_verified_data(ActorImage(RAM,len(original),struct.unpack_from('>5I',original_reloc)),
                                             original,original_reloc,old)
    check('installed actor ownership',METADATA,bytes.fromhex(request['metadata']))
    call(0x800262D0,[NEW_VROM,NEW_VROM+len(data),RAM,RAM+len(data),base,relocation_at,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    check('native cartridge actor relocation',base,loaded);check('native merged relocation',relocation_at,reloc)
    proofs.append((base,loaded));proofs.append((old,loaded_original))
    write(old,loaded_original)
    call(0x8002FE00,[old,len(original)]);call(0x80034CE0,[old,len(original)])
    call(0x8009C384,[letter]);cleared = read(letter,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    identities = [f'PLYR{i} '.encode()+b'TOWN  '+bytes.fromhex('1234')+bytes((0x30,i+1)) for i in range(4)]
    homes = (2,0,3,1)

    def fixture(player=0,*,full_home=False,full_queue=False,foreign=False):
        state = bytearray(saved);state[0xEF5A] = 2|(3<<4)|(1<<6)
        for index in range(4):
            at = 0x20+index*0xBD0;state[at:at+16] = identities[index]
            at = 0x3588+homes[index]*HOME_STRIDE;state[at:at+16] = identities[index]
            at = HOME_MAILBOX-SAVE_RAM+homes[index]*HOME_STRIDE
            state[at:at+1640] = (bytes(occupied) if full_home else cleared)*10
        state[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+820] = (bytes(occupied) if full_queue else cleared)*5
        state[0xEF64:0xEF6C] = struct.pack('>4H',5 if full_queue else 0,0,0,0)
        write(SAVE_RAM,state);write(pid,identities[player]);write(PRIVATE,word(SAVE_RAM+0x20+player*0xBD0))
        write(PLAYER,bytes((4 if foreign else player,)))
        write(letter,b'!'*164)
        return state

    def expected_mail(case,player):
        mail = bytearray(cleared);mail[:16] = identities[player];mail[16] = 0
        mail[36:38] = struct.pack('>H',case['gift']);mail[38:42] = bytes((0,128,8,12))
        mail[42:] = bytes.fromhex(case['wire']);return bytes(mail)

    def restore_mail(case,at):
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        check('complete English Snowman readback',text,bytes.fromhex(case['text']))

    complete_cases = request['cases'] if request.get('group','all')=='all' else []
    for index,case in enumerate(complete_cases):
        player = index%4;before = fixture(player);write(capital,word(case['capital']));write(RNG,word(case['seed']))
        call(0x8009C384,[letter]);call(old+START-RAM,[letter]);metadata = read(letter,42)
        check('original Snowman gift choice',letter+36,struct.pack('>H',case['gift']))
        check('original single RNG draw',RNG,word(case['rng_end']))
        # Restore the comparison's temporary free fields before testing the
        # cartridge implementation, which must not touch those global fields.
        write(FREE,globals_before[FREE]);write(capital,word(case['capital']));write(RNG,word(case['seed']))
        write(letter,b'!'*164);call(base+START-RAM,[letter],1)
        check('complete record and native metadata',letter,expected_mail(case,player))
        check('original recipient sender gift font',letter,metadata[:39])
        check('original Snowman type and paper',letter+40,metadata[40:42])
        check('retained single RNG draw',RNG,word(case['rng_end']))
        check('creation does not alter save',SAVE_RAM,before);restore_mail(case,letter)
        write(capital,word(case['capital']));write(RNG,word(case['seed']))
        call(base+END-RAM)
        expected = bytearray(before);expected[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+164] = expected_mail(case,player)
        expected[0xEF64:0xEF66] = b'\0\1';expected[0xEF68:0xEF6A] = struct.pack('>H',1<<homes[player])
        check('native owner queues only the complete selected reward',SAVE_RAM,expected)
        check('owner single RNG draw',RNG,word(case['rng_end']));restore_mail(case,QUEUE)
        check('final Snowman capitalization',capital,word(bytes.fromhex(case['text'])[14]))
        check('Snowman leaves native free fields alone',FREE,globals_before[FREE])
        record({'native_snowman_case':case['choice'],'capital':case['capital'],'passed':True})

    first = request['cases'][0]
    for fault in ('full_home','full_queue','foreign','invalid_capital','disabled_catalog'):
        before = fixture(full_home=fault=='full_home',full_queue=fault=='full_queue',foreign=fault=='foreign')
        write(capital,word(2 if fault=='invalid_capital' else 0));write(RNG,word(first['seed']))
        if fault=='disabled_catalog': write(MODULE_RAM+68,bytes(4))
        call(base+END-RAM);expected = bytearray(before)
        if fault=='disabled_catalog':
            expected[QUEUE-SAVE_RAM:QUEUE-SAVE_RAM+164] = expected_mail(first,0)
            expected[0xEF64:0xEF66] = b'\0\1';expected[0xEF68:0xEF6A] = b'\0\4'
        check('native capacity policy and complete creation gate: '+fault,SAVE_RAM,expected)
        check('native owner RNG policy: '+fault,RNG,word(first['seed'] if fault in ('full_queue','foreign') else first['rng_end']))
        write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        if fault=='disabled_catalog': restore_mail(first,QUEUE)
        record({'native_snowman_owner_case':fault,'passed':True})

    for fault in ('choice','capital','overlap','readonly'):
        fixture();write(capital,word(2 if fault=='capital' else 1))
        args = [letter,letter+2 if fault=='overlap' else pid,12 if fault=='choice' else 0,capital]
        if fault=='readonly': args[1] = base+report['symbols']['af_snowman_templates']
        call(base+report['symbols']['af_snowman_create'],args,0)
        check('invalid creator request retains destination: '+fault,letter,b'!'*164)
        check('invalid creator request retains capitalization: '+fault,capital,word(2 if fault=='capital' else 1))
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('Snowman heap accounting retained',metrics,heap)
    check('loaded actor and immutable snapshots retained',base,loaded)
    check('original comparison actor retained',old,loaded_original)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    for at in edges: check('Snowman fixture and stack guard',at,EDGE)
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('Snowman global restored',at,value)
    call(0x8009C040,[allocation])
    return {'complete_snowman_cases':len(complete_cases),'snowman_owner_cases':5,'snowman_assertions':assertions,
            'debugger_uploaded_creator_bytes':0,'original_comparison_bytes':len(original),
            'normal_scheduling':False,'durable_full_mailbox_retry':False,'hardware_verified':False,
            'requires_checkpoint_restore':True}
