"""Native FlashRAM I/O in isolated fixtures; never a normal save-menu claim."""

import json
import struct

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES, BANK_BYTES, FLASH_BYTES, SAVE_STATE, SAVE_DISPATCH, locations, validate_flash
from runtime_layout import MODULE_RAM, RESERVATION, TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,request,record,*,export_directory=None):
    writing = export_directory is not None
    if request['locations'] != locations() or len(request['cases']) != 2:
        raise ValueError('Flash mail tests require the exact pinned storage layout and both formats')
    for case in request['cases']:
        if len(bytes.fromhex(case['wire'])) != 122 or len(bytes.fromhex(case['output'])) != 1040:
            raise ValueError('Malformed FlashRAM snapshot fixture')
    read = debug.read_memory
    def write(address,data):
        debug.write_memory(address,data)
        record({'flash_test_ram_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        observed = read(address,len(expected))
        if observed != expected:
            record({'flash_mail_check':label,'assertion':'failed','address':f'{address:08X}',
                    'expected_sha256':sha256(expected),'observed_sha256':sha256(observed)})
            raise ValueError('FlashRAM mail mismatch: '+label)
        record({'flash_mail_check':label,'assertion':'passed','bytes':len(expected),'sha256':sha256(observed)})
    def call(address,args=(),expected=None):
        result = debug.call(f'{address:08X}',args)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native FlashRAM call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    for address,data in request['guards'].items():
        check('original FlashRAM instructions/table',int(address,16),bytes.fromhex(data))
    call(0x800CDBE0,expected=1)
    # Stream chip reads through a small buffer while the native saver owns its
    # separate save buffer. Fresh-start validation needs only one bank at a time.
    transfer_bytes = 0x4000 if writing else BANK_BYTES
    allocation_bytes = transfer_bytes+0x1240
    allocation = call(0x8009BFC0,[allocation_bytes])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-allocation_bytes:
        raise ValueError('FlashRAM fixture allocation failed')
    flash,work,output = allocation+16,allocation+transfer_bytes+32,allocation+transfer_bytes+0xE20
    if work+3552+16 > output or output+1040+16 > allocation+allocation_bytes:
        raise ValueError('FlashRAM decoder fixture overlap')
    for address in (allocation,flash+transfer_bytes,work+3552,output+1040): write(address,EDGE)
    write(TEST_STACK-0xA00,EDGE)
    write(TEST_STACK+0x30,EDGE)
    def read_chip():
        chunks = []
        for start in range(0,FLASH_BYTES,transfer_bytes):
            call(0x800CDE54,[flash,start//128,transfer_bytes//128],0)
            chunks.append(read(flash,transfer_bytes))
            check('native chip-read buffer guard',flash+transfer_bytes,EDGE)
        return b''.join(chunks)
    initial = read_chip()
    preserved = None
    if writing:
        if initial != b'\xFF'*FLASH_BYTES:
            raise ValueError('Native FlashRAM write fixture requires a completely blank isolated chip')
        if read(SAVE_STATE,32) != bytes(32):
            raise ValueError('Native save pipeline is not idle')
        original = read(SAVE_RAM,SAVE_BYTES)
        modified = bytearray(original)
        preserved = []
        for index,slot in enumerate(request['locations']):
            offset,size = slot['offset'],slot['bytes']
            wire = bytes.fromhex(request['cases'][index%2]['wire'])
            value = bytearray(modified[offset:offset+size])
            if slot['compact']:
                value[0],value[4] = 1,128
                value[5:127] = wire
            else:
                value[38:42] = bytes((1,128,4,0))
                value[42:] = wire
            modified[offset:offset+size] = value
            preserved.append({'label':slot['label'],'data':value.hex(),'case':index%2})
        write(SAVE_RAM,modified)
        expected_payload = None
        for step in range(160):
            before = int.from_bytes(read(SAVE_STATE,4),'big')
            if before > 6: raise ValueError('Native save pipeline selected an invalid state')
            result = call(SAVE_DISPATCH)
            control = struct.unpack('>8I',read(SAVE_STATE,32))
            record({'native_flash_save_step':step,'state_before':before,'state_after':control[0],
                    'page':control[1],'result':result,
                    'native_buffer_request':read(0x80146080,8).hex()})
            if before == 1 and control[0] == 2:
                pointer = control[2]
                if pointer&15 or not MODULE_RAM+RESERVATION <= pointer <= 0x80400000-SAVE_BYTES:
                    raise ValueError('Native save copy has an invalid buffer')
                expected_payload = read(pointer,SAVE_BYTES)
                for slot,value in zip(request['locations'],preserved):
                    expected = bytes.fromhex(value['data'])
                    if expected_payload[slot['offset']:slot['offset']+slot['bytes']] != expected:
                        raise ValueError('Native save preparation changed mail: '+slot['label'])
                record({'native_flash_prepared_payload':sha256(expected_payload),'complete_mail_slots':len(preserved)})
            if result == 1:
                if control != (0,)*8 or expected_payload is None:
                    raise ValueError('Native save completed without its complete copy and cleanup')
                break
            if result != 0: raise ValueError('Native save pipeline failed')
            # Advance the real frame boundary while the native flash worker runs.
            # Do not consume its completion queue: the save state machine owns it.
            record(debug.advance_game_frame())
        else:
            raise ValueError('Native FlashRAM save exceeded its bounded frame count')
        saved = read_chip()
        report = validate_flash(saved)
        if any(saved[start:start+SAVE_BYTES] != expected_payload for start in (0,BANK_BYTES)):
            raise ValueError('FlashRAM payload differs from the native prepared save')
        # Export through the native read API before checkpoint restoration can
        # restore cartridge memory. Only this ignored test directory is written.
        export_directory.mkdir()
        (export_directory/'test.flash').write_bytes(saved)
        manifest = {**report,'rom_sha256':request['rom_sha256'],'locations':request['locations'],
                    'records':preserved,'cases':request['cases'],
                    'source':'native save state machine, two-bank write/verify, and complete chip readback',
                    'ordinary_save_menu_validation':False,'hardware_validation':False}
        (export_directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        write(SAVE_RAM,original)
        check('restored live save payload',SAVE_RAM,original)
        record({'native_flash_export':report,'complete_mail_slots':len(preserved),'normal_gameplay':False})
    else:
        exported = request['export']
        report = validate_flash(initial)
        if (report['flash_sha256'] != exported['flash_sha256'] or request['cases'] != exported['cases']
                or exported['rom_sha256'] != request['rom_sha256']):
            raise ValueError('Fresh-start native FlashRAM does not match the verified export')
        preserved = exported['records']
        if len(preserved) != len(request['locations']): raise ValueError('Incomplete exported slot inventory')
        # Execute the game's native bank reader and native checksum/identity
        # validators after the fresh emulator has initialised its cartridge.
        for page,start in ((0,0),(512,BANK_BYTES)):
            call(0x8008F8A0,[flash,page],1)
            check('complete native bank payload',flash,initial[start:start+SAVE_BYTES])
            call(0x8008EE7C,[flash,SAVE_BYTES],0)
            town = int.from_bytes(initial[start+0x2F68:start+0x2F6A],'big')
            call(0x8008EF0C,[flash,town],1)
            checked_formats = set()
            for slot,value in zip(request['locations'],preserved):
                if value['label'] != slot['label'] or value['case'] not in (0,1):
                    raise ValueError('Invalid exported slot identity')
                expected = bytes.fromhex(value['data'])
                if len(expected) != slot['bytes']: raise ValueError('Invalid exported record size')
                check(f'persisted bank {start//BANK_BYTES} complete '+slot['label'],flash+slot['offset'],expected)
                # Full equality covers every slot. Decode each distinct format
                # and full/compact source layout directly from each read bank.
                key = slot['compact'],value['case']
                if key not in checked_formats:
                    case = request['cases'][value['case']]
                    wire_at = flash+slot['offset']+(5 if slot['compact'] else 42)
                    write(output,b'!'*1040)
                    call(int(request['restore'],16),[output,wire_at,122,work],1)
                    check('complete cold-start English output',output,bytes.fromhex(case['output']))
                    checked_formats.add(key)
            if len(checked_formats) != 4: raise ValueError('Missing persisted layout/format decode coverage')
        record({'native_flash_fresh_start_read':report,'complete_mail_slots':len(preserved),
                'decoded_layout_format_pairs':len(checked_formats),'decoded_banks':2,'normal_gameplay':False})
    for address in (allocation,flash+transfer_bytes,work+3552,output+1040): check('heap buffer guard',address,EDGE)
    check('lower stack guard',TEST_STACK-0xA00,EDGE)
    check('upper stack guard',TEST_STACK+0x30,EDGE)
    check('module guard',GUARD_ADDRESS,GUARD_WORD.to_bytes(4,'big')*4)
    call(0x8009C040,[allocation])
    return {'native_flash_mail_mode':'save' if writing else 'read','mail_slots':len(preserved),
            'normal_save_menu':False,'requires_checkpoint_restore':True}
