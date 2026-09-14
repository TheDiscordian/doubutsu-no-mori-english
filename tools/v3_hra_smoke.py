"""Bounded native HRA relocation, detour, group, score, and recommendation checks."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256, u32
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
import v3_hra as hra


def exercise(debug, rom_path, record, *, windows=True):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    hr = report.get('hra')
    if sha256(rom) != report['output_sha256'] or not hr:
        raise ValueError('HRA probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'hra_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native HRA check failed: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'HRA call {address:08X}: {result["return_value"]} != {expected}')
        return result['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, blob)
    capacity = hr['metadata_rows']
    extra = 0xA00 if capacity > hra.COUNT else 0
    size = 0x8400+extra
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('HRA fixture allocation failed')
    owner = allocation + 16
    layers, points, first, second = (allocation + extra + n for n in (0x7600, 0x7620, 0x7800, 0x7B00))
    data, reloc = (files[v].extract(rom) for v in (hra.NEW_VROM, hra.NEW_RELOC))
    if (sha256(data), sha256(reloc)) != (hr['output_sha256'], hr['relocation_sha256']):
        raise ValueError('Changed current HRA image')
    if owner + len(data) + len(reloc) > layers - 16:
        raise ValueError('HRA test areas overlap')
    expected = relocate_verified_data(SimpleNamespace(ram=hra.RAM, resident_bytes=len(data),
        sections=struct.unpack_from('>5I', reloc)), data, reloc, owner)
    debug.write_memory(allocation, bytes(size))
    call(0x800262D0, [hra.NEW_VROM, hra.NEW_VROM + len(data), hra.RAM, hra.RAM + len(data),
                     owner, owner + len(data), len(reloc)])
    check('complete native relocated HRA owner and cleared original BSS', owner, expected)
    linked = lambda address: owner + address - hra.RAM
    proof = (owner, expected[:hra.SECTIONS[0]])
    old_pointer = debug.read_memory(0x80107B50, 4)
    put(0x80107B50, owner)
    edge = b'V3HR' * 4
    guards = (allocation, layers - 16, first - 16, first + 512, second - 16, second + 512,
              allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    before = debug.command('g')
    initial = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(initial) != 71 or initial[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('HRA windows require the paused native game frame')
    run_windows, windows = windows, 0
    try:
        for row in hr['sites'] if run_windows else []:
            cases = [(0x1005, False), (0x3225 if windows % 4 == 0 else 0x32BB, False)]
            if row['kind'] == 'range' and row['start'] in (0x80926208, 0x809275BC):
                cases += [(0x3000, False), (0x32BB, True), (0xFFF, False)]
            for item, disabled in cases:
                put(BLOB_RAM + 0x7254, int(not disabled))
                regs = initial.copy()
                for i in range(1, 32):
                    if i not in (26, 27):
                        regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
                regs[row['source']] = item
                if row.get('paired'):
                    regs[row['lower_word'] >> 21 & 31] = item
                regs[29], regs[37] = extend(TEST_STACK), extend(linked(row['start']))
                wanted = regs.copy()
                selected = item & 0xFFFC in (0x3224, 0x32B8) and not disabled
                if row['kind'] == 'range':
                    wanted[1] = int(item < 0x1ECD)
                    if row['paired'] and item < 0x1000:
                        target = row['lower_target']
                    else:
                        wanted[1] = int(item < 0x1ECD or selected)
                        taken = bool(wanted[1]) == (row['branch'] >> 26 in (5, 21))
                        target = row['taken'] if taken else row['fall'] + (4 if row['branch'] >> 26 in (20, 21) else 0)
                        if taken:
                            word = row['delay']
                            if word >> 26 != 9:
                                raise ValueError('Unreviewed HRA delay effect')
                            value = wanted[word >> 21 & 31] + (word & 65535) - (65536 if word & 32768 else 0)
                            wanted[word >> 16 & 31] = extend(value)
                else:
                    offset = ((1161 if item & 0xFFFC == 0x3224 else 1198) * 4 + (item & 3)
                              if selected else item - 0x1000)
                    wanted[row['destination']] = extend(offset)
                    for word in (row['shift'], row['scale']):
                        value = wanted[word >> 16 & 31] & 0xFFFFFFFF
                        if word & 63 == 3:
                            value = (value - (0x100000000 if value & 0x80000000 else 0)) >> 2
                        else:
                            value <<= 2
                        wanted[word >> 11 & 31] = extend(value)
                    target = row['end']
                target = linked(target)
                stop = f'0,{target:x},4'
                if debug.command('Z' + stop) != 'OK':
                    raise ValueError('HRA breakpoint refused')
                try:
                    if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                        raise ValueError('HRA register write refused')
                    stopped = debug.command('c'); raw = debug.command('g')
                    actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
                    differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                        for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                    passed = stopped[:3] in ('T05', 'S05') and actual[37] & 0xFFFFFFFF == target and not differences
                    record({'hra_window': f'{row["start"]:08X}', 'item': f'{item:04X}',
                            'disabled': disabled, 'register_differences': differences,
                            'assertion': 'passed' if passed else 'failed'})
                    if not passed:
                        raise ValueError('HRA branch/index register result differs')
                    windows += 1
                finally:
                    debug.command('z' + stop); debug.command('G' + before)
                    put(BLOB_RAM + 0x7254, 1)
        # Predict native group assignment independently from the original types
        # and the full expanded metadata, including all unchanged native rows.
        table_at = hr['metadata_address'] - hra.RAM
        metadata = bytearray(expected[table_at:table_at + capacity * 4])
        series_at = 0x809283B0 - hra.RAM
        series = bytearray(expected[series_at:series_at + 55 * 3])
        for s in range(55):
            group, count = (5 if series[s * 3] == 1 else 0), 0
            for i in range(capacity):
                word = u32(metadata, i * 4)
                if word >> 26 == s:
                    if series[s * 3] != 1 or word >> 16 & 1023 >= 5:
                        struct.pack_into('>I', metadata, i * 4, word & 0xFC00FFFF | group << 16)
                        group += 1
                    count += 1
            series[s * 3 + 1] = count & 255
        put(layers, first); put(layers + 4, second)
        grid1, grid2 = bytearray(512), bytearray(512)
        items = ((grid1, 17, 0x3225), (grid1, 18, 0x32BB), (grid2, 34, 0x1414))
        search = bytearray(55 * 4)
        for grid, cell, item in items:
            struct.pack_into('>H', grid, cell * 2, item)
            index = (item - 0x1000) >> 2 if item < 0x2000 else (1161 if item & 0xFFFC == 0x3224 else 1198)
            word = u32(metadata, index * 4)
            s, group = word >> 26, word >> 16 & 1023
            put_mask = u32(search, s * 4) | 1 << group
            struct.pack_into('>I', search, s * 4, put_mask)
        debug.write_memory(first, grid1); debug.write_memory(second, grid2)
        call(linked(0x8092817C), [layers, 5], proof=proof)
        check(f'all {capacity} assigned native/imported metadata rows', owner + table_at, metadata)
        check('all native series counts including construction 21', owner + series_at, series)
        check('complete mixed-layer construction completion masks', linked(0x80929750), search)
        for group, item in ((19, 0x3224), (20, 0x32B8), (0, 0x1414), (21, 0)):
            call(linked(0x80925A5C), [group, 16], item, proof)
        put(BLOB_RAM + 0x7254, 0)
        call(linked(0x80925A5C), [20, 16], 0, proof)
        put(BLOB_RAM + 0x7254, 1)
        # Complete base-point evaluator: compare the actual native birth weights,
        # keeping unchanged wall/floor contributions in an empty-room baseline.
        debug.write_memory(first, bytes(512)); debug.write_memory(second, bytes(512))
        put(points, 0)
        call(linked(0x809274F8), [points, layers, 5, 0, 0], proof=proof)
        baseline = u32(debug.read_memory(points, 4), 0)
        debug.write_memory(first, grid1); debug.write_memory(second, grid2)
        put(points, 0)
        call(linked(0x809274F8), [points, layers, 5, 0, 0], proof=proof)
        weights = expected[0x80928680 - hra.RAM:hra.TABLE - hra.RAM]
        increment = sum(u32(weights, (u32(metadata, index * 4) >> 9 & 31) * 4) for index in (1161, 1198, 261))
        check('complete mixed-layer base points use actual donor birth properties', points, struct.pack('>I', baseline + increment))
        # Native range checks admit the one-past-table marker. It must not
        # become an out-of-range series-mask write in the expanded table.
        struct.pack_into('>H', grid1, 19 * 2, 0x1ECC)
        debug.write_memory(first, grid1)
        call(linked(0x8092817C), [layers, 5], proof=proof)
        check('one-past-native marker does not add a collection group', linked(0x80929750), search)
        put(points, 0)
        call(linked(0x809274F8), [points, layers, 5, 0, 0], proof=proof)
        check('one-past-native marker has zero point weight', points, struct.pack('>I', baseline + increment))
        if report['clothing'].get('display', {}).get('readers'):
            # Evaluate each placed orientation through the full native point
            # function; clothing is not added to construction completion masks.
            debug.write_memory(second, bytes(512))
            for rotation in range(4):
                grid = bytearray(512)
                struct.pack_into('>H', grid, 17*2, 0x3AFC | rotation)
                debug.write_memory(first, grid)
                put(points, 0)
                call(linked(0x809274F8), [points, layers, 5, 0, 0], proof=proof)
                clothing_points = u32(weights, 8*4)
                check('clothing mannequin uses its actual native birth weight', points,
                      struct.pack('>I', baseline+clothing_points))
        check('unchanged translated HRA code prefix', owner, expected[:hra.SECTIONS[0]])
        check('compiled suffix code retained', owner + hra.START, expected[hra.START:table_at])
        check('complete resident prefix retained', BLOB_RAM, blob)
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        put(BLOB_RAM + 0x7254, 1)
        debug.write_memory(0x80107B50, old_pointer)
    call(0x8009C040, [allocation])
    return {'native_hra_register_windows': windows, 'native_group_initialization': True,
            'native_mixed_layer_completion_masks': True, 'native_missing_item_selections': 5,
            'native_base_point_evaluations': 3+(4 if capacity > hra.COUNT else 0), 'one_past_native_marker_safe': True,
            'ordinary_house_evaluation_tested': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
