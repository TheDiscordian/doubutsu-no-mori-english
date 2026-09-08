"""Birthday requests through the real cartridge-loaded ordinary dispatcher."""

import calendar
import struct

from aflib import sha256
from birthday_fields import SPEC, REQUEST
from runtime_layout import MODULE_RAM, RESERVATION
from textcodec import tokenize

ANIMALS = 'Rat Ox Tiger Rabbit Dragon Snake Horse Ram Monkey Rooster Dog Boar'.split()
SIGNS = 'Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces'.split()
ENDS = (19,18,20,19,20,21,22,22,22,23,21,21)
SEEDS = (0xBC092F7A,0x795BB045,0xD31E9017,0xBD5280CB,0x6DF7DF3E,0x582BCFF2,
         0x850D3FDB,0xF3051F19,0xDD390FCD,0x36FBEF9F,0xF44E706A,0x4E11503C)
RNG, TEMP, PRIVATE, ORDERS, WINDOW = 0x8003C590,0x800419F0,0x80136FD8,0x80104A70,0x80142410
RNG_START, RNG_END = 0x8002C9AC,0x8002CA00
RNG_SHA256 = '54eaafabfeeb3e70158a80e2e61b775f4340c6620b3984238268d2765f34bb56'
EDGE = b'EDGE'*4


def random_draw(seed):
    seed = (seed*0x19660D+0x3C6EF35F)&0xFFFFFFFF
    bits = (seed>>9)|0x3F800000
    fraction = struct.unpack('>f',struct.pack('>I',bits))[0]-1.0
    scaled = struct.unpack('>f',struct.pack('>f',fraction*12.0))[0]
    return seed,bits,int(scaled)


def expected_fields(month, day, animal, sign):
    selected = next((i for i,last in enumerate(ENDS)
                     if month < i+1 or month == i+1 and day <= last),0)
    suffix = 'th' if 11 <= day <= 13 else {1:'st',2:'nd',3:'rd'}.get(day%10,'th')
    return [v.encode('ascii') for v in (ANIMALS[animal],SIGNS[sign],SIGNS[(selected-3)%12],
            calendar.month_name[month],str(day)+suffix)]


def prepared_tokens(data, info):
    """Do not interpret an earlier item or a later lucky colour as a birthday."""
    active = False
    result = []
    for token in tokenize(data,info):
        if token.kind != 'cmd': continue
        if token.data[1] == 0x0C:
            active = token.data == REQUEST
        elif active and 0x31 <= token.data[1] <= 0x35:
            result.append(token)
    return result


