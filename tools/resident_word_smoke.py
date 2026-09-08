"""Bounded native resident-word preparations, RNG comparisons, and full insertions."""

import struct

from aflib import sha256
from birthday_smoke import RNG,TEMP,RNG_START,RNG_END,RNG_SHA256
from flash_mail import SAVE_RAM,SAVE_BYTES
from fortune_smoke import seed_for
from resident_words import SPEC,HELPER,SCRATCH,relocated
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD
from textcodec import tokenize

WINDOW,SHOP,EDGE=0x80142410,0x80135C12,b'EDGE'*4
RANDOM_BASES=(0x414,0x434,0x464,0x4A0)
PREPARER_BASES={1:(0x219,0x1E5,0x334,0x314,0x414),3:(0x464,0x2F4,0x4A0)}


def random_cases(shared=False):
    from shared_npc_words import ORDINARY_BASES
    bases=RANDOM_BASES+(ORDINARY_BASES if shared else ())
    # Isolated fields exercise all five supported item slots; the outer native
    # preparations below separately prove the actual family-to-slot mapping.
    return tuple((position%5,base) for position,base in enumerate(bases))


def random_draw(seed,pool):
    final=(seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
    bits=(final>>9)|0x3F800000
    fraction=struct.unpack('>f',struct.pack('>I',bits))[0]-1.0
    return final,bits,int(struct.unpack('>f',struct.pack('>f',fraction*pool))[0])


def expected_preparer(entries,group,seed,shop):
    draws=[];values=[]
    if group==2:
        for minimum,maximum in ((1,10),(10,99),(0,9)):
            seed,bits,index=random_draw(seed,maximum-minimum);draws.append((seed,bits))
            values.append(str(minimum+index).encode())
        values.append(entries[0x454+shop])
        bases=(0x434,)
    else:
        bases=PREPARER_BASES[group]
    for base in bases:
        seed,bits,index=random_draw(seed,32);draws.append((seed,bits));values.append(entries[base+index])
    return values,draws


def prepared_tokens(entry,info,group):
    active=False;result=[]
    for token in tokenize(entry,info):
        if token.kind!='cmd':continue
        if token.data[1]==0x0C:active=token.data==bytes((0x7F,0x0C,9,0,group))
        elif active and 0x31<=token.data[1]<=0x35:result.append(token)
    return result


def exercise(debug,request,record):
    read=debug.read_memory;assertions=0;insertions=0;loads=0
    def write(at,value):
        debug.write_memory(at,value);record({'resident_word_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        nonlocal assertions
        actual=read(at,len(expected))
        record({'resident_word_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Native resident-word mismatch: '+label)
        assertions+=1
    def call(at,args=(),expected=None,proof=None):
        result=debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Native resident-word return differs')
        return result['return_value']
    def insert(entry,number,offset,value):
        nonlocal insertions
        write(cursor,struct.pack('>I',offset));write(WINDOW+0x28C,bytes(4))
        call(0x800A21C0,[WINDOW,cursor],0)
        expected=entry[:offset]+value+entry[offset+2:]
        check('complete insertion with surrounding text',message,struct.pack('>4I',1,number,len(expected),0)+expected)
        insertions+=1
        return expected
    def field(slot,value,code=None):
        entry=b'X'+bytes((0x7F,0x31+slot if code is None else code))+b'Y'
        write(message,struct.pack('>4I',1,0,len(entry),0)+entry)
        insert(entry,0,1,value)

    original,reloc=bytes.fromhex(request['source']),bytes.fromhex(request['relocation'])
    entries=[bytes.fromhex(v) for v in request['strings']]
    rng=bytes.fromhex(request['rng'])
    if len(rng)!=RNG_END-RNG_START or sha256(rng)!=RNG_SHA256:raise ValueError('Changed RNG fixture')
    check('unchanged complete native RNG',RNG_START,rng)
    saved=read(SAVE_RAM,SAVE_BYTES);globals_before={at:read(at,4) for at in (RNG,TEMP)}
    shop_before=read(SHOP,2);shop_bits=struct.unpack('>H',shop_before)[0]
    size=0x7000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Resident-word fixture allocation failed')
    base,message,staging,cursor,manager=(allocation+o for o in (0x10,0x5500,0x5980,0x59C0,0x5A00))
    scratch=base+SCRATCH-SPEC.ram;relocation_buffer=base+SPEC.resident_bytes
    if relocation_buffer+len(reloc)+16>message-16:raise ValueError('Resident-word fixture overlaps relocation workspace')
    edges=(allocation,relocation_buffer+len(reloc),message-16,message+0x410,staging-16,staging+32,
           cursor-16,cursor+16,manager+0x200,allocation+size-16,TEST_STACK-0x800,TEST_STACK+0x30)
    for at in edges:write(at,EDGE)
    actual_reloc=bytes.fromhex(request['installed_relocation'])
    call(0x800262D0,[SPEC.vrom,SPEC.vrom+SPEC.file_bytes,SPEC.ram,SPEC.ram+SPEC.resident_bytes,
                    base,relocation_buffer,len(actual_reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    loaded=relocated(original,reloc,base,module=request['module'],dates=request['dates'])
    check('complete cartridge-loaded actor and BSS',base,loaded)
    check('complete provided relocation workspace',relocation_buffer,actual_reloc)
    proof=(base,loaded[:SPEC.sections[0]])
    write(WINDOW+12,struct.pack('>I',message))

    # Every selected English random word passes through the real native helper.
    cases=random_cases(request.get('shared_npc_words',False))
    for index in range(32):
        seed,final,bits=seed_for(index)
        write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4));call(RNG_START,proof=(RNG_START,rng))
        check('independent original RNG state',RNG,struct.pack('>I',final))
        check('independent original RNG float',TEMP,struct.pack('>I',bits))
        for slot,start in cases:
            value=entries[start+index];before=read(WINDOW,0x330)
            write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4))
            call(base+HELPER-SPEC.ram,[scratch,slot,start,0x42000000],proof=proof)
            check('exactly one original random draw',RNG,struct.pack('>I',final))
            check('unchanged native random fraction',TEMP,struct.pack('>I',bits))
            check('complete sixteen-byte temporary',scratch,value.ljust(16,b' '))
            expected=bytearray(before);expected[0x100+slot*10:0x10A+slot*10]=value[:10].ljust(10,b' ')
            check('only selected native compatibility field changes',WINDOW,expected)
            field(slot,value)
            record({'resident_word_case':f'{start+index:04X}','slot':slot,'pool_index':index,'passed':True})

    # Real outer preparations preserve all original draw counts and numbers.
    preparations=0;original_draws=32
    for group,shop in ((1,0),(2,0),(2,1),(2,2),(2,3),(3,0)):
        word=(shop_bits&0x3FFF)|(shop<<14);write(SHOP,struct.pack('>H',word))
        seed=seed_for(31)[0];values,draws=expected_preparer(entries,group,seed,shop)
        write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4))
        for final,bits in draws:
            call(RNG_START,proof=(RNG_START,rng));original_draws+=1
            check('independent outer-preparer RNG state',RNG,struct.pack('>I',final))
            check('independent outer-preparer RNG float',TEMP,struct.pack('>I',bits))
        write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4))
        state=bytearray(0x200);struct.pack_into('>HH',state,0x1AC,9,group);write(manager,state)
        before=read(WINDOW,0x330)
        call(base+0x809215E4-SPEC.ram,[manager],proof=proof)
        check('complete manager retained',manager,state)
        check('outer preparer original RNG state',RNG,struct.pack('>I',draws[-1][0]))
        check('outer preparer original random fraction',TEMP,struct.pack('>I',draws[-1][1]))
        expected=bytearray(before)
        for slot,value in enumerate(values):expected[0x100+slot*10:0x10A+slot*10]=value[:10].ljust(10,b' ')
        check('outer preparer changes only selected compatibility fields',WINDOW,expected)
        scratch_value=values[-1].ljust(16,b' ')
        check('outer preparer complete final temporary',scratch,scratch_value)
        if group==2:
            # Two 24-byte dispatcher frames precede the expanded 56-byte local.
            check('complete expanded shop-name local',TEST_STACK-24-24-56+0x24,values[3].ljust(16,b' '))
        for slot,value in enumerate(values):field(slot,value)
        expected_saved=bytearray(saved);struct.pack_into('>H',expected_saved,SHOP-SAVE_RAM,word)
        check('saved game unchanged except explicit test shop level',SAVE_RAM,expected_saved)
        record({'resident_word_preparer':group,'shop_level':shop,'draws':len(draws),'passed':True})
        preparations+=1
        if group==2 and shop!=3:continue
        for number,raw in request['messages'][str(group)].items():
            entry=bytes.fromhex(raw);number=int(number,16)
            call(0x8009E558,[message,number,0],1);loads+=1
            check('complete resident message from cartridge',message,struct.pack('>4I',1,number,len(entry),0)+entry)
            expected=entry
            for token in reversed(prepared_tokens(entry,request['info'],group)):
                slot=token.data[1]-0x31
                if slot>=len(values):raise ValueError('Resident message uses an unprepared field')
                expected=insert(expected,number,token.offset,values[slot])

    # These unchanged category callers use free-string 11, not an extended item.
    for index in range(0x55D,0x561):
        value=entries[index];write(staging,b'G'*32)
        call(0x800C3F70,[staging,10,index])
        check('complete category load and adjacent guard',staging,value.ljust(10,b' ')+b'G'*22)
        before=read(WINDOW,0x330);call(0x8009D6D0,[WINDOW,11,staging,10])
        expected=bytearray(before);expected[0x38+110:0x38+120]=value.ljust(10,b' ')
        check('category setter only changes free-string 11',WINDOW,expected)
        field(0,value,code=0x37)
    write(SHOP,shop_before)
    for at,value in globals_before.items():write(at,value)
    check('complete saved game retained',SAVE_RAM,saved)
    expected_actor=bytearray(loaded);at=SCRATCH-SPEC.ram;expected_actor[at:at+16]=scratch_value
    check('complete actor BSS retained except expected temporary',base,expected_actor)
    check('complete relocation workspace retained',relocation_buffer,actual_reloc)
    for at in edges:check('heap and native stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'resident_random_word_preparations':len(cases)*32,'resident_outer_preparations':preparations,
            'resident_independent_rng_calls':original_draws,'resident_complete_message_loads':loads,
            'resident_field_insertions':insertions,'resident_word_assertions':assertions,
            'normal_gameplay':False,'native_category_selection_executed':False,'requires_checkpoint_restore':True}
