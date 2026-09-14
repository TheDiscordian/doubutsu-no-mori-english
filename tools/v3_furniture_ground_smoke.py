"""Current native ground-item windows, drop flags, and complete descriptor selection."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_ground import BLOB_SIZE, RAM, RELOC, RESIDENT, SECTIONS, SITES, SIZE, VROM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    ground = report.get('furniture_ground')
    if sha256(rom) != report['output_sha256'] or not ground:
        raise ValueError('Ground probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    edge = b'V3GD' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'ground_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Ground native check failed: ' + label)

    def call(address, args, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        return result['return_value']

    def put(at, *values):
        debug.write_memory(at, struct.pack('>' + 'I' * len(values), *values))

    check('complete current startup prefix', BLOB_RAM, blob)
    size = 0x10000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Ground fixture allocation failed')
    owner, table, source, dest, stack = (allocation + n for n in (16, 0xC000, 0xC100, 0xC200, 0xE000))
    debug.write_memory(allocation, bytes(size))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != ground['output_sha256'] or sha256(reloc) != ground['relocation_sha256']:
        raise ValueError('Changed ground-item owner proof')
    loaded = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=RESIDENT, sections=SECTIONS),
        data, reloc, owner, address_constants=(RAM + RESIDENT,))
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + RESIDENT, owner, owner + RESIDENT, len(reloc)])
    check('complete native-relocated ground owner and BSS', owner, loaded)
    proof = (owner, loaded[:SECTIONS[0]])
    saved_owner = debug.read_memory(0x80100CC0, 4)
    put(0x80100CC0, owner)
    guards = (allocation, table - 16, source - 16, dest - 16, dest + 16, stack - 0x800,
              stack + 0x200, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    before = debug.command('g')
    original_regs = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(original_regs) != 71 or original_regs[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Ground windows require the paused game frame')

    def window(regs, target):
        breakpoint = f'0,{target:x},4'
        if debug.command('Z' + breakpoint) != 'OK':
            raise ValueError('Ground breakpoint refused')
        try:
            if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                raise ValueError('Ground register write refused')
            stopped = debug.command('c')
            raw = debug.command('g')
            actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
            if stopped[:3] not in ('T05', 'S05') or actual[37] & 0xFFFFFFFF != target:
                raise ValueError(f'Ground window missed its continuation: {stopped}/{actual[37]:016X}')
            return actual
        finally:
            debug.command('z' + breakpoint)
            debug.command('G' + before)

    for start, _, temporary, destination, purpose in SITES:
        for item, selected, disabled in ((0x1004, False, False), (0x3225, True, False),
                                         (0x32BB, True, False), (0x32BB, False, True)):
            if disabled:
                put(BLOB_RAM + 0x7254, 0)
            try:
                regs = original_regs.copy()
                for i in range(1, 32):
                    if i not in (26, 27):
                        regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
                regs[1], regs[4], regs[9] = 1, item, item & 0xF000
                regs[29], regs[37] = extend(stack), extend(owner + start - RAM)
                wanted = regs.copy()
                kind = 1 if selected else item >> 12
                if temporary is None:
                    wanted[2] = 0
                    target = 0x8090FA28 if kind == 1 else 0x8090FA34
                else:
                    wanted[temporary] = item & 0xF000
                    target = start + 8
                wanted[destination] = kind
                actual = window(regs, owner + target - RAM)
                differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                    for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                record({'ground_window': f'{start:08X}', 'purpose': purpose, 'item': f'{item:04X}',
                        'selected': selected, 'disabled_profile': disabled, 'register_differences': differences,
                        'assertion': 'failed' if differences else 'passed'})
                if differences:
                    raise ValueError('Ground classification changed unrelated registers')
            finally:
                if disabled:
                    put(BLOB_RAM + 0x7254, 1)

    for item in (0x1004, 0x3225, 0x32BB):
        for start, target in ((0x8090F888, 0x8090F8C8), (0x8090FA1C, 0x8090FA34)):
            regs = original_regs.copy()
            regs[1], regs[4], regs[9] = 1, item, item & 0xF000
            regs[29], regs[37] = extend(stack), extend(owner + start - RAM)
            actual = window(regs, owner + target - RAM)
            passed = actual[2] == 0x200 and actual[4] == item
            record({'native_drop_flag_path': f'{start:08X}', 'item': f'{item:04X}',
                    'flags': actual[2], 'identity_retained': actual[4] == item,
                    'assertion': 'passed' if passed else 'failed'})
            if not passed:
                raise ValueError('Native drop path did not retain furniture flags and identity')

    # Exact native 12-byte output: padding byte 1 is intentionally untouched.
    furniture = bytes.fromhex('070012341020304050607080')
    fallback = bytes.fromhex('090023452030405060708090')
    debug.write_memory(source, furniture + fallback)
    put(table + 8, source)
    put(table + 20, source + 12)
    for item, disabled in ((0x1004, False), (0x3225, False), (0x32BB, False), (0x32BB, True)):
        if disabled:
            put(BLOB_RAM + 0x7254, 0)
        try:
            debug.write_memory(dest, b'?' * 12)
            call(owner + 0x80911CD8 - RAM, [item, dest, 0, table], proof)
            expected = bytearray(fallback if disabled else furniture)
            expected[1] = ord('?')
            if not disabled:
                struct.pack_into('>H', expected, 2, 47)
            check('complete native furniture or disabled ground descriptor', dest, bytes(expected))
        finally:
            if disabled:
                put(BLOB_RAM + 0x7254, 1)
    check('input descriptor records unchanged', source, furniture + fallback)
    check('complete resident prefix unchanged', BLOB_RAM, blob)
    check('complete ground owner and BSS unchanged', owner, loaded)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(0x80100CC0, saved_owner)
    call(0x8009C040, [allocation])
    return {'ground_register_windows': 12, 'native_drop_flag_paths': 6,
            'complete_native_ground_descriptor_cases': 4,
            'ordinary_drop_pickup_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