def exercise(debug, request, record, base, proof):
    read = debug.read_memory
    def write(at,value):
        debug.write_memory(at,value)
        record({'birthday_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        actual = read(at,len(expected))
        record({'birthday_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual != expected: raise ValueError('Birthday native mismatch: '+label)
    def call(at,args=(),expected=None,code=None):
        result = debug.call(f'{at:08X}',args,verified_code=code);record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Birthday native return differs')
        return result['return_value']
    rng_code = bytes.fromhex(request['birthday_rng'])
    if len(rng_code) != RNG_END-RNG_START or sha256(rng_code) != RNG_SHA256:
        raise ValueError('Birthday fixture requires the complete original RNG')
    check('complete original RNG function',RNG_START,rng_code)
    globals_before = {at:read(at,4) for at in (RNG,TEMP,PRIVATE,ORDERS)}
    allocation = call(0x8009BFC0,[0x1400])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x1400:
        raise ValueError('Birthday fixture allocation failed')
    player,data,manager,orders,cursor = (allocation+o for o in (0x10,0xB30,0xF60,0x1190,0x1290))
    edges = (allocation,player+0xB00,data-16,data+0x410,manager-16,manager+0x200,
             orders-16,orders+216,cursor-16,cursor+16,allocation+0x13F0)
    for at in set(edges): write(at,EDGE)
    write(PRIVATE,struct.pack('>I',player));write(ORDERS,struct.pack('>I',orders))
    write(WINDOW+12,struct.pack('>I',data))
    cases = [(month,day) for month,last in enumerate(ENDS,1) for day in (last+1,last)]
    insertions,loads = 0,0
    names = ('088B','088A','088C','2586')
    for case,(month,day) in enumerate(cases):
        # Cover every value in both random pools. Finish with both complete
        # Sagittarius fields for the all-message insertion batch.
        seed = SEEDS[8 if case == len(cases)-1 else case%12]
        first,bits,animal = random_draw(seed)
        final,last_bits,sign = random_draw(first)
        write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4))
        for expected_seed,expected_bits in ((first,bits),(final,last_bits)):
            call(RNG_START,code=(RNG_START,rng_code))
            check('independent original random draw state',RNG,struct.pack('>I',expected_seed))
            check('independent original random float bits',TEMP,struct.pack('>I',expected_bits))
        write(RNG,struct.pack('>I',seed));write(TEMP,bytes(4))
        source_player = bytearray(b'P'*0xB00)
        source_player[0xA92:0xA94] = bytes((month,day))
        write(player,source_player)
        number = names[case%len(names)]
        entry = bytes.fromhex(request['birthday_messages'][number])
        call(0x8009E558,[data,int(number,16),0],1)
        check('complete birthday question loaded from cartridge',data,
              struct.pack('>4I',1,int(number,16),len(entry),0)+entry)
        loads += 1
        requests = [t for t in tokenize(entry,request['info']) if t.kind == 'cmd' and t.data == REQUEST]
        if len(requests) != 1: raise ValueError('Birthday fixture requires one exact request')
        write(orders,b'X'*216);write(cursor,struct.pack('>I',requests[0].offset))
        call(0x800A21C0,[WINDOW,cursor],0)
        check('birthday request changes only row nine slot nine',orders,b'X'*214+b'\0\4')
        check('birthday request advances five bytes',cursor,struct.pack('>I',requests[0].offset+5))
        state = bytearray(0x200);struct.pack_into('>HH',state,0x1AC,9,4)
        write(manager,state)
        before_window = read(WINDOW,0x330)
        call(base+0x809215E4-SPEC.ram,[manager],code=proof)
        fields = expected_fields(month,day,animal,sign)
        check('complete manager retained',manager,state)
        check('complete player and saved birthday retained',player,source_player)
        check('exactly two original random draws',RNG,struct.pack('>I',final))
        check('same final original random float bits',TEMP,struct.pack('>I',last_bits))
        expected_window = bytearray(before_window)
        expected_window[0x100:0x132] = b''.join(v[:10].ljust(10,b' ') for v in fields)
        check('only fifty native compatibility bytes change',WINDOW,expected_window)
        # All five actual native insertion handlers read the complete extended
        # rows. Checking only the native mirrors would miss Sagittarius's s.
        for slot,value in enumerate(fields):
            payload = b'X'+bytes((0x7F,0x31+slot))+b'Y'
            write(data,struct.pack('>4I',1,0,len(payload),0)+payload)
            write(cursor,struct.pack('>I',1));write(WINDOW+0x28C,bytes(4))
            call(0x800A21C0,[WINDOW,cursor],0)
            check('complete birthday value through native item insertion',data,
                  struct.pack('>4I',1,0,len(value)+2,0)+b'X'+value+b'Y')
            check('birthday field insertion retains cursor',cursor,struct.pack('>I',1))
            insertions += 1
        record({'birthday_preparation':[month,day],'animal_index':animal,'random_sign_index':sign,
                'fields':[v.decode() for v in fields],'passed':True})
    if fields[1:3] != [b'Sagittarius']*2:
        raise ValueError('Birthday full-message batch must exercise both long Western names')
    for number,hexadecimal in request['birthday_messages'].items():
        entry = bytes.fromhex(hexadecimal)
        call(0x8009E558,[data,int(number,16),0],1)
        check('complete birthday-related message from cartridge',data,
              struct.pack('>4I',1,int(number,16),len(entry),0)+entry)
        expected = entry
        for token in reversed(prepared_tokens(entry,request['info'])):
            value = fields[token.data[1]-0x31]
            write(cursor,struct.pack('>I',token.offset));write(WINDOW+0x28C,bytes(4))
            call(0x800A21C0,[WINDOW,cursor],0)
            expected = expected[:token.offset]+value+expected[token.offset+2:]
            check('complete scoped birthday field in full dialogue',data,
                  struct.pack('>4I',1,int(number,16),len(expected),0)+expected)
            insertions += 1
        record({'birthday_message':number,'insertions':len(prepared_tokens(entry,request['info'])),
                'expanded_bytes':len(expected),'passed':True})
        loads += 1
    write(PRIVATE,bytes(4))
    before_window,before_rng = read(WINDOW,0x330),{at:read(at,4) for at in (RNG,TEMP)}
    call(base+0x809215E4-SPEC.ram,[manager],code=proof)
    check('missing player retains every window byte',WINDOW,before_window)
    for at,value in before_rng.items(): check('missing player consumes no RNG',at,value)
    for at,value in globals_before.items():
        write(at,value);check('original player/order pointers and RNG restored',at,value)
    for at in set(edges): check('birthday owned allocation guards',at,EDGE)
    check('birthday calls retain complete ordinary overlay code',base,proof[1])
    call(0x8009C040,[allocation])
    return {'birthday_preparations':len(cases),'original_rng_calls':len(cases)*2,
            'birthday_message_loads':loads,'birthday_field_insertions':insertions,
            'complete_messages':len(request['birthday_messages']),'missing_player_cases':1,
            'allocation_freed':True,'requires_checkpoint_restore':True}
