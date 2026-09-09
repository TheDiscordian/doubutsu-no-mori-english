"""Run actual NPC show handlers on guarded fixtures, not normal actor gameplay."""

import struct
import time
from dataclasses import replace

from aflib import sha256
from mail_reader_smoke import all_pages
from mail_view_smoke import pointer, snapshot
from npc_mail_show import OVERLAYS, relocated, relocate_verified_data
from dialogue_dates import relocated as dates_relocated
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug,keyboard,request,record):
    from emulator_smoke import require_program_counter
    read = debug.read_memory
    def write(address,data):
        debug.write_memory(address,data)
        record({'npc_show_test_write':f'{address:08X}','bytes':len(data),'sha256':sha256(data)})
    def check(label,address,expected):
        actual = read(address,len(expected))
        if actual != expected:
            record({'npc_show_check':label,'assertion':'failed','address':f'{address:08X}',
                    'expected':expected.hex(),'observed':actual.hex()})
            raise ValueError('NPC letter-show mismatch: '+label)
        record({'npc_show_check':label,'assertion':'passed','bytes':len(expected),'sha256':sha256(actual)})
    def call(address,args,proof=None):
        result = debug.call(f'{address:08X}',args,verified_code=proof)
        record(result)
        return result['return_value']
    def closed():
        state = snapshot(debug)
        record({'npc_show_submenu':state})
        if (state['program'],state['move_index']) != (0,0):
            raise ValueError('NPC show test requires a closed submenu')
        return int(state['submenu'],16)
    for address,data in request['guards'].items():
        check('original resident instructions',int(address,16),bytes.fromhex(data))
    private = pointer(debug,0x80136FD8,0xBD0)
    saved_private = read(private,0xBD0)
    # These regions are read-only inputs. Synthetic memory lives in our own heap
    # allocation and must never be substituted into an actual NPC's saved state.
    preference = private+0x3EE
    preferences = read(preference,28)
    completed = 0
    branches = tuple(request.get('branches',('first_job','known_sender','unknown_sender')))
    if not branches or len(branches)!=len(set(branches)) or any(b not in ('first_job','known_sender','unknown_sender') for b in branches):
        raise ValueError('Invalid NPC show branch selection')
    for branch in branches:
        record(debug.pause_game_thread())
        submenu = closed()
        key = 'first_job' if branch == 'first_job' else 'ordinary'
        spec = OVERLAYS[key]
        code_bytes = spec.sections[0]
        data = bytes.fromhex(request['overlays'][key]['data'])
        reloc = bytes.fromhex(request['overlays'][key]['relocation'])
        secret = request.get('secret_overlay') if key == 'ordinary' else None
        if secret:
            from secret_actor import NEW_VROM,NEW_RELOCATION
            if (sha256(data)!=secret['overlay_sha256'] or sha256(reloc)!=secret['relocation_sha256']
                    or len(data)!=secret['bytes'] or len(reloc)!=secret['relocation_bytes']):
                raise ValueError('Changed approved secret show overlay')
            spec = replace(spec,vrom=NEW_VROM,relocation=NEW_RELOCATION,file_bytes=len(data),
                           sections=struct.unpack_from('>5I',reloc))
        # Place relocation scratch after BSS, then guarded manager/client/memory
        # fixtures. Each region is 16-byte aligned and remains allocated until
        # every window referencing the overlay's static Mail_c has closed.
        fixture_offset = 16+spec.resident_bytes+len(reloc)+16
        size = fixture_offset+0x1B0+0x180+0x20+0xC0+0x10+0xB0*2+16
        allocation = call(0x8009BFC0,[size])
        if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
            raise ValueError('NPC show heap allocation failed')
        base = allocation+16
        manager = allocation+fixture_offset
        client,animal,memory = manager+0x1B0,manager+0x330,manager+0x350
        pointers,source,expected = memory+0xC0,memory+0xD0,memory+0x180
        write(allocation,EDGE)
        write(manager-16,EDGE)
        write(allocation+size-16,EDGE)
        call(0x800262D0,[spec.vrom,spec.vrom+spec.file_bytes,spec.ram,
             spec.ram+spec.resident_bytes,base,base+spec.resident_bytes,len(reloc)],
             proof=(0x800262D0,bytes.fromhex(request['loader'])))
        overlay = (relocate_verified_data(spec,data,reloc,base) if secret else
                   dates_relocated(data,reloc,request['date_module'],base)
                   if key == 'ordinary' and request.get('date_module') else relocated(spec,data,reloc,base))
        check('complete native relocation and zeroed BSS',base,overlay)
        # The enlarged file materializes writable data/BSS before new code.
        # Only the unchanged native text prefix is a handler code proof.
        proof = (base,overlay[:code_bytes])
        letter = base+spec.letter-spec.ram
        for index,case in enumerate(request['cases']):
            record(debug.pause_game_thread())
            closed()
            population = read(0x80130DB8,0x528*15)
            player_before = read(private,0xBD0)
            write(manager,bytes(size-fixture_offset-16))
            write(manager+0x174,struct.pack('>3I',submenu,pointers,pointers+4))
            write(manager+0x1A0,struct.pack('>I',0x07DD))
            write(pointers,struct.pack('>2I',client,memory))
            write(client+0x174,struct.pack('>I',animal))
            write(animal,bytes.fromhex(request['identity']))
            write(memory,saved_private[:16])
            mail = bytes.fromhex(case['mail'])
            write(source,mail)
            compact = memory+0x2A
            call(0x800A82C8,[compact,source])
            expected_compact = mail[38:39]+mail[41:42]+mail[36:38]+mail[39:40]+mail[42:]+bytes(5)
            check('complete compact fixture',compact,expected_compact)
            source_memory = read(memory,0xC0)
            call(0x8009C384,[expected])
            call(0x800A8344,[expected,compact,0 if branch == 'unknown_sender' else memory,animal])
            expected_letter = bytearray(read(expected,164))
            if branch != 'first_job': expected_letter[0x28] = 0
            if branch == 'unknown_sender': expected_letter[0x12:0x18] = b' '*6
            if spec.globals:
                write(base+spec.globals-spec.ram,struct.pack('>2I',0 if branch == 'unknown_sender' else memory,compact))
            write(TEST_STACK-0x800,EDGE)
            write(TEST_STACK+0x30,EDGE)
            call(base+spec.handler-spec.ram,[manager],proof=proof)
            check('complete caller temporary letter',letter,expected_letter)
            check('manager continuation state',manager+0x185,bytes((4,10 if branch == 'first_job' else 3)))
            check('compact source and sender memory retained',memory,source_memory)
            check('original full-letter fixture retained',source,mail)
            check('caller retains saved NPC population',0x80130DB8,population)
            check('caller retains saved player state',private,player_before)
            check('lower call-stack guard',TEST_STACK-0x800,EDGE)
            check('upper call-stack guard',TEST_STACK+0x30,EDGE)
            debug.send('c')
            time.sleep(8)
            state = snapshot(debug)
            record({'npc_show_open':branch,'case':case['label'],'submenu':state})
            for field,value in {'program':12,'move_index':3,'board_state':2,'board_mode':1,'source':f'{letter:08X}'}.items():
                if state.get(field) != value:
                    raise ValueError(f'NPC show {field}: {state.get(field)!r}, expected {value!r}')
            if case['snapshot']:
                all_pages(debug,keyboard,{'reader':request['reader'],'hook':request['hooks']['af_mail_header_hook'],
                    'status':1,**{k:case[k] for k in ('header','body','footer')}},record)
            else:
                if (state['body_length'],state['footer_length']) != (len(bytes.fromhex(case['body'])),len(bytes.fromhex(case['footer']))):
                    raise ValueError('Ordinary NPC show changed text lengths')
                record(debug.pause_game_thread())
                for name,address in request['hooks'].items():
                    breakpoint = f'0,{int(address,16):x},4'
                    if debug.command('Z'+breakpoint) != 'OK':
                        raise ValueError('NPC show ordinary hook breakpoint rejected')
                    try:
                        if debug.command('c') != 'S05': raise ValueError('NPC show ordinary hook did not stop')
                        require_program_counter(debug.command('g'),address)
                        record({'npc_show_ordinary_hook':name,'pc':address})
                    finally:
                        debug.command('z'+breakpoint)
                debug.send('c')
            keyboard.press(('b','a','Return')[index%3],0.12)
            time.sleep(5)
            record(debug.pause_game_thread())
            closed()
            check('temporary source retained after window close',letter,expected_letter)
            check('compact source retained after window close',memory,source_memory)
            check('saved header/footer preferences retained',preference,preferences)
            for address in (allocation,manager-16,allocation+size-16): check('heap fixture guard',address,EDGE)
            check('resident module guard',GUARD_ADDRESS,GUARD_WORD.to_bytes(4,'big')*4)
            record({'npc_show_case_passed':branch,'case':case['label'],'snapshot':case['snapshot']})
            completed += 1
        call(0x8009C040,[allocation])
        record({'npc_show_allocation_freed':f'{allocation:08X}','only_after_window_close':True})
    return {'npc_show_cases':completed,'native_callers':len(branches),'normal_actor_gameplay':False,
            'game_save_validation':False,'requires_checkpoint_restore':True}
