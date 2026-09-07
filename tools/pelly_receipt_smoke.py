"""Isolated native Pelly receipt handlers, not a normal gameplay animation test."""

import struct

from aflib import sha256
from mail_storage import PELLY_RAM
from mail_view_smoke import pointer
from runtime_layout import MODULE_RAM, RESERVATION, TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

RELOC_SHA256 = 'ac371d4f4c5d0c87f2ffb3d56bbddfdd7f1384ecca4cca5d3e769e4306241d2f'
EDGE = b'EDGE'*4
ANIMALS, POPULATION_BYTES = 0x80130DB8, 0x528*15
SOURCE = TEST_RETURN+0x300


def relocated_pelly(data,reloc,base):
    """Independent model of the original loader for this exact relocation list.

    Section offsets and the HI register cache follow native DoRelocation. The
    source relocation digest limits this model to Pelly, including its data
    pointers and signed load immediates; it is not a general overlay linker.
    """
    if (len(data) != 0x1E00 or sha256(reloc) != RELOC_SHA256 or base & 15
            or not MODULE_RAM+RESERVATION <= base <= 0x80400000-len(data)):
        raise ValueError('Invalid Pelly relocation input')
    text,writable,rodata,bss,count = struct.unpack_from('>5I',reloc)
    if (text,writable,rodata,bss,count) != (0x1BE0,0x1C0,0x60,0,148):
        raise ValueError('Unexpected Pelly relocation sections')
    result,high = bytearray(data),{}
    starts,sizes = (0,0,text,text+writable),(0,text,writable,rodata)
    def store(offset,word): struct.pack_into('>I',result,offset,word&0xFFFFFFFF)
    def target(value):
        if not PELLY_RAM <= value < PELLY_RAM+len(data):
            raise ValueError('Pelly relocation target is outside its original overlay')
        return base+value-PELLY_RAM
    for (record,) in struct.iter_unpack('>I',reloc[20:20+count*4]):
        section,kind,offset = record>>30,(record>>24)&63,record&0xFFFFFF
        if section == 0 or offset&3 or offset+4 > sizes[section]:
            raise ValueError('Invalid Pelly relocation location')
        at = starts[section]+offset
        word = struct.unpack_from('>I',result,at)[0]
        if kind == 2:
            if not word&0x0F000000: store(at,target(word))
        elif kind == 4:
            if word>>26 not in (2,3): raise ValueError('Invalid relocated Pelly jump')
            store(at,(word&0xFC000000)|((target(0x80000000|((word&0x3FFFFFF)<<2))&0xFFFFFFF)>>2))
        elif kind == 5:
            if word>>26 != 15: raise ValueError('Invalid relocated Pelly high instruction')
            high[(word>>16)&31] = at,word
        elif kind == 6:
            register = (word>>21)&31
            if register not in high: raise ValueError('Unpaired Pelly low relocation')
            hi_at,hi_word = high[register]
            value = ((hi_word&0xFFFF)<<16)+(word&0xFFFF)-(0x10000 if word&0x8000 else 0)
            if not value&0x0F000000:
                value = target(value)
                store(hi_at,(hi_word&0xFFFF0000)|(((value+0x8000)>>16)&0xFFFF))
                store(at,(word&0xFFFF0000)|(value&0xFFFF))
        else:
            raise ValueError('Unsupported Pelly relocation')
    return bytes(result)


