"""Guarded, test-only title callback substitution for actual N64 model rendering."""
import struct

from aflib import by_vrom, sha256
from event_artwork_preview import CODE, META, ASSETS, DEPTH, EDGE, OBJECT, ROM_SHA, CODE_SHA, transforms
from runtime_layout import GUARD_ADDRESS, GUARD_WORD
from title_start_smoke import locate


def words(*values):
    return struct.pack('>'+'I'*len(values), *values)


def exercise(debug, request, rom, state):
    read, write = debug.read_memory, debug.write_memory
    if sha256(rom) != ROM_SHA or read(0x80000318, 4) != words(0x800000):
        raise ValueError('Event graphics fixture requires its exact eight-MiB cartridge')
    resident = words(*([GUARD_WORD]*4))
    if read(GUARD_ADDRESS, 16) != resident or read(0x800418D8, 4) != bytes(4):
        raise ValueError('Resident guard changed or a native thread faulted')
    _, actor, title_base, _ = locate(debug, memory_end=0x80800000)
    if title_base != 0x80400010:
        raise ValueError('Unexpected title allocation')
    title_guards = (0x80400000, 0x804475F0)
    for address in title_guards:
        if read(address, 16) != words(*([0xAF54C0DE]*4)):
            raise ValueError('Title boundary guard changed')
    if request.get('setup'):
        if state:
            raise ValueError('Preview already installed')
        code = bytes.fromhex(request['code'])
        if not 4 <= len(code) <= 0x2000 or len(code) % 4 or sha256(code) != CODE_SHA:
            raise ValueError('Invalid test callback extent')
        obj = by_vrom(rom)[OBJECT].extract(rom)
        if len(obj) != 0x9AD80:
            raise ValueError('Changed installed event object size')
        regions = ((CODE, len(code)), (META, 0xC0), (ASSETS, len(obj)), (DEPTH, 320*240*2))
        guards = tuple(at for start, size in regions for at in (start-16, start+size))
        for start, size in regions:
            for offset in range(-16, size+16, 4096):
                size_now = min(4096, size+16-offset)
                if read(start+offset, size_now) != bytes(size_now):
                    raise ValueError('Event preview scratch RAM is not unused')
        callback = read(actor+0x168, 4)
        if not title_base <= int.from_bytes(callback, 'big') < 0x804475F0:
            raise ValueError('Unexpected title drawing callback')
        for start, data in ((CODE, code), (ASSETS, obj)):
            for offset in range(0, len(data), 4096):
                write(start+offset, data[offset:offset+4096])
        for address in guards:
            write(address, EDGE)
        write(META, bytes(0xC0))
        write(actor+0x168, words(CODE))
        state.update(actor=actor, callback=callback, code=code, obj=obj, guards=guards)
        return {'event_preview_installed': True, 'actor': f'{actor:08X}',
                'code_sha256': sha256(code), 'object_sha256': sha256(obj),
                'checkpoint_restore_required': True, 'ordinary_scene': False}
    if not state or actor != state['actor']:
        raise ValueError('Missing matching event preview state')
    if 'select' in request:
        mode = request['select']
        write(META, words(mode, 0, 0))
        write(META+0x40, transforms(mode))
        return {'event_preview_selection': mode}
    if 'verify' in request:
        if read(actor+0x168, 4) != words(CODE):
            raise ValueError('Event preview callback changed')
        mode, draws, error = struct.unpack('>3I', read(META, 12))
        if mode != request['verify'] or draws < 2 or error:
            raise ValueError(f'Event preview draw state failed: {mode}/{draws}/{error}')
        for start, data in ((CODE, state['code']), (ASSETS, state['obj'])):
            for offset in range(0, len(data), 4096):
                part = data[offset:offset+4096]
                if read(start+offset, len(part)) != part:
                    raise ValueError('Event preview changed its code or installed model')
        for address in state['guards']:
            if read(address, 16) != EDGE:
                raise ValueError('Event preview exceeded its owned buffer')
        return {'event_preview_rendered': mode, 'draws': draws, 'error': error,
                'guards_intact': True, 'model_unchanged': True, 'native_fault': False,
                'visual_acceptance': False, 'ordinary_scene': False}
    if request.get('restored'):
        if read(actor+0x168, 4) != state['callback']:
            raise ValueError('Title callback was not restored')
        for address in state['guards']:
            if read(address, 16) != bytes(16):
                raise ValueError('Preview scratch RAM was not restored')
        return {'event_preview_checkpoint_restored': True, 'native_title_callback_restored': True}
    raise ValueError('Unknown event preview action')
