"""Run installed HRA model mail through native selection, creation, and delivery.

Controlled house scores and mailbox/queue contents are disposable fixtures.
Actual native code runs; this is not an ordinary room-scoring playthrough.
"""
import json
import re
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom,sha256
from academy_smoke import PLAYER,PRIVATE,TIME,EMPLOYMENT,RNG,FREE
from flash_mail import SAVE_RAM,SAVE_BYTES
from mail_record import Field,Record,pack
from mail_storage import HOME_MAILBOX,HOME_STRIDE,QUEUE
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK
from v3_asset_loader import BLOB
from v3_npc_draw_smoke import boot_proofs
from villager_event_scenario import IDENTITIES
import v3_hra_rewards as rewards

CAPITAL,SESSION=0x80199F64,0x80199F5C


def exercise(debug, rom_path, record, *, deliver_for_save=False):
    path=Path(rom_path);image=path.read_bytes()
    report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:
        raise ValueError('HRA reward check requires its exact current cartridge')
    rewards.verify_installed_items(image,report)
    files=by_vrom(image);hr=report['hra'];reward=hr['model_rewards']
    rows=reward['source']['rewards'];boot=boot_proofs(image)
    imports={r['item_id']:r for r in report['furniture']['imports']}
    if not {f'{r["item"]:04X}' for r in rows}<=imports.keys():
        raise ValueError('HRA reward check needs both complete admitted models')
    flags=[int(imports[f'{r["item"]:04X}']['profile_ram'],16)-4 for r in rows]
    read,write=debug.read_memory,debug.write_memory
    assertions=calls=0
    def check(label,address,expected):
        nonlocal assertions
        actual=read(address,len(expected));passed=actual==expected
        record(dict(hra_reward_check=label,address=f'{address:08X}',bytes=len(expected),
            expected_sha256=sha256(expected),actual_sha256=sha256(actual),passed=passed))
        if not passed:
            differences=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
            record(dict(hra_reward_differences=differences[:24]))
            raise ValueError('Native HRA reward mismatch: '+label)
        assertions+=1
    def call(address,args=(),proof=None,wanted=None):
        nonlocal calls
        result=debug.call(f'{address:08X}',list(args),return_address=MODULE_RAM+0x6480,
                          verified_code=proof or boot.get(address))
        record(result);calls+=1
        if wanted is not None and (result['return_value'],result['return_value_v1'])!=wanted:
            # Capture the actual creator allocation before its range check.
            # This diagnoses a failed native path; it never changes instructions
            # or makes a failed delivery count as a passing reward case.
            stop=0x80197DBC
            expected=bytes.fromhex('3c027fe6244237203c03002602621021')
            if read(stop,len(expected))==expected:
                breakpoint=f'0,{stop:x},4'
                if debug.command('Z'+breakpoint)!='OK':
                    raise ValueError('HRA creator diagnostic breakpoint rejected')
                try:
                    debug.call(f'{address:08X}',list(args),
                        return_address=MODULE_RAM+0x6480,
                        verified_code=proof or boot.get(address))
                except ValueError as error:
                    observed=re.search(r'after_registers=([0-9a-fA-F]{1136})',str(error))
                    if observed:
                        raw=observed.group(1)
                        values=[int(raw[i:i+16],16)&0xFFFFFFFF for i in range(0,len(raw),16)]
                        record(dict(hra_creator_allocation_diagnostic=True,
                            pc=f'{values[37]:08X}',allocation=f'{values[19]:08X}',
                            allocation_bytes=values[16],
                            existing_heap_end='80400000',
                            instructions_changed=False,delivery_passed=False))
                    else:
                        raise
                finally:
                    debug.command('z'+breakpoint)
            raise ValueError('Native HRA reward returns the wrong delivery result')
        return result['return_value']
    def put(address,value):write(address,struct.pack('>I',value))
    saved=read(SAVE_RAM,SAVE_BYTES)
    globals_before={at:read(at,n) for at,n in ((PLAYER,1),(PRIVATE,4),(TIME,8),
        (EMPLOYMENT,4),(FREE,200),(CAPITAL,4),(SESSION,4),(MODULE_RAM+68,4),
        *((at,4) for at in RNG),*((at,4) for at in flags))}
    check('no preceding mail capture',SESSION,bytes(4))
    size=0xA000;allocation=call(0x8009BFC0,[size])
    workspace=report['equipment_resources']['scene_arena']['workspace']
    borrowed=report['equipment_resources']['scene_arena']['borrowed_state']['ram']
    lower=MODULE_RAM+RESERVATION<=allocation<=0x80400000-size
    upper=(read(borrowed,4)==struct.pack('>I',1) and
        workspace['free_block']+16<=allocation<=workspace['end_guard']-size)
    if allocation&15 or not(lower or upper):
        raise ValueError('HRA reward fixture exceeds native heap')
    scene_edges=(workspace['front_guard'],workspace['end_guard']) if upper else ()
    for at in scene_edges:check('exclusive scene-workspace guard',at,bytes.fromhex('AF53434E')*4)
    root,series,pid,empty=(allocation+n for n in (16,0x9000,0x9020,0x9040))
    data,reloc=(files[v].extract(image) for v in (rewards.owner.NEW_VROM,rewards.owner.NEW_RELOC))
    loaded=relocate_verified_data(SimpleNamespace(ram=rewards.owner.RAM,
        resident_bytes=len(data),sections=struct.unpack_from('>5I',reloc)),data,reloc,root,
        memory_end=0x80800000 if upper else 0x80400000)
    call(0x800262D0,[rewards.owner.NEW_VROM,rewards.owner.NEW_VROM+len(data),
        rewards.owner.RAM,rewards.owner.RAM+len(data),root,root+len(data),len(reloc)])
    check('complete cartridge-loaded and relocated HRA owner',root,loaded)
    start=rewards.SEND-rewards.owner.RAM;end=rewards.SEND_END-rewards.owner.RAM
    sender=root+start;proof=(sender,loaded[start:end])
    selector=root+BIND_SELECTOR-rewards.owner.RAM
    selector_proof=(selector,loaded[BIND_SELECTOR-rewards.owner.RAM:BIND_SELECTOR_END-rewards.owner.RAM])
    names=files[rewards.mail.VROM].extract(image)
    key=names[hr['score_letters']['name_table_address']-rewards.mail.RAM:][:10]
    write(series,key+b' '*6);write(empty,bytes(164));call(0x8009C384,[empty])
    cleared=read(empty,164);occupied=bytearray(cleared);occupied[38]=3
    edge=b'V3HM'*4
    # The retained English formatter alone uses 1,224 stack bytes. Its path
    # through restore (264), generation (216), score creation (120), loader
    # (112), and this send wrapper (256) exceeds a 2-KiB test guard. Reserve
    # 4 KiB inside the existing isolated scratch stack, as other mail checks do.
    guards=(allocation,series-16,empty+164,allocation+size-16,TEST_STACK-0x1000,TEST_STACK+0x40)
    for at in guards:write(at,edge)
    bits=root+0x80929628-rewards.owner.RAM;write(bits,bytes(8))
    if deliver_for_save:
        # The existing loaded player's real house/mailbox receives the two
        # original rewards. Only supplied scores are controlled; no mailbox,
        # identity, earned flag, RNG, time, or import selection is fabricated.
        private=int.from_bytes(globals_before[PRIVATE],'big')
        identity=read(private,16)
        home=next((i for i in range(4)
            if saved[0x3588+i*HOME_STRIDE:0x3598+i*HOME_STRIDE]==identity),None)
        if home is None or globals_before[PLAYER][0]>=4:
            raise ValueError('Reward persistence needs the actual resident and matching house')
        flag_at=0x3588+home*HOME_STRIDE+0x1C
        if saved[flag_at]&12 or any(read(at,4)!=struct.pack('>I',1) for at in flags):
            raise ValueError('Reward persistence needs both selected, unearned source rewards')
        destination=HOME_MAILBOX+home*HOME_STRIDE
        slots=[i for i in range(10) if read(destination+i*164+38,1)==cleared[38:39]]
        if len(slots)<2:raise ValueError('Actual home mailbox lacks two free reward slots')
        expected=bytearray(saved)
        try:
            for slot,gift in zip(slots,rows):
                points=gift['points']
                call(sender,[home,points,0,series,0x11FC,0],proof,(1,1))
                mail=bytearray(164);mail[:16]=identity;mail[18:30]=b' '*12
                mail[30:35]=b'\xff'*5;mail[39:42]=bytes((128,6,51))
                struct.pack_into('>H',mail,36,gift['item'])
                mail[42:]=pack(Record(4,0,(gift['template'],),
                    ((0,Field(f'{points:,}'.rjust(10).encode())),),False))
                offset=destination-SAVE_RAM+slot*164
                expected[offset:offset+164]=mail;expected[flag_at]|=gift['flag']
                check('persistent source reward: complete town/mail/house flags',SAVE_RAM,expected)
                check('persistent reward detaches mail capture',SESSION,bytes(4))
                record(dict(hra_reward_for_save=gift,home=home,slot=slot,
                    native_delivery=True,actual_house_identity=True,controlled_score=True))
            for at in guards:check('persistent reward fixture boundary',at,edge)
            for at in scene_edges:check('persistent reward scene guard',at,bytes.fromhex('AF53434E')*4)
            for at in (PRIVATE,PLAYER,TIME,EMPLOYMENT,*flags):
                check('persistent rewards retain original player/time/selection',at,globals_before[at])
        finally:
            call(0x8009C040,[allocation])
        return dict(hra_rewards_ready_for_native_save=True,native_calls=calls,assertions=assertions,
            home=home,mailbox_slots=slots[:2],complete_rewarded_town_sha256=sha256(expected),
            controlled_scores=True,ordinary_room_scoring_tested=False,
            original_source_acquisition_rules=True,requires_checkpoint_restore=True)
    cases=[('below',69999,(1,1),0,0,False,False,False,None),
        ('first threshold',70000,(1,1),0,1,False,False,False,rows[0]),
        ('first priority',100000,(1,1),0,2,False,False,False,rows[0]),
        ('second after first',100000,(1,1),8,3,False,False,False,rows[1]),
        ('second independent',100000,(0,1),0,0,False,False,False,rows[1]),
        ('first independent',100000,(1,0),0,3,False,False,False,rows[0]),
        ('neither selected',100000,(0,0),0,1,False,False,False,None),
        ('first earned',70000,(1,1),8,2,False,False,False,None),
        ('both earned',100000,(1,1),12,3,False,False,False,None),
        ('full mailbox refusal',70000,(1,1),0,0,True,False,False,rows[0]),
        ('full mailbox and queue refusal',70000,(1,1),0,1,True,True,False,rows[0]),
        ('creator failure',100000,(1,1),8,2,False,False,True,rows[1])]
    try:
        for label,points,selected,earned,home,full,queue_full,disabled,gift in cases:
            state=bytearray(saved)
            for slot in range(4):
                at=0x3588+slot*HOME_STRIDE
                state[at:at+16]=IDENTITIES[slot];state[at+0x1C]=0xF3
                at=HOME_MAILBOX-SAVE_RAM+slot*HOME_STRIDE
                state[at:at+1640]=bytes(occupied)*10
            flag_at=0x3588+home*HOME_STRIDE+0x1C;state[flag_at]|=earned
            destination=HOME_MAILBOX+home*HOME_STRIDE
            if not full:state[destination-SAVE_RAM:destination-SAVE_RAM+164]=cleared
            at=QUEUE-SAVE_RAM;state[at:at+820]=(bytes(occupied) if queue_full else cleared)*5
            state[at-8:at]=struct.pack('>4H',5 if queue_full else 0,0,0,0)
            write(SAVE_RAM,state);write(pid,IDENTITIES[home]);put(PRIVATE,pid)
            write(PLAYER,bytes((home,)));write(TIME,bytes.fromhex('00000011010907D0'))
            put(EMPLOYMENT,0);put(CAPITAL,0)
            for address,enabled in zip(flags,selected):put(address,enabled)
            put(RNG[0],123);put(RNG[1],0)
            ordinary=call(selector,[points,0],selector_proof)
            wanted_rng=[read(at,4) for at in RNG]
            put(RNG[0],123);put(RNG[1],0)
            if disabled:put(MODULE_RAM+68,0)
            # Both original post-office readers count the destination mailbox
            # before accepting queue mail. A full mailbox is a refusal even when
            # the queue has room; do not change that rule to satisfy this test.
            accepted=not(full or queue_full or disabled)
            call(sender,[home,points,0,series,0x11FC,0],proof,(int(accepted),int(accepted)))
            expected=bytearray(state)
            if accepted:
                number=gift['template'] if gift else ordinary
                fields=((0,Field(f'{points:,}'.rjust(10).encode())),) if gift else (
                    (0,Field(f'{points:,}'.rjust(10).encode())),(3,Field(b'2000')),
                    (4,Field(b'September')),(5,Field(b'17th')))
                mail=bytearray(164);mail[:16]=IDENTITIES[home];mail[18:30]=b' '*12
                mail[30:35]=b'\xff'*5;mail[39:42]=bytes((128,6,51))
                if gift:
                    struct.pack_into('>H',mail,36,gift['item']);expected[flag_at]|=gift['flag']
                mail[42:]=pack(Record(4,0,(number,),fields,False))
                at=QUEUE-SAVE_RAM if full else destination-SAVE_RAM
                expected[at:at+164]=mail
                if full:expected[QUEUE-SAVE_RAM-8:QUEUE-SAVE_RAM-2]=struct.pack('>3H',1,0,1)
            check(label+': complete town, delivered letter, and retained house flags',SAVE_RAM,expected)
            for address,value in zip(RNG,wanted_rng):check(label+': original RNG draw',address,value)
            check(label+': detached capture',SESSION,bytes(4))
            put(MODULE_RAM+68,int.from_bytes(globals_before[MODULE_RAM+68],'big'))
            record(dict(hra_reward_case=label,home=home,points=points,selected=selected,
                earned=earned,gift=gift,accepted=accepted,passed=True))
        check('unchanged complete installed send instructions',sender,proof[1])
        for at in guards:check('fixture boundary',at,edge)
        for at in scene_edges:check('retained scene-workspace guard',at,bytes.fromhex('AF53434E')*4)
    finally:
        write(SAVE_RAM,saved)
        for at,value in globals_before.items():write(at,value)
        call(0x8009C040,[allocation])
    check('complete original town restored',SAVE_RAM,saved)
    return dict(hra_reward_native_cases=len(cases),native_calls=calls,assertions=assertions,
        controlled_scores=True,ordinary_room_scoring_tested=False,
        native_mailbox_and_queue=True,requires_checkpoint_restore=True)


BIND_SELECTOR,BIND_SELECTOR_END=0x80925BB8,0x80925D1C
