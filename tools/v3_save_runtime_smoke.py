"""Native FlashRAM write plus a fresh-process V3 load, using disposable saves."""
import importlib.util
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, yaz0_decode
from flash_mail import SAVE_RAM, SAVE_BYTES, SAVE_STATE, SAVE_DISPATCH, FLASH_BYTES
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_save_codec import BANK, BLOB_SIZE, PROFILE, STATE
from v3_save_runtime import STATE_RAM, STATE_BYTES
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record, *, export_directory=None, seed_directory=None, test_sync=True, collect_items=False):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('save_runtime'):
        raise ValueError('FlashRAM V3 check requires its exact current cartridge')
    writing = export_directory is not None
    if writing == (seed_directory is not None):
        raise ValueError('Choose either isolated writer or fresh exported-save reader')
    console = report.get('equipment_resources', {}).get('console_storage')
    if not console:
        spec = importlib.util.spec_from_file_location('v3_save_reference',
            Path(__file__).resolve().parents[1] / 'tests/test_v3_save_codec.py')
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
    files = by_vrom(rom)
    blob, code = files[BLOB].extract(rom)[:BLOB_SIZE], files[CODE_VROM].extract(rom)
    proofs = boot_proofs(rom) if collect_items or console else {}
    edge, calls = b'V3IO' * 4, 0
    state_bytes = report['save_runtime']['state_bytes']
    state_guard = STATE_RAM + state_bytes - 16
    profile_bytes = 192 if console else PROFILE
    expected_console = None

    def logical_bank(bank):
        if not console:
            return bank
        ext = bank[SAVE_BYTES:]
        if (len(bank) != BANK or ext[:16] != struct.pack('>4I', 0x41465333, 0x00050680, 3, 72064)
                or struct.unpack_from('>I', ext, 20)[0] != 1 or any(ext[36:])):
            raise ValueError('Native compressed save has invalid metadata')
        seal = bytearray(bank); seal[18:20] = bytes(2); seal[SAVE_BYTES+24:SAVE_BYTES+28] = bytes(4)
        if zlib.crc32(seal) != struct.unpack_from('>I', ext, 24)[0] or sum(struct.unpack('>31936H', bank[:SAVE_BYTES])) & 65535:
            raise ValueError('Native compressed save checksum mismatch')
        length = struct.unpack_from('>I', ext, 16)[0]
        stream = bank[20:0x2F68] + bank[0x2F6A:SAVE_BYTES]
        if not 0 < length <= len(stream) or any(stream[length:]):
            raise ValueError('Native compressed save exceeds capacity or has dirty padding')
        decoded = yaz0_decode(b'Yaz0' + struct.pack('>I', 72064) + bytes(8) + stream[:length])
        if (zlib.crc32(decoded[:BANK]), zlib.crc32(decoded[BANK:])) != struct.unpack_from('>2I', ext, 28):
            raise ValueError('Native decoded town/console checksum mismatch')
        if decoded[BANK:] != expected_console:
            raise ValueError('Native save loses independent console progress')
        return decoded[:BANK]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'v3_flash_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native V3 FlashRAM check failed: ' + label)

    def call(address, args=(), expected=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proofs.get(address))
        record(result)
        calls += 1
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError(f'Native V3 FlashRAM call {address:08X} returned unexpected value')
        return result['return_value']

    def validate(bank, state):
        if console:
            canonical = logical_bank(bank)
            ext = bytearray(0x680)
            struct.pack_into('>3I', ext, 0, 0x41465333, 0x00040680, 3)
            ext[0x18:0xB8]=state[:160]; ext[0xC0:0x2C0]=state[192:704]
            ext[0x2C0:0x2E0]=state[160:192]; ext[0x2E0:0x360]=state[704:832]
            ext[0x360:0x390]=state[832:880]; ext[0x390:0x4D0]=state[880:1200]
            payload=bytearray(canonical[:SAVE_BYTES]);payload[18:20]=bytes(2)
            struct.pack_into('>I',ext,12,zlib.crc32(payload))
            struct.pack_into('>I',ext,16,zlib.crc32(ext))
            if canonical[SAVE_BYTES:] != ext or sum(struct.unpack('>31936H',canonical[:SAVE_BYTES])) & 65535:
                raise ValueError('Native canonical bank loses complete imported state')
        elif len(bank) != BANK or reference.reference_pack(bank, state) != bank:
            raise ValueError('Saved bank fails the independent payload/profile/CRC encoding check')

    check('complete resident prefix', BLOB_RAM, blob)
    for start, end in ((0x8008ECA0, 0x80090120), (0x800CDB10, 0x800CE120)):
        check('complete installed flash owner', start, code[start - CODE_RAM:end - CODE_RAM])
    check('runtime magic', STATE_RAM, bytes.fromhex('AF535633'))
    check('runtime end guard', state_guard, bytes.fromhex('AF53C0DE') * 4)
    if console:
        packet=console['packet']; all_blob=files[BLOB].extract(rom)
        check('complete console startup packet',packet['ram'],all_blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']])
        check('console state initialized',console['state']['ram'],struct.pack('>4I',0x41464335,0,0,0))
        for workspace in ('scratch','hash'):
            check('console '+workspace+' guard',console[workspace]['guard'],bytes.fromhex('AF4355DE')*4)
    call(0x800CDBE0, expected=1)
    size = 0x4100 if writing else 0x10100
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('V3 flash fixture allocation failed')
    transfer, transfer_size = allocation + 16, size - 0x100
    guards = (allocation, transfer + transfer_size, allocation + size - 16, TEST_STACK - 0xA00, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)

    def read_chip():
        parts = []
        for start in range(0, FLASH_BYTES, transfer_size):
            call(0x800CDE54, [transfer, start // 128, transfer_size // 128], 0)
            parts.append(debug.read_memory(transfer, transfer_size))
        check('complete-chip transfer guard', transfer + transfer_size, edge)
        return b''.join(parts)

    initial = read_chip()
    if writing:
        if initial != b'\xFF' * FLASH_BYTES or debug.read_memory(SAVE_STATE, 32) != bytes(32):
            raise ValueError('Writer requires blank isolated FlashRAM and idle native pipeline')
        original = debug.read_memory(SAVE_RAM, SAVE_BYTES)
        old_runtime = debug.read_memory(STATE_RAM, state_bytes)
        if console:
            old_console=debug.read_memory(console['state']['ram'],console['state']['bytes'])
            expected_console=bytes((i*73+(i>>3)+19)&255 for i in range(6528))
            debug.write_memory(console['state']['ram']+16,expected_console)
        if collect_items:
            from v3_collection_smoke import prepare
            modified, state = prepare(debug, rom, report, call, check, record)
        else:
            modified = bytearray(original)
            # Storage fixtures: preserve the rest of the cold-boot payload,
            # install a synthetic town ID, and store the actual imported IDs.
            modified[0x2F68:0x2F6A] = bytes.fromhex('3012')
            struct.pack_into('>H', modified, 0x34, 0x3225)
            struct.pack_into('>H', modified, 0x20 + 0xBD0 + 0x14, 0x32BB)
            debug.write_memory(SAVE_RAM, bytes(modified))
            state = bytearray(old_runtime[16:-16]) if console else bytearray.fromhex(report['save_runtime']['profile_hex']) + bytearray(512)
            state[profile_bytes + (137 >> 3)] |= 1 << (137 & 7)
            state[profile_bytes + 128 + (174 >> 3)] |= 1 << (174 & 7)
            state[profile_bytes + 384 + (137 >> 3)] |= 1 << (137 & 7)
            debug.write_memory(STATE_RAM + 16, bytes(state))
        if test_sync:
            # The diagnostic transfer buffer must not consume memory needed by
            # the real synchronous writer's complete-bank allocation.
            if console:
                call(0x8009C0C0,[transfer,transfer+4,transfer+8])
                record({'save_probe_heap_before_release':struct.unpack('>3I',debug.read_memory(transfer,12))})
                call(0x8009C040,[allocation])
            sync_result=call(0x8008F7C8)
            if console:
                record({'save_probe_runtime_after_sync':debug.read_memory(STATE_RAM,16).hex(),
                        'console_state_after_sync':debug.read_memory(console['state']['ram'],16).hex()})
                allocation=call(0x8009BFC0,[size])
                if allocation & 15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
                    raise ValueError('Post-save diagnostic transfer allocation failed')
                transfer=allocation+16
                guards=(allocation,transfer+transfer_size,allocation+size-16,TEST_STACK-0xA00,TEST_STACK+0x40)
                for at in guards:debug.write_memory(at,edge)
            if sync_result!=0:raise ValueError('Native synchronous save failed; see recorded state/heap')
            synchronous = read_chip()
            validate(synchronous[:BANK], state)
            if synchronous[SAVE_BYTES:BANK] == bytes(BANK - SAVE_BYTES) or synchronous[BANK:] != b'\xFF' * BANK:
                raise ValueError('Synchronous writer did not retain its complete single-bank semantics')
            if logical_bank(synchronous[:BANK])[0x14:SAVE_BYTES] != modified[0x14:]:
                raise ValueError('Synchronous save changed the actual live payload')
            check('synchronous save updates only live header', SAVE_RAM, synchronous[:20]+modified[20:])
        expected_bank = None
        for step in range(160):
            before = int.from_bytes(debug.read_memory(SAVE_STATE, 4), 'big')
            if before > 6:
                raise ValueError('Native V3 save dispatch has an invalid state')
            result = call(SAVE_DISPATCH)
            control = struct.unpack('>8I', debug.read_memory(SAVE_STATE, 32))
            record({'v3_flash_save_step': step, 'state_before': before,
                    'state_after': control[0], 'page': control[1], 'result': result})
            if before == 1 and control[0] == 2:
                pointer = control[2]
                owner, retired = struct.unpack('>II', debug.read_memory(0x80146080, 8))
                framebuffers = struct.unpack('>4I', debug.read_memory(0x80146060, 16))
                record({'v3_save_framebuffer': f'{pointer:08X}', 'owner_state': owner,
                        'retired_pointer': f'{retired:08X}', 'framebuffers': [f'{p:08X}' for p in framebuffers]})
                # Native CFB 0 occupies 80000400..80025BFF below bootstrap code;
                # a framebuffer is not necessarily in the ordinary heap.
                if (pointer & 63 or owner != 4 or pointer != retired or pointer not in framebuffers
                        or not 0x80000400 <= pointer <= 0x80400000 - 0x25800):
                    raise ValueError(f'Invalid complete-bank save framebuffer {pointer:08X}')
                expected_bank = debug.read_memory(pointer, BANK)
                validate(expected_bank, state)
                if logical_bank(expected_bank)[0x14:SAVE_BYTES] != modified[0x14:]:
                    raise ValueError('Asynchronous save preparation changed the live payload')
            if result == 1:
                if control != (0,) * 8 or expected_bank is None:
                    raise ValueError('Native V3 save finished without complete preparation/cleanup')
                break
            if result != 0:
                raise ValueError('Native V3 save pipeline reported failure')
            record(debug.advance_game_frame())
        else:
            raise ValueError('Native V3 save exceeded the bounded frame count')
        saved = read_chip()
        if saved != expected_bank * 2:
            raise ValueError('Both complete banks must match native preparation, including the extension')
        export_directory.mkdir()
        (export_directory / 'test.flash').write_bytes(saved)
        manifest = {'rom_sha256': sha256(rom), 'flash_sha256': sha256(saved),
            'bank_sha256': sha256(expected_bank), 'working_state_hex': state.hex(),
            'synchronous_single_bank_passed': test_sync, 'asynchronous_two_banks_passed': True,
            'native_collection_populated_catalogue': collect_items,
            'ordinary_save_menu_tested': False, 'hardware_tested': False}
        if console:
            manifest.update(console_hex=expected_console.hex(),save_format=5,
                canonical_bank_sha256=sha256(logical_bank(expected_bank)))
        (export_directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        debug.write_memory(SAVE_RAM, original)
        debug.write_memory(STATE_RAM, old_runtime)
        if console:debug.write_memory(console['state']['ram'],old_console)
        check('original live payload restored', SAVE_RAM, original)
        check('original runtime state restored', STATE_RAM, old_runtime)
    else:
        manifest = json.loads((seed_directory / 'manifest.json').read_text())
        if manifest['rom_sha256'] != sha256(rom) or manifest['flash_sha256'] != sha256(initial):
            raise ValueError('Fresh native chip differs from the matching exported save')
        bank = initial[:BANK]
        state = bytes.fromhex(manifest['working_state_hex'])
        if console:expected_console=bytes.fromhex(manifest['console_hex'])
        validate(bank, state)
        if initial != bank * 2:
            raise ValueError('Export does not contain two matching complete banks')
        tail = debug.read_memory(SAVE_RAM + SAVE_BYTES, BANK - SAVE_BYTES)
        for page in (0, 512):
            call(0x8008F8A0, [transfer, page], 1)
            check('native full-bank reader including extension', transfer, bank)
            call(0x8008EE7C, [transfer, SAVE_BYTES], 0)
            call(0x8008EF0C, [transfer, 0x3012], 1)
            if console:check('bank probing does not load console progress',console['state']['ram']+16,bytes(6528))
        if console:
            # The complete-bank probe buffer must not starve the actual loader,
            # which allocates its own complete bank on this same native heap.
            call(0x8009C040,[allocation])
        for address in (0x8008F968, 0x8008F938):
            call(address, expected=1)
            check('complete native decoded payload', SAVE_RAM, logical_bank(bank)[:SAVE_BYTES])
            if console:check('all four console players restored',console['state']['ram']+16,expected_console)
            check('separate live catalogue/profile state', STATE_RAM + 16, state)
            check('load commits ready/town', STATE_RAM + 8, struct.pack('>II', 1, 0x3012))
            check('unnamed native RAM tail unchanged', SAVE_RAM + SAVE_BYTES, tail)
            call(0x8008EF6C, expected=1)
        if console:
            allocation=call(0x8009BFC0,[size])
            if allocation & 15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
                raise ValueError('Post-load diagnostic transfer allocation failed')
            transfer=allocation+16
            guards=(allocation,transfer+transfer_size,allocation+size-16,TEST_STACK-0xA00,TEST_STACK+0x40)
            for at in guards:debug.write_memory(at,edge)
        if read_chip() != initial:
            raise ValueError('Read-only fresh load changed cartridge storage')
    check('complete resident prefix retained', BLOB_RAM, blob)
    check('runtime end guard retained', state_guard, bytes.fromhex('AF53C0DE') * 4)
    if console:
        for workspace in ('scratch','hash'):
            check('console '+workspace+' guard retained',console[workspace]['guard'],bytes.fromhex('AF4355DE')*4)
        check('console state guard retained',console['state']['ram']+console['state']['bytes']-16,bytes.fromhex('AF4355DE')*4)
    for at in guards:
        check('private/stack guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_calls': calls, 'mode': 'write' if writing else 'fresh-read',
            'flash_sha256': manifest['flash_sha256'], 'ordinary_save_menu_tested': False,
            'hardware_tested': False, 'requires_checkpoint_restore': True}
