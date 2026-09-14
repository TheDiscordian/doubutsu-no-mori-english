"""Exercise complete native room-grid functions and selected shop eligibility."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_fields import BLOB_SIZE


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('furniture_fields'):
        raise ValueError('Field probe requires its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    edge = b'V3FG' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'field_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Field native check failed: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Field call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    check('complete current startup prefix', BLOB_RAM, blob)
    allocation = call(0x8009BFC0, [0x1000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x803FF000:
        raise ValueError('Field test allocation failed')
    pointers = [allocation + 16 + i * 0x240 for i in range(5)]
    source0, source1, assigned0, assigned1, mapped = pointers
    guards = [allocation + 0xFF0, TEST_STACK - 0x800, TEST_STACK + 0x40]
    for at in pointers:
        guards += [at - 16, at + 512]
    for at in guards:
        debug.write_memory(at, edge)
    inputs = [{10: 0x1000, 33: 0x3225, 50: 0x3000, 254: 0x32B8},
              {70: 0x1000, 71: 0x32B9}]
    sources = []
    for at, entries in zip(pointers, inputs):
        values = [0] * 256
        for index, item in entries.items():
            values[index] = item
        data = struct.pack('>256H', *values)
        sources.append(data)
        debug.write_memory(at, data)
    for disabled in (False, True):
        if disabled:
            debug.write_memory(BLOB_RAM + 0x7254, bytes(4))
        wanted_maps, wanted_indices, serial = [], [], 0
        for entries in inputs:
            item_map = [0] * 256
            index_map = [0xA5A5] * 256
            # Retain the native function's initialization behaviour: only the
            # first destination entry is initialized, not the complete grid.
            index_map[0] = 0xFFFF
            for index, item in sorted(entries.items()):
                if item == 0x3000 or disabled and item & 0xFFFC == 0x32B8:
                    continue
                item_map[index], index_map[index] = item, serial
                serial += 1
            wanted_maps.append(struct.pack('>256H', *item_map))
            wanted_indices.append(struct.pack('>256H', *index_map))
        debug.write_memory(assigned0, b'\xA5' * 512)
        debug.write_memory(assigned1, b'\xA5' * 512)
        call(0x800BE844, [assigned0, source0, assigned1, source1])
        check('first-layer sequential furniture indices', assigned0, wanted_indices[0])
        check('second-layer sequential furniture indices', assigned1, wanted_indices[1])
        for layer, source in enumerate((source0, source1)):
            debug.write_memory(mapped, b'\xA5' * 512)
            call(0x800BEA50, [mapped, source])
            check('complete native furniture grid with selected imports', mapped, wanted_maps[layer])
        call(0x800BEE50, [0x3227], 1)
        call(0x800BEE50, [0x32BB], int(not disabled))
        call(0x800BEE50, [0x3000], 0)
        if disabled:
            debug.write_memory(BLOB_RAM + 0x7254, struct.pack('>I', 1))
    # Unchanged native birth types: Halloween is not shop-eligible; event is.
    call(0x800BEE50, [0x1000], 0)
    call(0x800BEE50, [0x1004], 1)
    for index in (1161, 1198):
        call(0x800BED5C, [index, 0], 0xFFFFFFFF)
    check('first source grid unchanged', source0, sources[0])
    check('second source grid unchanged', source1, sources[1])
    check('complete resident prefix retained', BLOB_RAM, blob)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_complete_field_functions': 2, 'mixed_layers_tested': 2,
            'disabled_profiles_tested': True, 'native_shop_and_action_sound_rules_tested': True,
            'ordinary_placement_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
