"""Native Resetti comparisons in an isolated cartridge-loaded actor fixture."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from npc_mail_show import ShowOverlay,relocate_verified_data
from resetti_replies import (VROM,RAM,RELOC_VROM,SOURCE_SHA256,RELOC_SHA256,FIRST,END,
                             TABLE,TABLE_RAM,CHANGES,patch)
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

SPEC=ShowOverlay(VROM,RAM,RELOC_VROM,3616,(3280,304,32,0,85),SOURCE_SHA256,RELOC_SHA256,0,0,0)
ACTOR_BYTES,REPLY,INDEX=0x958,0x94C,0x956
EDGE=b'EDGE'*4


def relocated(data,reloc,base):
    patch(data,reloc)
    output=bytearray(relocate_verified_data(SPEC,data,reloc,base))
    for address,before,after in CHANGES:
        if struct.unpack_from('>I',output,address-RAM)[0]!=before:
            raise ValueError('Resetti matcher instruction unexpectedly relocated')
        struct.pack_into('>I',output,address-RAM,after)
    output[TABLE_RAM-RAM:TABLE_RAM-RAM+len(TABLE)]=TABLE
    return bytes(output)


def cases(values):
    """Every fitting position, case variants, prefixes, and right-edge overreads."""
    result=[]
    def add(label,reply,index=0):
        if len(reply)!=10:raise ValueError('Reply fixture exceeds native storage')
        result.append((label,reply,index,int(any(word in reply for word in values))))
    for i,value in enumerate(values):
        for offset in range(11-len(value)):
            add(f'word {i} at {offset}',b'Z'*offset+value+b'Z'*(10-offset-len(value)))
        add(f'word {i} case variant',value.swapcase().ljust(10,b' '))
        add(f'word {i} incomplete prefix',value[:-1].ljust(10,b' '))
        # The final byte follows the ten-byte reply in the actor. It must not
        # complete a substring whose start lies beyond the last valid position.
        add(f'word {i} across input boundary',b'Z'*(11-len(value))+value[:-1],value[-1])
    for value in (b'          ',b'No        ',b'Okay      ',b'NO        ',b'ZZZZZZZZZZ'):
        add('neutral or partial reply',value)
    return result


def exercise(debug,request,record):
    read=debug.read_memory;assertions=0
    def write(at,value):
        debug.write_memory(at,value)
        record({'resetti_reply_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        nonlocal assertions
        actual=read(at,len(expected))
        record({'resetti_reply_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Resetti native mismatch: '+label)
        assertions+=1
    def call(at,args=(),expected=None,proof=None):
        result=debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Resetti native return {result["return_value"]} differs from {expected}')
        return result['return_value']
    data,reloc=bytes.fromhex(request['source']),bytes.fromhex(request['relocation'])
    patch(data,reloc)
    values=[bytes.fromhex(v)for v in request['values']]
    saved=read(SAVE_RAM,SAVE_BYTES)
    size=0x1E00;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Resetti fixture allocation failed')
    base,actor,staging=allocation+16,allocation+0x1000,allocation+0x19A0
    edges=(allocation,actor-16,actor+ACTOR_BYTES,staging-16,staging+32,
           allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x30)
    for at in edges:write(at,EDGE)
    call(0x800262D0,[VROM,VROM+SPEC.file_bytes,RAM,RAM+SPEC.resident_bytes,
                     base,base+SPEC.resident_bytes,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    loaded=relocated(data,reloc,base)
    check('complete cartridge actor and relocation',base,loaded)
    proof=(base,loaded[:SPEC.sections[0]])
    for i,value in enumerate(values):
        write(staging,b'G'*32)
        call(0x800C3F70,[staging,10,FIRST+i])
        check('complete loaded dictionary word and padding',staging,value.ljust(10,b' ')+b'G'*22)
    all_cases=cases(values)
    for label,reply,index,expected in all_cases:
        state=bytearray(b'Q'*ACTOR_BYTES);state[REPLY:REPLY+10]=reply;state[INDEX]=index
        write(actor,state)
        call(base+0x809B4C18-RAM,[actor],expected,proof)
        check('detector retains complete actor and reply',actor,state)
        record({'resetti_reply_case':label,'reply_sha256':sha256(reply),'expected_rude':expected,
                'index_byte':index,'passed':True})
    good_cases=0
    for number,raw in request['good_targets'].items():
        value=bytes.fromhex(raw).ljust(10,b' ')
        state=bytearray(b'Q'*ACTOR_BYTES);state[REPLY:REPLY+10]=value;state[INDEX]=int(number,16)-0x484
        write(actor,state)
        call(base+0x809B4BB8-RAM,[actor],1,proof)
        call(base+0x809B4D08-RAM,[actor],0,proof)
        check('exact good target accepted with actor retained',actor,state)
        # A changed final byte tests the complete ten-byte comparison, including
        # padding. It must not be accepted merely because the visible prefix fits.
        state[REPLY+9]=ord('Z');write(actor,state)
        expected=1 if any(word in bytes(state[REPLY:REPLY+10])for word in values)else 2
        call(base+0x809B4D08-RAM,[actor],expected,proof)
        check('incorrect padded target retained',actor,state)
        record({'resetti_good_target':number,'exact_result':0,'changed_tail_result':expected,'passed':True})
        good_cases+=1
    # The classifier must distinguish actual rude answers from neutral failures.
    for reply,expected in ((values[0].ljust(10,b' '),1),(b'Okay      ',2)):
        state=bytearray(b'Q'*ACTOR_BYTES);state[REPLY:REPLY+10]=reply;state[INDEX]=0
        write(actor,state);call(base+0x809B4D08-RAM,[actor],expected,proof)
        check('rude or neutral classification retains actor',actor,state)
    check('complete saved game retained',SAVE_RAM,saved)
    check('complete actor code and data retained',base,loaded)
    for at in edges:check('heap and stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'resetti_dictionary_words':32,'resetti_detector_cases':len(all_cases),
            'resetti_good_targets':good_cases,'resetti_classifier_cases':good_cases*2+2,
            'resetti_assertions':assertions,'allocation_freed':f'{allocation:08X}',
            'normal_editor':False,'requires_checkpoint_restore':True}