def exercise(debug,request,record):
    from emulator_smoke import message_snapshot
    read = debug.read_memory
    def write(address,data):
        debug.write_memory(address,data)
        record({'test_only_ram_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        actual = read(address,len(expected))
        if actual != expected:
            differences = [(i,a,b) for i,(a,b) in enumerate(zip(actual,expected)) if a != b]
            record({'pelly_check':label,'assertion':'failed','address':f'{address:08X}',
                    'differences':differences[:32]})
            raise ValueError(f'Pelly {label}: {len(differences)} differences, first {differences[:16]}')
        record({'pelly_check':label,'assertion':'passed','address':f'{address:08X}',
                'bytes':len(expected),'sha256':sha256(actual)})
    def call(address,args,expected=None,proof=None):
        result = debug.call(f'{address:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Pelly native {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    for address,data in request['guards'].items():
        check('instruction guard',int(address,16),bytes.fromhex(data))
    private = pointer(debug,0x80136FD8,0xBD0)
    game = pointer(debug,0x8010EF90,0x1DAC)
    submenu,staged = game+0x1CBC,game+0x1CF4
    original_private = read(private,0xBD0)
    original_population = read(ANIMALS,POPULATION_BYTES)
    original_counters = read(0x80135E04,6)
    original_submenu = read(submenu,0xE4)
    original_handover = read(0x80136F34,4)
    player = read(0x80136EA3,1)[0]
    if player >= 4: raise ValueError('Pelly probes require a local player')
    call(0x8007D2B8,[0x20000002+player])
    call(0x8007D6E0,[],0)
    slots = [i for i in range(15) if 0xE000 <= int.from_bytes(original_population[i*0x528:i*0x528+2],'big') < 0xE0D8]
    if not slots: raise ValueError('No local NPC for Pelly probes')
    animal = ANIMALS+slots[0]*0x528
    allocation = call(0x8009BFC0,[0x2AB0])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x2AB0:
        raise ValueError('Pelly overlay test allocation failed')
    base,actor,handover = allocation+16,allocation+0x2090,allocation+0x2A10
    write(allocation,EDGE)
    write(allocation+0x2AA0,EDGE)
    loader = bytes.fromhex(request['loader'])
    call(0x800262D0,[0x8A6C10,0x8A8A10,PELLY_RAM,PELLY_RAM+0x1E00,base,base+0x1E00,0x270],
         proof=(0x800262D0,loader))
    expected_overlay = relocated_pelly(bytes.fromhex(request['overlay']),bytes.fromhex(request['relocation']),base)
    check('complete natively relocated overlay',base,expected_overlay)
    proof = (base,expected_overlay[:0x1BE0])
    # States three and six have native no-op initializers; eight loads the
    # hand-back introduction, and ten clears demo order nine. Exercise these
    # real initializers, without advancing a synthetic actor's animation.
    setup = base+0x809C4E74-PELLY_RAM
    write(handover,bytes(32))
    write(0x80136F34,struct.pack('>I',handover))
    write(TEST_STACK-0xC00,EDGE)
    write(TEST_STACK+0x30,EDGE)
    def message(number):
        observed = message_snapshot(debug)
        expected = request['messages'][f'{number:04X}']
        if (observed.get('loaded') != 1 or observed.get('message_id') != f'{number:04X}'
                or observed.get('data') != expected):
            raise ValueError(f'Pelly message {number:04X} does not match complete ROM record: {observed}')
        record({'pelly_message':f'{number:04X}','complete_data':True,'bytes':len(bytes.fromhex(expected))})
    def reset():
        write(private,original_private)
        write(ANIMALS,original_population)
        write(0x80135E04,original_counters)
        write(submenu,original_submenu)
    cases = 0
    for case in request['cases']:
        for sister in (0,1):
            for pocket in (range(10) if case.get('reject') else (0,9)):
                reset()
                mail = bytearray.fromhex(case['mail'])
                mail[0x12:0x22] = original_private[:16]
                mail[0x22],mail[0x26] = 0,0
                write(SOURCE,mail)
                call(0x8009C70C,[SOURCE,animal])
                mail = read(SOURCE,164)
                accepted = not case.get('reject',False)
                # Compare actor delivery with the already tested lower-level
                # result from exactly the same pre-send NPC/player/RTC state.
                call(0x800B6A3C,[SOURCE,0],int(accepted))
                expected_population = read(ANIMALS,POPULATION_BYTES)
                expected_counters = read(0x80135E04,6)
                reset()
                destination = private+0x40A+pocket*164
                write(destination,mail)
                call(0x8009C67C,[staged,destination])
                call(0x8009C384,[destination])
                private_after_removal = read(private,0xBD0)
                write(submenu+0xDC,bytes((0,7,0,pocket)))
                write(actor,bytes(0x960))
                write(actor+0x724,bytes((sister,)))
                write(actor+0x938,struct.pack('>4I',0xCCCCCCCC,0xCCCCCCCC,0,setup))
                call(base+0x809C471C-PELLY_RAM,[actor,game],proof=proof)
                expected_private = bytearray(private_after_removal)
                if not accepted:
                    restored = bytearray(mail);restored[0x26] = 1
                    expected_private[0x40A+pocket*164:0x40A+(pocket+1)*164] = restored
                check('complete player pockets and state',private,bytes(expected_private))
                check('complete NPC population versus receipt baseline',ANIMALS,expected_population)
                check('delivery counts versus receipt baseline',0x80135E04,expected_counters)
                call(0x8009C384,[SOURCE])
                check('staged source cleared only after send or pocket return',staged,read(SOURCE,164))
                check('actor selected action',actor+0x938,struct.pack('>I',3 if accepted else 6))
                check('actor subsequent state',actor+0x93C,struct.pack('>I',5 if accepted else 0xCCCCCCCC))
                check('actor refusal reason',actor+0x949,bytes((0 if accepted else 4,)))
                message((0x8B9 if accepted else 0x8E1)+sister)
                if not accepted:
                    call(setup,[actor,game,8],proof=proof)
                    message(0x8E1+sister)
                    check('hand-back initializer action',actor+0x938,struct.pack('>I',8))
                    call(base+0x809C3F0C-PELLY_RAM,[actor,game],proof=proof)
                    message(0x2DE8+sister)
                    check('after-refusal action',actor+0x938,struct.pack('>I',10))
                    check('refusal explanation retains complete returned letter',private,bytes(expected_private))
                check('inactive score context',int(request['context'],16),bytes(4))
                check('low stack guard',TEST_STACK-0xC00,EDGE)
                check('high stack guard',TEST_STACK+0x30,EDGE)
                check('allocation start',allocation,EDGE)
                check('allocation end',allocation+0x2AA0,EDGE)
                check('module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
                record({'native_pelly_receipt_case':case['label'],'sister':sister,'pocket':pocket,
                        'accepted':accepted,'normal_gameplay_animation':False,'requires_checkpoint_restore':True})
                cases += 1
    # Preserve each supported hand-back reason, then every refusal selector.
    for sister in (0,1):
        write(actor+0x724,bytes((sister,)))
        for reason in (1,2,3,4):
            write(actor+0x949,bytes((reason,)))
            call(setup,[actor,game,8],proof=proof)
            message({1:0x8E1,2:0x8B5,3:0x1BD7,4:0x8E1}[reason]+sister)
        for reason in (0,1,2,3,4,5,127,255):
            write(actor+0x949,bytes((reason,)))
            call(base+0x809C3F0C-PELLY_RAM,[actor,game],proof=proof)
            message({2:0x2DDA,3:0x2DDE,4:0x2DE8}.get(reason,0x2DDC)+sister)
    check('unchanged loaded overlay',base,expected_overlay)
    reset()
    write(0x80136F34,original_handover)
    call(0x8009C040,[allocation])
    return {'native_pelly_receipt_cases':cases,'refusal_selector_cases':16,'handback_initializer_cases':8,
            'scope':'Native actor receipt/refusal handlers and action initializers; no animation or normal gameplay claim',
            'requires_checkpoint_restore':True,'game_save_validation':False}
