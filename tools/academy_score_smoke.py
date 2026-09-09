"""Cartridge score overlay, complete English readbacks, and actual HRA scheduler."""

import struct
from types import SimpleNamespace

from academy_letters import SCHEDULER
from academy_score_letters import RAM,VROM
from academy_score_scenario import expected_record,selected_template
from academy_smoke import FREE,PLAYER,PRIVATE,TIME,EMPLOYMENT,RNG,EDGE
from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_catalog import templates
from mail_record import pack
from mail_runtime_test_scenario import output_bytes
from mail_storage import HOME_MAILBOX,HOME_STRIDE,QUEUE
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from villager_event_scenario import IDENTITIES


def exercise(debug,request,record):
    read,write = debug.read_memory,debug.write_memory
    assertions = readbacks = 0
    def check(label,at,expected):
        nonlocal assertions
        observed = read(at,len(expected))
        record({'academy_score_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if observed==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(observed)})
        if observed != expected:
            differences = [i for i,(a,b) in enumerate(zip(expected,observed)) if a!=b]
            record({'score_mismatch_bytes':len(differences),'first_differences':[
                {'offset':i,'expected':expected[i],'observed':observed[i]} for i in differences[:24]]})
            raise ValueError('Native score mismatch: '+label)
        assertions += 1
    def call(at,args=(),expected=None,proof=None,v1=None):
        result = debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Score call {at:08X} returned {result["return_value"]}, expected {expected}')
        if v1 is not None and result['return_value_v1'] != v1:
            raise ValueError(f'Score call {at:08X} returned v1={result["return_value_v1"]}, expected {v1}')
        return result['return_value']
    def word(value): return struct.pack('>I',value)
    symbols = request['module']['symbols'];capital,session = (int(symbols[name],16) for name in
                  ('af_mail_generation_capital','af_npc_mail_session'))
    check('no active preceding capture',session,bytes(4))
    for at,value in request['guards'].items(): check('native helper guard',int(at,16),bytes.fromhex(value))
    scheduler = bytes.fromhex(request['scheduler']);check('installed whole HRA scheduler',SCHEDULER,scheduler)
    saved = read(SAVE_RAM,SAVE_BYTES)
    globals_before = {at:read(at,size) for at,size in ((FREE,200),(PLAYER,1),(PRIVATE,4),(TIME,8),(EMPLOYMENT,4),
                      (capital,4),(MODULE_RAM+68,4),(0x80107B50,4),*((at,4) for at in RNG))}
    size = 0xC000;allocation = call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Score fixture allocation failed')
    base,original_at,work,text,pid,series,game,metrics,empty = (allocation+at for at in
                     (16,0x4800,0x9000,0x9DE0,0xA300,0xA320,0xA400,0xA500,0xA600))
    data,reloc,original,oldreloc = (bytes.fromhex(request[k]) for k in ('data','relocation','original','original_relocation'))
    spec = SimpleNamespace(ram=RAM,resident_bytes=16976,sections=struct.unpack_from('>5I',reloc))
    loaded = relocate_verified_data(spec,data,reloc,base)
    proof = (base,loaded[:spec.sections[0]])
    original_spec = SimpleNamespace(ram=RAM,resident_bytes=16976,sections=struct.unpack_from('>5I',oldreloc))
    oldloaded = relocate_verified_data(original_spec,original,oldreloc,original_at)
    oldproof = (original_at,oldloaded[:original_spec.sections[0]])
    call(0x800262D0,[VROM,VROM+len(data),RAM,RAM+16976,base,base+16976,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['guards']['800262D0'])))
    check('native cartridge relocation and BSS clear',base,loaded)
    check('native adjacent relocation records',base+16976,reloc)
    # Only the independently relocated original is uploaded for comparisons.
    # The replacement score overlay, creator, and resources all load from ROM.
    write(original_at,oldloaded)
    for at in (0x8002FE00,0x80034CE0):
        call(at,[original_at,len(oldloaded)],proof=(at,bytes.fromhex(request['guards'][f'{at:08X}'])))
    check('complete original comparison image',original_at,oldloaded)
    edges = (allocation,base+16976+len(reloc),original_at-16,original_at+16976,work-16,
             text+1040,pid+16,series+16,game-16,metrics+16,empty+176,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x30)
    for at in edges: write(at,EDGE)
    write(empty,bytes(164));call(0x8009C384,[empty]);cleared = read(empty,164)
    occupied = bytearray(cleared);occupied[38] = 3
    write(game,bytes(256));call(0x800D3848,[game+0x88]);game_alloc = read(game+0x88,20)
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);heap = read(metrics,12)
    catalog = bytes.fromhex(request['catalog']);homes = (2,0,3,1)
    longest = max(range(55),key=lambda i:len(bytes.fromhex(request['series'][i]['english']).rstrip()))
    write(series,bytes.fromhex(request['series'][longest]['native'])+b' '*6)

    def fixture(player,slot,cap,case,*,full=False,queue_full=False,month=9,day=17,score_room=False):
        state = bytearray(saved);state[0xEF5A] = 2|(3<<4)|(1<<6)
        for i,home in enumerate(homes):
            at = 0x3588+home*HOME_STRIDE;state[at:at+16] = IDENTITIES[i]
            state[at+24:at+28] = bytes.fromhex('07CF0101');state[at+28:at+32] = bytes((160,0,0,0))
            if score_room:
                state[at+20:at+22] = bytes(2);state[at+34:at+36] = bytes(2)
                state[at+56:at+56+1024] = bytes(1024)
            at = HOME_MAILBOX-SAVE_RAM+home*HOME_STRIDE;state[at:at+1640] = bytes(occupied)*10
        if not full:
            at = HOME_MAILBOX-SAVE_RAM+homes[player]*HOME_STRIDE+slot*164;state[at:at+164] = cleared
        at = QUEUE-SAVE_RAM;state[at:at+820] = cleared*5
        state[at-8:at] = struct.pack('>4H',5 if queue_full else 0,0,0,0)
        write(SAVE_RAM,state);write(pid,IDENTITIES[player]);write(PRIVATE,word(pid));write(PLAYER,bytes((player,)))
        write(TIME,bytes((0,0,0,day,1,month,7,208)));write(EMPLOYMENT,bytes(4));write(FREE,b'!'*200)
        write(capital,word(cap));write(RNG[0],word(case['seed']));write(RNG[1],bytes(4))
        for start in (base,original_at): write(start+0x80929628-RAM,bytes.fromhex(case['bits']))
        write(TEST_STACK-180,bytes(164))
        return state

    def english(player,number,points,cap,month=9,day=17):
        snapshot = expected_record(request,number,points,longest,month,day,cap)
        mail = bytearray(164);mail[:16] = IDENTITIES[player];mail[18:30] = b' '*12;mail[30:35] = b'\xff'*5
        mail[39:42] = bytes((128,6,51));mail[42:] = pack(snapshot)
        return bytes(mail),snapshot

    def readback(at,snapshot):
        nonlocal readbacks
        call(int(symbols['af_mail_restore'],16),[text,at+42,122,work],1)
        wanted = output_bytes(snapshot,templates(catalog,snapshot))
        check('complete delivered English reader output',text,wanted)
        check('complete delivered final capital',capital,word(wanted[14]));check('capture detached',session,bytes(4))
        readbacks += 1

    comparisons = 0
    for index,case in enumerate([] if request.get('scheduler_only') else request['cases']):
        for cap in (0,1):
            player,slot = index//10+cap*2,index%10;home = homes[player]
            at = HOME_MAILBOX+home*HOME_STRIDE+slot*164;month,day = index%12+1,index%28+1
            args = [home,case['points'],case['room'],series,0x11FC,0]
            before = fixture(player,slot,cap,case,month=month,day=day)
            call(original_at+0x468,args,proof=oldproof)
            check('original selected template',TEST_STACK-12,word(case['template']))
            original_mail = read(at,164);rng = tuple(read(addr,4) for addr in RNG)
            expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = original_mail
            check('original changes only the selected mailbox',SAVE_RAM,expected)
            before = fixture(player,slot,cap,case,month=month,day=day)
            mail,snapshot = english(player,case['template'],case['points'],cap,month,day)
            if original_mail[:39] != mail[:39] or original_mail[40:42] != mail[40:42]:
                raise ValueError('Score metadata differs from original sender/recipient/type/paper/gift')
            call(base+0x468,args,1,proof,v1=1)
            expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
            check('only selected mailbox receives complete score English',SAVE_RAM,expected)
            for addr,value in zip(RNG,rng): check('original score choice RNG preserved',addr,value)
            check('owned English capture leaves native temporary fields untouched',FREE,b'!'*200)
            readback(at,snapshot);comparisons += 1
        record({'native_score_template':case['template'],'passed':True})

    rejections = retries = 0;case = request['cases'][0]
    for home,points in (() if request.get('scheduler_only') else ((4,123456),(0xFFFFFFFF,123456),(homes[0],0xFFFFFFFF))):
        before = fixture(0,0,1,case);call(base+0x468,[home,points,0,series,0x11FC,0],0,proof,v1=0)
        check('invalid score input retains save',SAVE_RAM,before);check('invalid score retains capital',capital,word(1))
        rejections += 1
    for player in (() if request.get('scheduler_only') else (4,0xFFFFFFFF)):
        before = fixture(0,0,1,case);call(base+0x27D8,[player],0,proof,v1=0)
        check('invalid scoring entry retains save',SAVE_RAM,before);rejections += 1
    for fault in (() if request.get('scheduler_only') else ('disabled','unknown_series','semicolon','full_queue')):
        chosen = next(c for c in request['cases'] if c['template']==0x3A) if fault=='unknown_series' else dict(case)
        if fault=='semicolon':
            chosen['bits'] = f'{1<<17:016X}'
            chosen['seed'] = next(c['seed'] for c in request['cases'] if c['template']==0x3C)
        before = fixture(0,0,1,chosen,full=fault=='full_queue',queue_full=fault=='full_queue')
        if fault=='disabled': write(MODULE_RAM+68,bytes(4))
        if fault=='unknown_series': write(series,b'!'*10)
        call(base+0x468,[homes[0],chosen['points'],chosen['room'],series,0x11FC,0],0,proof,v1=0)
        check('rejected score publishes no partial mail',SAVE_RAM,before)
        if fault!='full_queue': check('failed score preparation retains capital',capital,word(1))
        rejections += 1
        write(series,bytes.fromhex(request['series'][longest]['native'])+b' '*6)
        write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        if fault=='disabled':
            # Restore only the source configuration. Retry keeps the actual RNG.
            number = selected_template(request,chosen,int.from_bytes(read(RNG[0],4),'big'))
            call(base+0x468,[homes[0],chosen['points'],chosen['room'],series,0x11FC,0],1,proof,v1=1)
            mail,snapshot = english(0,number,chosen['points'],1);at = HOME_MAILBOX+homes[0]*HOME_STRIDE
            expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
            check('resource retry publishes one complete score',SAVE_RAM,expected);readback(at,snapshot);retries += 1

    # Compare actual room evaluation, not a replacement score fixture routine.
    # Empty room input makes the expected native evaluation reproducible.
    fixture(1,4,1,case,score_room=True);write(TEST_STACK-276,bytes(164))
    points = call(original_at+0x27D8,[1],proof=oldproof)
    number = int.from_bytes(read(TEST_STACK-108,4),'big')
    record({'original_empty_room_score':points,'template':number})
    mail,snapshot = english(1,number,points,1);at = HOME_MAILBOX+homes[1]*HOME_STRIDE+4*164
    before = fixture(1,4,1,case,score_room=True)
    call(base+0x27D8,[1],points,proof,v1=1)
    expected = bytearray(before);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
    check('actual scoring returns original points and complete English',SAVE_RAM,expected);readback(at,snapshot)
    before = fixture(1,4,1,case,score_room=True);write(MODULE_RAM+68,bytes(4))
    call(base+0x27D8,[1],points,proof,v1=0)
    check('failed actual scoring retains save and original points',SAVE_RAM,before)
    write(MODULE_RAM+68,globals_before[MODULE_RAM+68]);rejections += 1

    scheduler_cases = 0
    before = fixture(1,4,1,case,score_room=True)
    call(0x8007D650,[],0);call(0x8009CA94,[1],1)
    probe = call(0x800BEBEC,[game,16976])
    record({'score_gamealloc_probe':probe,'game_allocator':f'{game+0x88:08X}'})
    if probe:
        call(0x800BEC3C,[game,probe]);scheduler_game = game
    else:
        # This checkpoint can have no free system arena after train startup.
        # Verify that actual allocation failure retains eligibility, then use
        # the scheduler's original documented NULL-game gameplay-arena path.
        call(SCHEDULER,[game]);check('actual overlay allocation failure retains eligibility',SAVE_RAM,before)
        check('failed allocation publishes no overlay owner',0x80107B50,bytes(4))
        rejections += 1;scheduler_cases += 1;scheduler_game = 0
    for fault in ('none','disabled','full_queue'):
        before = fixture(1,4,1,case,score_room=True,full=fault=='full_queue',queue_full=fault=='full_queue')
        if fault=='disabled': write(MODULE_RAM+68,bytes(4))
        call(SCHEDULER,[scheduler_game])
        expected = bytearray(before)
        if fault=='none':
            expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
            offset = 0x3588+homes[1]*HOME_STRIDE
            expected[offset+24:offset+28] = bytes.fromhex('07D00911');expected[offset+28] = 32
            check('real scheduler publishes complete score and native date flags',SAVE_RAM,expected);readback(at,snapshot)
            seed = tuple(read(addr,4) for addr in RNG);call(SCHEDULER,[scheduler_game])
            check('same-day score scheduler sends no duplicate',SAVE_RAM,expected)
            for addr,value in zip(RNG,seed): check('same-day score scheduler does not reroll',addr,value)
        else:
            check('failed real scheduler retains house update and mark date',SAVE_RAM,before);rejections += 1
        check('game allocator list retained',game+0x88,game_alloc)
        call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('scheduler releases gameplay-arena allocations',metrics,heap)
        write(MODULE_RAM+68,globals_before[MODULE_RAM+68])
        if fault=='disabled':
            call(SCHEDULER,[scheduler_game]);expected[at-SAVE_RAM:at-SAVE_RAM+164] = mail
            offset = 0x3588+homes[1]*HOME_STRIDE
            expected[offset+24:offset+28] = bytes.fromhex('07D00911');expected[offset+28] = 32
            check('real scheduler resource retry delivers and marks date',SAVE_RAM,expected);readback(at,snapshot)
            check('retry retains the game allocator list',game+0x88,game_alloc)
            call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('retry releases gameplay-arena allocations',metrics,heap);retries += 1
        scheduler_cases += 1
    call(0x8009C0C0,[metrics,metrics+4,metrics+8]);check('native heap accounting retained',metrics,heap)
    check('replacement scoring instructions retained',base,proof[1]);check('original comparison instructions retained',original_at,oldproof[1])
    check('installed scheduler retained',SCHEDULER,scheduler)
    for at in edges: check('fixture or stack guard',at,EDGE)
    check('resident guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    write(SAVE_RAM,saved);check('live save restored',SAVE_RAM,saved)
    for at,value in globals_before.items(): write(at,value);check('live global restored',at,value)
    call(0x8009C040,[allocation])
    return {'academy_score_comparisons':comparisons,'complete_readbacks':readbacks,'scheduler_cases':scheduler_cases,
            'scheduler_game_argument':scheduler_game,'game_allocation_available':bool(probe),'scheduler_only':bool(request.get('scheduler_only')),
            'rejections':rejections,'resource_retries':retries,'assertions':assertions,'creator_uploaded_bytes':0,
            'original_comparison_bytes':len(oldloaded),'normal_gameplay':False,'hardware_verified':False,
            'requires_checkpoint_restore':True}
