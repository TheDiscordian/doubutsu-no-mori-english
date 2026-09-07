"""Isolated native NPC sends; all gameplay mutations require checkpoint restoration."""

import struct

from aflib import sha256
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from mail_view_smoke import pointer

ANIMALS, STRIDE, COUNT = 0x80130DB8,0x528,15
SOURCE = TEST_RETURN+0x300
SHADOW = SOURCE+0x100
EDGE = b'EDGE'*4
LOW_STACK = TEST_STACK-0xC00


def exercise(debug,request,record):
    """Controlled in-memory sends, not normal post-office gameplay or a save."""
    def read(address,size): return debug.read_memory(address,size)
    def write(address,data):
        debug.write_memory(address,data)
        record({'test_only_ram_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        observed = read(address,len(expected))
        if observed != expected:
            differences = [(i,a,b) for i,(a,b) in enumerate(zip(observed,expected)) if a != b]
            record({'npc_mail_check':label,'read':[f'{address:08X}',len(expected)],'assertion':'failed',
                    'observed':observed.hex(),'expected':expected.hex()})
            raise ValueError(f'NPC mail {label} failed at {address:08X}: {len(differences)} differences; '
                             f'first offset/observed/expected values: {differences[:16]}')
        record({'npc_mail_check':label,'read':[f'{address:08X}',len(expected)],
                'sha256':sha256(observed),'assertion':'passed'})
    def call(address,args,expected=None):
        result = debug.call(f'{address:08X}',args)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'NPC mail native return at {address:08X}: {result["return_value"]} != {expected}')
        return result['return_value']
    for address,expected in request['guards'].items():
        check('instruction guard',int(address,16),bytes.fromhex(expected))
    context = int(request['context'],16)
    check('initial inactive score context',context,b'\0'*4)
    private = pointer(debug,0x80136FD8,0xBD0)
    player_no = read(0x80136EA3,1)
    if player_no[0] >= 4: raise ValueError('NPC send probe requires a local-player town checkpoint')
    # Clear only this player's first-job event through the original native API.
    # This is fixture setup, not evidence that the introductory jobs are complete.
    call(0x8007D2B8,[0x20000002+player_no[0]])
    call(0x8007D6E0,[],0)
    population = read(ANIMALS,STRIDE*COUNT)
    slots = [i for i in range(COUNT) if 0xE000 <= struct.unpack_from('>H',population,i*STRIDE)[0] < 0xE0D8]
    if not slots: raise ValueError('No native resident for isolated NPC send tests')
    slot = slots[0]
    animal = ANIMALS+slot*STRIDE
    original = population[slot*STRIDE:(slot+1)*STRIDE]
    for i in range(COUNT):
        if i != slot and population[i*STRIDE+0x4EC] == 0x86:
            raise ValueError('An unrelated letter quest would precede this isolated test')
    private_before = read(private,0xBD0)
    counter_before = read(0x80135E04,6)
    sender = private_before[:16]
    # The native clear helper defines its null PersonalID representation.
    write(LOW_STACK,EDGE)
    write(TEST_STACK+0x30,EDGE)
    for case in request['cases']:
        label = case['label']
        visitor,quest = case.get('visitor',False),case.get('quest',False)
        if visitor and quest: raise ValueError('The native visitor path does not receive local letter quests')
        write(animal,original)
        write(private,private_before)
        write(0x80136EA3,b'\x04' if visitor else player_no)
        memory = bytearray(176)
        memory[:16] = sender
        memory[0x28],memory[0x29] = 60,9
        write(animal+0x10,bytes(memory))
        contest = bytearray(36)
        if quest: contest[0],contest[1] = 0x86,0x10
        write(animal+0x4EC,bytes(contest))
        if quest:
            call(0x800B795C,[animal+0x4EC+14])
            contest[:] = read(animal+0x4EC,36)
        mail = bytearray.fromhex(case['mail'])
        if len(mail) != 164: raise ValueError('NPC test mail has the wrong native size')
        mail[0x12:0x22] = sender
        mail[0x22] = 0
        write(SOURCE-16,EDGE+mail+EDGE)
        call(0x8009C70C,[SOURCE,animal])
        mail[:] = read(SOURCE,164)
        before_animal = read(animal,STRIDE)
        before_private = read(private,0xBD0)
        expected_return = 0 if case.get('reject') else 1
        counters = bytearray(read(0x80135E04,6))
        if case.get('post_office'):
            expected_mail = bytes(mail)
            if expected_return:
                write(SHADOW-16,EDGE+mail+EDGE)
                call(0x8009C384,[SHADOW])
                expected_mail = read(SHADOW,164)
                counters[2:4] = ((int.from_bytes(counters[2:4],'big')+1)&0xFFFF).to_bytes(2,'big')
            call(0x800B6A3C,[SOURCE,0],expected_return)
        else:
            expected_mail = bytes(mail)
            call(0x800A8868,[SOURCE],expected_return)
        check(label+' source letter/accepted clearing',SOURCE-16,EDGE+expected_mail+EDGE)
        check(label+' post-office counts and recipient flags',0x80135E04,bytes(counters))
        check(label+' cleared score context',context,b'\0'*4)
        if case.get('reject'):
            check(label+' no NPC mutation',animal,before_animal)
            check(label+' no player mutation',private,before_private)
        else:
            expected = bytearray(before_animal)
            rank,legacy,length = case['scores']
            present = struct.unpack_from('>H',mail,0x24)[0]
            flags = memory[0x29]|0x80
            if not visitor and rank < 2: flags = (flags&~0x40)|0x20|(rank<<6)
            if quest: flags &= ~0x20
            expected[0x10+0x29] = flags
            expected[0x10+0x28] = 60+3-(5 if rank == 0 else 0)+(3 if present else 0)
            compact = bytes((mail[0x26],mail[0x29]))+mail[0x24:0x26]+bytes((mail[0x27],))+mail[0x2A:]
            expected[0x3A:0x3A+127] = compact
            # Native clear copies its invalid-date constant; local replies stamp RTC.
            expected[0xBA:0xBE] = read(0x80117AE8,4) if visitor else read(0x80136FC2,2)+read(0x80136FC1,1)+read(0x80136FBF,1)
            if quest:
                quest_rank = (2 if length >= 49 else 1 if length >= 17 else 0)+(3 if legacy else 0)+(6 if present else 0)
                contest[1] = (contest[1]&0x87)|8
                contest[14:30] = sender
                contest[32] = quest_rank
                # Prize selection remains the original RNG-dependent function.
                # Record its selected item; do not predict it with a second RNG draw.
                contest[34:36] = read(animal+0x4EC+34,2)
                expected[0x4EC:0x510] = contest
                record({'npc_mail_quest_score':quest_rank,'selected_present':contest[34:36].hex(),
                        'reference':label,'prize_selection':'original native function; exact random choice not asserted'})
            check(label+' complete NPC state',animal,bytes(expected))
            after_private = read(private,0xBD0)
            if visitor and rank < 2:
                # The unmodified visitor path owns exactly the seventeen-byte remail record.
                check(label+' player before remail',private,before_private[:0xACC])
                check(label+' player after remail',private+0xADD,before_private[0xADD:])
                check(label+' visitor date',private+0xACC,read(0x80136FC2,2)+read(0x80136FC1,1)+read(0x80136FBF,1))
                check(label+' visitor grade/personality',private+0xADC,bytes(((rank<<7)|(original[11]&0x7F),)))
                record({'npc_mail_visitor_names':after_private[0xAD0:0xADC].hex(),'reference':label,
                        'name_copy':'original native six-byte name and town-name calls'})
            else:
                check(label+' unchanged player state',private,before_private)
        if slot: check(label+' earlier NPCs',ANIMALS,population[:slot*STRIDE])
        tail = population[(slot+1)*STRIDE:]
        if tail: check(label+' later NPCs',animal+STRIDE,tail)
        check(label+' low stack guard',LOW_STACK,EDGE)
        check(label+' upper stack guard',TEST_STACK+0x30,EDGE)
        check(label+' module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
        record({'native_npc_send_case':label,'visitor':visitor,'quest':quest,'accepted':bool(expected_return),
                'post_office':case.get('post_office',False),
                'snapshot':mail[0x27] == 128,'requires_checkpoint_restore':True})
    write(animal,original)
    write(private,private_before)
    write(0x80136EA3,player_no)
    write(0x80135E04,counter_before)
    return {'native_npc_send_cases':len(request['cases']),'npc_slot':slot,
            'scope':'Controlled native sends with isolated memory fixtures; restore full checkpoint, including first-job event and RNG',
            'normal_post_office_gameplay':False,'game_save_validation':False}
