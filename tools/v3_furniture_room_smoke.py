"""Exercise installed room detours at native instruction boundaries, not gameplay."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_room import BLOB_SIZE, RAM, RELOC, VROM, signed
from v3_furniture_runtime import RESIDENT, SIZE
from v3_npc_draw_smoke import boot_proofs


def extend(value):
    value &= 0xFFFFFFFF
    return value | (0xFFFFFFFF00000000 if value & 0x80000000 else 0)


def signed64(value):
    return value - (1 << 64) if value >> 63 else value


def delay_effect(word, registers, read_word):
    """Only the reviewed retained delay instructions, independent of detour code."""
    op, source, dest = word >> 26, word >> 21 & 31, word >> 16 & 31
    if op == 9:
        registers[dest] = extend(registers[source] + signed(word))
    elif op == 35:
        registers[dest] = extend(read_word((registers[source] + signed(word)) & 0xFFFFFFFF))
    elif op == 0 and word & 63 in (37, 42):
        target = word >> 11 & 31
        registers[target] = (registers[source] | registers[dest] if word & 63 == 37
                             else int(signed64(registers[source]) < signed64(registers[dest])))
    else:
        raise ValueError(f'Unreviewed room delay operation {word:08X}')
    registers[0] = 0


def expected_window(row, registers, selected, read_word):
    result = registers.copy()
    value = registers[row['source']] & 0xFFFFFFFF
    if row['kind'] in ('collision', 'tile_lookup', 'model_dma'):
        index = value >> 2 if row['kind'] == 'collision' else value
        item = ({1161: 0x3224, 1198: 0x32B8}[index] if selected else index * 4 + 0x1000)
        result[row['destination']] = extend(item)
        if row['kind'] == 'collision':
            result[5] = item & 65535
        elif row['kind'] == 'model_dma':
            result[4], result[5] = index & 65535, item & 65535
        return row['end'], result
    if row['kind'] == 'transform':
        if row['mode'] == 1:
            offset = ((1024 + ((value & 4095) >> 2)) * 4 + (value & 3)
                      if selected else value - 4096)
            result[row['destination']] = extend(offset)
            if row['after'] == 0x30450003:
                result[5] = offset & 3
            elif row['after'] == 0x00042083:
                result[4] = extend(signed64(extend(offset)) >> 2)
            else:
                raise ValueError('Unknown room index continuation')
        else:
            result[row['destination']] = 1 if selected else value >> 12 & 15
        return row['end'], result
    result[1] = int(signed64(registers[row['source']]) < 0x1ECD or selected)
    if row['paired'] and signed64(registers[row['source']]) < 0x1000:
        # The original upper SLTI is the lower branch's delay instruction.
        return row['lower_target'], result
    taken = bool(result[1]) == (row['branch'] >> 26 in (5, 21))
    if taken:
        delay_effect(row['delay'], result, read_word)
        return row['taken'], result
    return row['fall'] + (4 if row['branch'] >> 26 in (20, 21) else 0), result


def exercise(debug, rom_path, record, *, identity_only=False):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    room = report.get('furniture_identity' if identity_only else 'furniture_room')
    if sha256(rom) != report['output_sha256'] or not room or report['resident_blob_bytes'] != BLOB_SIZE:
        raise ValueError('Room probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'room_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Room native check failed: ' + label)

    def call(address, args):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=boot.get(address))
        record(result)
        return result['return_value']

    def word(address):
        return struct.unpack('>I', debug.read_memory(address, 4))[0]

    check('complete 48-KiB startup prefix', BLOB_RAM, blob)
    check('startup installed', 0x8019ACD0, struct.pack('>I', 1))
    size = 0x1D000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Room probe allocation failed')
    live, stack = allocation + 16, allocation + 0x1C000
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    final_room = report.get('furniture_identity') or room
    if sha256(data) != final_room['output_sha256'] or sha256(reloc) != room['relocation_sha256']:
        raise ValueError('Changed room owner or relocation proof')
    sections = struct.unpack_from('>5I', reloc)
    expected = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=RESIDENT,
                                                       sections=sections), data, reloc, live)
    if live + RESIDENT + len(reloc) >= stack - 0x1000:
        raise ValueError('Room fixture overlaps test stack')
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + RESIDENT, live, live + RESIDENT, len(reloc)])
    check('complete relocated room and BSS', live, expected)
    saved_owner = debug.read_memory(0x80100E00, 4)
    debug.write_memory(0x80100E00, struct.pack('>I', live))
    stack_data = b'\xA5' * 0x200
    debug.write_memory(stack, stack_data)
    edge = b'V3RM' * 4
    guards = (allocation, allocation + size - 16, stack - 0x1000, stack + 0x200)
    for at in guards:
        debug.write_memory(at, edge)
    check('native game context', 0x800D334C, bytes.fromhex('27BDFFE0AFB00014'))
    before = debug.command('g')
    if len(before) != 71 * 16 or int(before[37 * 16:38 * 16], 16) & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Room windows require the paused native game frame')
    if debug.thread_snapshot() != {'pointer': '80145630', 'state': 4, 'id': 4}:
        raise ValueError('Room windows require the native graph thread')
    original_registers = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    windows = 0
    # Each distinct patched instruction sequence needs register/delay proof.
    # This does not attempt every item or every gameplay combination.
    for row in room['sites']:
        cases = [(0x1000, False, False), (0x3225, True, False), (0x3000, False, False),
                 (0x32B8, False, True)]
        if identity_only:
            cases = [(1, False, False), (947, False, False), (1161, True, False),
                     (1198, True, False), (1198, False, True), (65535, False, False)]
        if row['kind'] == 'range' and row['paired']:
            cases.append((0xFFF, False, False))
        for value, selected, disabled in cases:
            enabled_at = BLOB_RAM + 0x7254
            if disabled:
                debug.write_memory(enabled_at, bytes(4))
            registers = original_registers.copy()
            for i in range(1, 32):
                if i not in (26, 27):
                    registers[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
            registers[row['source']] = extend(value)
            if identity_only and row['kind'] == 'collision':
                registers[5] = extend(value * 4)
            elif identity_only and row['kind'] == 'model_dma':
                registers[18] = extend(value * 4 + 0x1000)
            registers[29] = extend(stack)
            registers[37] = extend(live + row['start'] - RAM)
            linked_target, wanted = expected_window(row, registers, selected, word)
            target = live + linked_target - RAM
            if not live <= target < live + sections[0]:
                raise ValueError('Room window stop is outside verified native text')
            breakpoint = f'0,{target:x},4'
            if debug.command('Z' + breakpoint) != 'OK':
                raise ValueError('Room window breakpoint refused')
            try:
                if debug.command('G' + ''.join(f'{n:016x}' for n in registers)) != 'OK':
                    raise ValueError('Room window registers refused')
                stopped = debug.command('c')
                after = debug.command('g')
                observed = [int(after[i:i + 16], 16) for i in range(0, len(after), 16)]
                compared = (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70))
                differences = {str(i): [f'{wanted[i]:016X}', f'{observed[i]:016X}']
                               for i in compared if wanted[i] != observed[i]}
                passed = stopped[:3] in ('T05', 'S05') and observed[37] & 0xFFFFFFFF == target and not differences
                record({'room_window': f'{row["start"]:08X}', 'item': f'{value:04X}',
                        'selected': selected, 'disabled_profile': disabled,
                        'expected_pc': f'{target:08X}', 'observed_pc': f'{observed[37]:016X}',
                        'register_differences': differences, 'assertion': 'passed' if passed else 'failed'})
                if not passed:
                    raise ValueError(f'Room window {row["start"]:08X}/{value:04X} failed: {differences}')
                windows += 1
            finally:
                debug.command('z' + breakpoint)
                debug.command('G' + before)
                if disabled:
                    debug.write_memory(enabled_at, struct.pack('>I', 1))
    check('original caller stack unchanged', stack, stack_data)
    check('complete resident prefix unchanged', BLOB_RAM, blob)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(0x80100E00, saved_owner)
    call(0x8009C040, [allocation])
    if identity_only:
        return {'native_room_identity_windows': windows, 'sites': len(room['sites']),
                'ordinary_pickup_tested': False, 'requires_checkpoint_restore': True}
    return {'native_room_windows': windows, 'range_sites': room['range_sites'],
            'index_sites': room['index_sites'], 'field_type_sites': room['field_type_sites'],
            'ordinary_placement_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
