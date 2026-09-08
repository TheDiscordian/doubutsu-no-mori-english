"""Silent isolated native loading, random selection, and fortune insertion."""

import struct

from aflib import sha256
from birthday_smoke import RNG, TEMP, RNG_START, RNG_END, RNG_SHA256
from flash_mail import SAVE_RAM, SAVE_BYTES
from fortune_strings import (VROM, RAM, RELOC_VROM, FIRST, END, BASES, CHANGES,
                             SOURCE_SHA256, RELOC_SHA256, patch)
from npc_mail_show import ShowOverlay, relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from textcodec import tokenize

SPEC = ShowOverlay(VROM, RAM, RELOC_VROM, 1760, (1568,192,0,0,40),
                   SOURCE_SHA256, RELOC_SHA256, 0, 0, 0)
WINDOW, EDGE = 0x80142410, b'EDGE'*4


def seed_for(index):
    if type(index) is not int or not 0 <= index < 32:
        raise ValueError('Fortune fixture index must be within its native pool')
    # Invert the native LCG so the next native single-precision fraction is
    # exactly index/32. The real preparer still executes its own unchanged RNG.
    final = index << 27
    seed = ((final-0x3C6EF35F)*pow(0x19660D, -1, 1 << 32)) & 0xFFFFFFFF
    return seed, final, (final >> 9) | 0x3F800000


def relocated(original, reloc, base):
    patch(original, reloc)
    output = bytearray(relocate_verified_data(SPEC, original, reloc, base))
    for address, before, after in CHANGES:
        if struct.unpack_from('>I', output, address-RAM)[0] != before:
            raise ValueError('Fortune frame word unexpectedly relocated')
        struct.pack_into('>I', output, address-RAM, after)
    return bytes(output)


def exercise(debug, request, record):
    read = debug.read_memory
    assertions = 0
    def write(at, value):
        debug.write_memory(at, value)
        record({'fortune_write': f'{at:08X}', 'bytes': len(value), 'sha256': sha256(value)})
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'fortune_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Fortune native mismatch: '+label)
        assertions += 1
    def call(at, args=(), expected=None, proof=None):
        result = debug.call(f'{at:08X}', args, verified_code=proof); record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Fortune native return differs')
        return result['return_value']

    original, reloc = bytes.fromhex(request['source']), bytes.fromhex(request['relocation'])
    patch(original, reloc)
    rng = bytes.fromhex(request['rng'])
    if len(rng) != RNG_END-RNG_START or sha256(rng) != RNG_SHA256:
        raise ValueError('Fortune test requires the complete native RNG')
    check('unchanged complete native RNG', RNG_START, rng)
    saved = read(SAVE_RAM, SAVE_BYTES)
    before_rng, before_temp = read(RNG,4), read(TEMP,4)
    size = 0x1800
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Fortune fixture allocation failed')
    base, data, cursor, staging, address_out = (allocation+o for o in (0x10,0x900,0xD40,0xD80,0xDC0))
    edges = (allocation, allocation+size-16, data-16, data+0x410,
             staging-16, staging+32, cursor-16, cursor+16, TEST_STACK-0x800, TEST_STACK+0x30)
    for at in edges: write(at, EDGE)
    call(0x800262D0, [VROM,VROM+SPEC.file_bytes,RAM,RAM+SPEC.resident_bytes,
                     base,base+SPEC.resident_bytes,len(reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    loaded = relocated(original, reloc, base)
    check('complete cartridge-loaded relocated overlay', base, loaded)
    proof = (base,loaded[:SPEC.sections[0]])
    entries = [bytes.fromhex(raw) for raw in request['strings']]
    offset = [0]
    for raw in entries: offset.append(offset[-1]+len(raw))
    for index in (-1,0,FIRST-1,FIRST,END-1,END,1561,1562):
        write(address_out,b'G'*16)
        call(0x800C3E30,[index & 0xFFFFFFFF,address_out,address_out+4])
        expected = (struct.pack('>2I',0x02600000+offset[index],len(entries[index]))
                    if 0 <= index < len(entries) and len(entries[index]) <= 64 else bytes(8))
        check('relocated string-table boundary',address_out,expected+b'G'*8)
    for index in range(FIRST,END):
        write(staging,b'G'*32)
        call(0x800C3F70,[staging,16,index])
        check('complete fortune fragment and loader guard',staging,entries[index].ljust(16,b' ')+b'G'*16)

    write(WINDOW+12,struct.pack('>I',data))
    entry = bytes.fromhex(request['message'])
    fields = 0
    for index in range(32):
        seed, final, bits = seed_for(index)
        write(RNG,struct.pack('>I',seed)); write(TEMP,bytes(4))
        call(RNG_START,proof=(RNG_START,rng))
        check('independent original RNG state',RNG,struct.pack('>I',final))
        check('independent original RNG float',TEMP,struct.pack('>I',bits))
        values = [entries[start+index] for start in BASES]
        for slot,value in enumerate(values):
            before = read(WINDOW,0x330)
            write(RNG,struct.pack('>I',seed)); write(TEMP,bytes(4))
            call(base+0x809DC590-RAM,[slot],proof=proof)
            check('preparer consumes exactly one original draw',RNG,struct.pack('>I',final))
            check('preparer retains native random fraction',TEMP,struct.pack('>I',bits))
            expected = bytearray(before)
            expected[0x100+slot*10:0x10A+slot*10] = value.ljust(16,b' ')[:10]
            check('native window changes only the selected compatibility field',WINDOW,expected)
            # The expanded local ends four bytes before the caller argument
            # slot, and its value must survive until the native setter returns.
            check('complete expanded native stack local',TEST_STACK-56+0x24,value.ljust(16,b' '))
        call(0x8009E558,[data,0x973,0],1)
        check('complete fortune message from cartridge',data,struct.pack('>4I',1,0x973,len(entry),0)+entry)
        expected = entry
        for slot in (3,0,1,2):
            tokens = [t for t in tokenize(expected,request['info'])
                      if t.kind == 'cmd' and t.data[1] == 0x31+slot]
            if len(tokens) != 1: raise ValueError('Fortune message must use each prepared field once')
            token = tokens[0]
            write(cursor,struct.pack('>I',token.offset)); write(WINDOW+0x28C,bytes(4))
            call(0x800A21C0,[WINDOW,cursor],0)
            expected = expected[:token.offset]+values[slot]+expected[token.offset+2:]
            check('full fortune insertion with all surrounding text retained',data,
                  struct.pack('>4I',1,0x973,len(expected),0)+expected)
            fields += 1
        record({'fortune_pool_index':index,'selected_ids':[f'{start+index:04X}' for start in BASES],
                'complete_reading_insertions':True})
    write(RNG,before_rng); write(TEMP,before_temp)
    check('complete saved game retained',SAVE_RAM,saved)
    check('complete overlay retained',base,loaded)
    for at in edges: check('heap and native stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'fortune_complete_phrases':128,'fortune_native_preparations':128,
            'fortune_independent_rng_calls':32,'fortune_complete_readings':32,
            'fortune_insertions':fields,'fortune_assertions':assertions,
            'allocation_freed':f'{allocation:08X}','normal_gameplay':False,'requires_checkpoint_restore':True}
