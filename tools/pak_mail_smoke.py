"""Isolated native Controller Pak transport tests, without travel-flow claims."""

import json
import struct

from aflib import sha256
from flash_mail import FLASH_BYTES, SAVE_RAM, SAVE_BYTES, checksum
from pak_mail import (PAK_BYTES, PASSPORT_BYTES, LETTER_FILE_BYTES, PRIVATE_BYTES,
                      ANIMAL_BYTES, PAK_INFO, PASSPORT, PROBE_CODE, passport_slots,
                      letter_slots, fixture_records)
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record,*,export_directory=None):
    writing = export_directory is not None
    if (request['passport_slots'] != passport_slots() or request['letter_slots'] != letter_slots()
            or len(request['cases']) != 2):
        raise ValueError('Pak fixture requires both exact native storage inventories')
    for case in request['cases']:
        if len(bytes.fromhex(case['wire'])) != 122 or len(bytes.fromhex(case['output'])) != 1040:
            raise ValueError('Malformed Pak snapshot fixture')
    read = debug.read_memory
    def write(address,data):
        debug.write_memory(address,data)
        record({'pak_test_ram_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        observed = read(address,len(expected))
        if observed != expected:
            record({'pak_mail_check':label,'assertion':'failed','address':f'{address:08X}',
                    'expected_sha256':sha256(expected),'observed_sha256':sha256(observed)})
            raise ValueError('Controller Pak mismatch: '+label)
        record({'pak_mail_check':label,'assertion':'passed','bytes':len(expected),'sha256':sha256(observed)})
    def call(address,args=(),expected=None,proof=None):
        result = debug.call(f'{address:08X}',args,verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            record({'pak_native_error':read(PAK_INFO+0x70,4).hex()})
            raise ValueError(f'Native Pak call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    for address,data in request['guards'].items():
        check('original Pak instructions/table',int(address,16),bytes.fromhex(data))
    original_save = read(SAVE_RAM,SAVE_BYTES)
    call(0x8007A070,expected=PAK_INFO)
    call(0x800790C0,[0],1)
    def usage(expected):
        queue = call(0x800D6A10)
        call(0x80078F08,[PAK_INFO],1)
        call(0x80078FE8,[PAK_INFO],1)
        call(0x800D6A44,[queue])
        free,maximum,used = struct.unpack('>3I',read(PAK_INFO+0x2D4,12))
        if maximum != 16 or used != expected or free > PAK_BYTES:
            raise ValueError(f'Unexpected isolated Pak usage: free={free}, maximum={maximum}, used={used}')
        record({'native_pak_usage':{'free_bytes':free,'maximum_files':maximum,'used_files':used}})
        return free
    initial_free = usage(0 if writing else 2)
    if writing and initial_free < PASSPORT_BYTES+LETTER_FILE_BYTES:
        raise ValueError('Fresh isolated Controller Pak cannot hold both test files')
    # Reuse one chip buffer. Decoder work follows the largest note inside it;
    # raw chip reads run only while neither the note nor decoder is in use.
    allocation_bytes = 0x8200
    allocation = call(0x8009BFC0,[allocation_bytes])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-allocation_bytes:
        raise ValueError('Controller Pak fixture allocation failed')
    probe,buffer = allocation+16,allocation+0x100
    work,output = buffer+LETTER_FILE_BYTES+16,buffer+LETTER_FILE_BYTES+0xE10
    if probe+len(PROBE_CODE)+16 > buffer or work+3552+16 > output or output+1040+16 > buffer+PAK_BYTES:
        raise ValueError('Controller Pak fixture buffer overlap')
    write(probe,PROBE_CODE)
    for address in (allocation,probe+len(PROBE_CODE),buffer+PAK_BYTES): write(address,EDGE)
    write(TEST_STACK-0xA00,EDGE)
    write(TEST_STACK+0x30,EDGE)
    def chip_read():
        call(probe,[buffer],0,proof=(probe,PROBE_CODE))
        check('raw Pak buffer guard',buffer+PAK_BYTES,EDGE)
        return read(buffer,PAK_BYTES)
    initial = chip_read()
    exported = request.get('export')
    if not writing and (sha256(initial) != exported['pak_sha256']
                        or request['cases'] != exported['cases']
                        or request['rom_sha256'] != exported['rom_sha256']):
        raise ValueError('Fresh-start Controller Pak differs from the native export')
    notes = []
    if writing:
        private = int.from_bytes(read(0x80136FD8,4),'big')
        if private not in [SAVE_RAM+0x20+i*PRIVATE_BYTES for i in range(4)]:
            raise ValueError('Pak writer needs a valid local test-town player')
        call(0x800B7F78,[private],1)
        call(0x800951C0,expected=0)
        passport = bytearray(read(PASSPORT,PASSPORT_BYTES))
        passport[8:0xBD8] = read(private,PRIVATE_BYTES)
        passport[0xBD8:0x1100] = read(0x80130DB8,ANIMAL_BYTES)
        fixture,records = fixture_records(passport,passport_slots(),request['cases'])
        write(buffer,fixture)
        call(0x800793B8,[buffer+8,buffer+0xBD8,PAK_INFO],1)
        saved = read(PASSPORT,PASSPORT_BYTES)
        if saved[2:] != fixture[2:] or checksum(saved):
            raise ValueError('Native passport preparation changed data or produced a bad checksum')
        notes.append({'kind':0,'data':saved.hex(),'records':records})
        write(buffer,bytes(LETTER_FILE_BYTES))
        write(buffer+2,b' '*80)
        for slot in letter_slots(): call(0x8009C384,[buffer+slot['offset']])
        fixture,records = fixture_records(read(buffer,LETTER_FILE_BYTES),letter_slots(),request['cases'])
        write(buffer,fixture)
        # Stage zero writes the note. Stage one invokes FlashRAM saving and is
        # deliberately outside this Pak-only fixture.
        write(output,b'\x00')
        call(0x80079D50,[buffer,PAK_INFO,output],0)
        check('native letter writer advances to second stage',output,b'\x01')
        saved = read(buffer,LETTER_FILE_BYTES)
        if saved[2:] != fixture[2:] or checksum(saved):
            raise ValueError('Native letter-file preparation changed data or produced a bad checksum')
        notes.append({'kind':1,'data':saved.hex(),'records':records})
        remaining = usage(2)
        if initial_free-remaining != PASSPORT_BYTES+LETTER_FILE_BYTES:
            raise ValueError('Native Pak allocation differs from the two exact note sizes')
    else:
        notes = exported['notes']
    if [note['kind'] for note in notes] != [0,1]:
        raise ValueError('Pak export needs exactly the passport and letter-storage file')
    decoded = 0
    for note in notes:
        kind = note['kind']
        size,slots = (PASSPORT_BYTES,passport_slots()) if kind == 0 else (LETTER_FILE_BYTES,letter_slots())
        expected = bytes.fromhex(note['data'])
        if len(expected) != size or checksum(expected) or len(note['records']) != len(slots):
            raise ValueError('Malformed complete Pak note')
        write(buffer,b'!'*size)
        if kind == 0:
            call(0x80079F44,expected=1)
            check('native checksum-gated passport load',PASSPORT,expected)
            call(0x8007942C,[buffer+8,buffer+0xBD8,PAK_INFO],1)
            check('native complete player import',buffer+8,expected[8:0xBD8])
            check('native complete NPC import',buffer+0xBD8,expected[0xBD8:0x1100])
            source = PASSPORT
        else:
            call(0x80079EA4,[buffer,PAK_INFO],1)
            check('native complete stored-letter file',buffer,expected)
            source = buffer
        call(0x8008EE7C,[source,size],0)
        for address in (buffer+size,work+3552,output+1040): write(address,EDGE)
        seen = set()
        for slot,value in zip(slots,note['records']):
            if value['label'] != slot['label'] or value['case'] not in (0,1):
                raise ValueError('Pak record identity mismatch')
            complete = bytes.fromhex(value['data'])
            if len(complete) != slot['bytes']:
                raise ValueError('Pak record size mismatch')
            check(f'persisted file {kind} '+slot['label'],source+slot['offset'],complete)
            key = slot['compact'],value['case']
            if key not in seen:
                case = request['cases'][value['case']]
                wire_at = source+slot['offset']+(5 if slot['compact'] else 42)
                write(output,b'!'*1040)
                call(int(request['restore'],16),[output,wire_at,122,work],1)
                check('complete Pak English reconstruction',output,bytes.fromhex(case['output']))
                seen.add(key)
                decoded += 1
        if len(seen) != (4 if kind == 0 else 2):
            raise ValueError('Missing Pak layout/format decoder coverage')
        for address in (buffer+size,work+3552,output+1040): check('note/decoder guard',address,EDGE)
    saved = chip_read()
    if not writing and saved != initial:
        raise ValueError('Read-only native Pak checks changed the chip')
    if writing:
        export_directory.mkdir()
        (export_directory/'test.pak').write_bytes(saved)
        # Blank cartridge control file: no saved town or state transfers here.
        (export_directory/'test.flash').write_bytes(b'\xFF'*FLASH_BYTES)
        manifest = {'rom_sha256':request['rom_sha256'],'pak_sha256':sha256(saved),
                    'cases':request['cases'],'notes':notes,'passport_slots':passport_slots(),
                    'letter_slots':letter_slots(),'source':'native note writes and raw native PIF readback',
                    'normal_travel':False,'hardware_validation':False}
        (export_directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    check('unchanged live save payload',SAVE_RAM,original_save)
    for address in (allocation,probe+len(PROBE_CODE),buffer+PAK_BYTES): check('heap guard',address,EDGE)
    check('raw-reader instructions retained',probe,PROBE_CODE)
    check('lower stack guard',TEST_STACK-0xA00,EDGE)
    check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,GUARD_WORD.to_bytes(4,'big')*4)
    call(0x8009C040,[allocation])
    return {'native_pak_mail_mode':'save' if writing else 'read','mail_slots':177,
            'decoded_layout_format_pairs':decoded,'pak_sha256':sha256(saved),
            'normal_travel':False,'requires_checkpoint_restore':True}
