"""Native HRA metadata, full mailbox reads, and membership/date failure gates."""

import struct

from academy_letters import START,SCHEDULER
from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_record import Record,pack
from mail_runtime_test_scenario import output_bytes
from mail_storage import HOME_MAILBOX,HOME_STRIDE
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from villager_event_scenario import IDENTITIES

EDGE = b'EDGE'*4
FREE,PLAYER,PRIVATE,TIME,EMPLOYMENT = 0x80140680,0x80136EA3,0x80136FD8,0x80136FBC,0x8013A0E4
RNG = (0x8003C590,0x800419F0)
NOW = bytes.fromhex('00000011010907D0')


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = 0
    def check(label,at,expected):
        nonlocal assertions
        value = read(at,len(expected))
        record({'academy_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if value==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(value)})
        if value != expected: raise ValueError('Native academy mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Academy call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    symbols = request['module']['symbols']
    capital,session = (int(symbols[name],16) for name in ('af_mail_generation_capital','af_npc_mail_session'))
    check('no preceding capture scope',session,bytes(4))
    for at,value in {**request['patches'],**request['guards']}.items(): check('installed code guard',int(at,16),bytes.fromhex(value))
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((FREE,200),(PLAYER,1),(PRIVATE,4),(TIME,8),(EMPLOYMENT,4),
                        (capital,4),(MODULE_RAM+68,4),*((at,4) for at in RNG))}
    allocation = call(0x8009BFC0,[8192])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-8192:
        raise ValueError('Academy native fixture allocation failed')
    original_at,pid,baseline,metrics,work,text = (allocation+at for at in (16,0x180,0x1B0,0x280,0x300,0x1110))
    original = bytes.fromhex(request['original']);write(original_at,original)
    for at in (0x8002FE00,0x80034CE0):
        call(at,[original_at,len(original)],proof=(at,bytes.fromhex(request['guards'][f'{at:08X}'])))
    edges = (allocation,allocation+0x160,pid+16,baseline+176,work-16,work+3552,
             text+1040,allocation+8176,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(baseline,bytes(164));call(0x8009C384,[baseline]);cleared = read(baseline,164)
    occupied = bytearray(cleared);occupied[38] = 3
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    catalog = bytes.fromhex(request['catalog']);homes = (2,0,3,1)

    def fixture(player,slot,cap,*,full=False,member=False):
        state = bytearray(saved);state[0xEF5A] = 2|(3<<4)|(1<<6)
        for index,home in enumerate(homes):
            at = 0x3588+home*HOME_STRIDE;state[at:at+16] = IDENTITIES[index]
            state[at+24:at+28] = bytes.fromhex('07CF0101');state[at+28:at+32] = bytes((32 if member else 0,0,0,0))
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE;state[at:at+1640] = bytes(occupied)*10
        if not full:
            at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slot*164;state[at:at+164] = cleared
        write(SAVE_RAM,state);write(pid,IDENTITIES[player]);write(PRIVATE,word(pid));write(PLAYER,bytes((player,)))
        write(TIME,NOW);write(EMPLOYMENT,bytes(4));write(FREE,b'!'*200);write(capital,word(cap))
        write(RNG[0],bytes(4));write(RNG[1],bytes(4));write(baseline,cleared)
        # Native clear leaves structure padding; initialise the original's owned
        # comparison letter before it enters its independent stack frame.
        write(TEST_STACK-176,bytes(164))
        return state

    def english(player,number,cap):
        snapshot = Record(2,0,(number,),(),bool(cap));mail = bytearray(164)
        mail[:16] = IDENTITIES[player];mail[18:30] = b' '*12;mail[30:35] = b'\xff'*5
        mail[39:42] = bytes((128,6,51));mail[42:] = pack(snapshot)
        return bytes(mail),snapshot

    def readback(at,snapshot):
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        wanted = output_bytes(snapshot,templates(catalog,snapshot))
        check('complete delivered reader output',text,wanted)
        check('complete delivered capitalization',capital,word(wanted[14]))
        check('capture remains detached',session,bytes(4))

    comparisons = 0
    for index,number in enumerate(request['templates']):
        for cap in (0,1):
            player,slot = index//10+cap*2,index%10;home = homes[player]
            at = HOME_MAILBOX+home*HOME_STRIDE+slot*164
            before = fixture(player,slot,cap)
            call(original_at,[home,number],proof=(original_at,original))
            native = read(at,164);expected = bytearray(before)
            expected[at-SAVE_RAM:at-SAVE_RAM+164] = native
            check('original changes only its selected mailbox',SAVE_RAM,expected)
            check('original keeps unused free strings',FREE,b'!'*200)
            before = fixture(player,slot,cap);mail,snapshot = english(player,number,cap)
            if native[:39] != mail[:39] or native[40:42] != mail[40:42]:
                raise ValueError('Complete academy metadata differs from original sender/recipient/type/paper')
            call(START,[home,number],1)
            expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
            check('only selected mailbox receives complete English',SAVE_RAM,expected)
            check('creator keeps unused free strings',FREE,b'!'*200)
            for rng in RNG: check('direct creation consumes no RNG',rng,bytes(4))
            readback(at,snapshot);comparisons += 1
        record({'native_academy_template':number,'passed':True})

    rejections = 0
    for home,number in ((4,0x1DC),(0xFFFFFFFF,0x1DC),(homes[0],0x1DB),(homes[0],0x1F0),(homes[0],0x101DC)):
        before = fixture(0,0,1);call(START,[home,number],0)
        check('invalid home/template retains whole save',SAVE_RAM,before);check('invalid input retains capital',capital,word(1))
        rejections += 1

    # Exercise the real native scheduler, including its eligibility helper and
    # both changed success gates. No replacement scheduler code is uploaded.
    scheduler_cases,retries = 0,0
    next_seed = 0x3C6EF35F
    draw = struct.unpack('>f',word((next_seed>>9)|0x3F800000))[0]-1.0
    hint = 0x1DC+int(struct.unpack('>f',struct.pack('>f',draw*19.0))[0])
    for member in (False,True):
        for fault in ('none','disabled','full'):
            player,slot = int(member)+1,4;home = homes[player]
            before = fixture(player,slot,1,full=fault=='full',member=member)
            if fault == 'disabled': write(MODULE_RAM+68,bytes(4))
            call(0x8007D650,[],0);call(SCHEDULER,[0])
            if fault != 'none':
                check('failed delivery retains membership/date and whole save',SAVE_RAM,before)
                check('failed scheduler creation retains capital',capital,word(1));rejections += 1
            else:
                number = hint if member else 0x1EF;mail,snapshot = english(player,number,1)
                expected = bytearray(before);at = HOME_MAILBOX+home*HOME_STRIDE+slot*164
                expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
                offset = 0x3588+home*HOME_STRIDE
                expected[offset+24:offset+28] = bytes.fromhex('07D00911');expected[offset+28] = 32
                check('successful scheduler commits only letter and native flags/date',SAVE_RAM,expected)
                readback(at,snapshot)
                rng_before = tuple(read(rng,4) for rng in RNG);call(SCHEDULER,[0])
                check('same-day scheduler produces no duplicate',SAVE_RAM,expected)
                for rng,value in zip(RNG,rng_before): check('same-day scheduler does not reroll',rng,value)
            write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
            if fault == 'disabled':
                # Keep eligibility and the live RNG; a retry may select another
                # original hint, but never changes membership/date on failure.
                seed = int.from_bytes(read(RNG[0],4),'big');new_seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
                draw = struct.unpack('>f',word((new_seed>>9)|0x3F800000))[0]-1.0
                number = 0x1DC+int(struct.unpack('>f',struct.pack('>f',draw*19.0))[0]) if member else 0x1EF
                call(SCHEDULER,[0]);mail,snapshot = english(player,number,1)
                expected = bytearray(before);at = HOME_MAILBOX+home*HOME_STRIDE+slot*164
                expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail;offset = 0x3588+home*HOME_STRIDE
                expected[offset+24:offset+28] = bytes.fromhex('07D00911');expected[offset+28] = 32
                check('resource retry delivers and commits native flags/date',SAVE_RAM,expected)
                readback(at,snapshot);retries += 1
            scheduler_cases += 1
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('native heap accounting retained',metrics,heap)
    check('original comparison code retained',original_at,original)
    for at,value in request['patches'].items(): check('installed creator and gates retained',int(at,16),bytes.fromhex(value))
    for at in edges: check('fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('original globals restored',at,value)
    call(0x8009C040,[allocation])
    return {'academy_comparisons':comparisons,'complete_delivered_readbacks':comparisons+4,
            'templates':len(request['templates']),'scheduler_cases':scheduler_cases,'rejections':rejections,
            'resource_retries':retries,'assertions':assertions,'creator_uploaded_bytes':0,
            'original_comparison_bytes':len(original),'normal_gameplay':False,
            'hardware_verified':False,'requires_checkpoint_restore':True}
