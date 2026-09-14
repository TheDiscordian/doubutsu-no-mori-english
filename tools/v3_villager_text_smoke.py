"""Current native shared-name, phrase, reset, and insertion checks."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_villager_text import DATA, STRIDE


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes(); report = json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['villager_text']:
        raise ValueError('Villager text probe needs its exact current cartridge')
    files = by_vrom(rom); blob = files[BLOB].extract(rom)
    actor, animal = MODULE_RAM + 0x6500, MODULE_RAM + 0x6690
    output, temporary, text = MODULE_RAM + 0x6D01, MODULE_RAM + 0x6DC0, MODULE_RAM + 0x6E00
    edge = b'V3TX' * 4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'v3_text_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('V3 text check failed: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native V3 text return value')

    def output_call(label, address, args, expected, returned=None):
        debug.write_memory(output - 16, edge + b'!' * 16 + edge)
        call(address, args, returned)
        check(label, output - 16, edge + expected + b'!' * (16 - len(expected)) + edge)

    def insert(label, address, opcode, expected):
        original = b'Hi ' + bytes((0x7F, opcode)) + b'!'
        result = b'Hi ' + expected.rstrip(b' ') + b'!'
        debug.write_memory(text - 16, edge + original.ljust(1024, b' ') + edge)
        call(address, [actor, text, 3, len(original)], len(result))
        check(label, text, result)
        check('insertion leading guard', text - 16, edge)
        check('insertion trailing guard', text + 1024, edge)

    check('complete startup blob', BLOB_RAM, blob)
    check('startup installed', 0x8019ACD0, struct.pack('>I', 1))
    actor_data = bytearray(0x180); actor_data[2] = 3
    struct.pack_into('>I', actor_data, 0x174, animal)
    debug.write_memory(actor, actor_data)
    for address in (actor - 16, actor + 0x180, animal + 0x540, TEST_STACK - 0x800, TEST_STACK + 0x40):
        debug.write_memory(address, edge)
    phrase_resource = files[0x2E00000].extract(rom)
    original_row = next(phrase_resource[at:at + 16] for at in range(32, len(phrase_resource), 16)
                        if phrase_resource[at + 4:at + 6] == b'\xE0\x00')
    if len(original_row[6:].rstrip(b' ')) <= 4:
        raise ValueError('Original-reset fixture needs a retained native default key')
    for row in report['villager_text']['imports']:
        npc = int(row['actor_id'], 16)
        name = row['name'].encode().ljust(8, b' ')
        phrase = row['catchphrase'].encode().ljust(10, b' ')
        key = bytes.fromhex(row['saved_default_key'])
        animal_data = bytearray(b'\xA5' * 0x540)
        struct.pack_into('>H', animal_data, 0, npc)
        debug.write_memory(animal, animal_data)
        call(0x800A9EC8, [actor])
        animal_data[0x4E5:0x4E9] = key
        check('reset changes only four saved bytes', animal, bytes(animal_data))
        output_call('eight-byte imported name', 0x80196044, [output, 8, npc], name, 1)
        output_call('six-byte compatibility name', 0x800ACC38, [output, npc & 255], name[:6])
        output_call('actor imported name', 0x80195D20, [output, actor], name)
        insert('actual talk-name insertion', 0x80195E2C, 0x1B, name)
        output_call('full default phrase', 0x80194FDC, [output, 10, npc, animal + 0x4E5], phrase, 1)
        output_call('actor default phrase', 0x8019521C, [output, actor], phrase)
        insert('actual catchphrase insertion', 0x801952F4, 0x1C, phrase)
        # Borrow the other pilot's phrase through the real native four-byte setter.
        other = next(r for r in report['villager_text']['imports'] if r != row)
        other_id = int(other['actor_id'], 16)
        key_pointer = BLOB_RAM + DATA + (other_id - 0xE0DA) * STRIDE + 26
        call(0x800A9E54, [animal, key_pointer])
        animal_data[0x4E5:0x4E9] = bytes.fromhex(other['saved_default_key'])
        check('borrowed reference preserves the animal', animal, bytes(animal_data))
        output_call('borrowed imported phrase', 0x8019521C, [output, actor], other['catchphrase'].encode().ljust(10, b' '))
        debug.write_memory(temporary, b'Yup!')
        call(0x800A9E54, [animal, temporary])
        output_call('custom phrase remains literal', 0x8019521C, [output, actor], b'Yup!      ')
        debug.write_memory(temporary, original_row[:4])
        call(0x800A9E54, [animal, temporary])
        output_call('borrowed original phrase', 0x8019521C, [output, actor], original_row[6:])
    # Original reset and load routines execute through the checked return bridges.
    animal_data = bytearray(b'\xA5' * 0x540); animal_data[0:2] = b'\xE0\x00'
    debug.write_memory(animal, animal_data)
    call(0x800A9EC8, [actor]); animal_data[0x4E5:0x4E9] = original_row[:4]
    check('original reset changes only its saved key', animal, bytes(animal_data))
    original_name = files[0x2C00000].extract(rom)[32:40]
    output_call('original actor name retained', 0x80195D20, [output, actor], original_name)
    output_call('original default retained', 0x8019521C, [output, actor], original_row[6:])
    for row in report['villager_text']['imports']:
        debug.write_memory(temporary, bytes.fromhex(row['saved_default_key']))
        call(0x800A9E54, [animal, temporary])
        output_call('original villager borrows imported phrase', 0x8019521C,
                    [output, actor], row['catchphrase'].encode().ljust(10, b' '))
    special = struct.unpack_from('>H', files[CODE_VROM].extract(rom), 0x8010B510 - CODE_RAM)[0]
    struct.pack_into('>I', actor_data, 0x174, 0); struct.pack_into('>H', actor_data, 6, special)
    debug.write_memory(actor, actor_data)
    special_name = files[0x2C00000].extract(rom)[32 + 216 * 8:40 + 216 * 8]
    output_call('special actor name retained', 0x80195D20, [output, actor], special_name)
    output_call('missing import causes no name write', 0x80196044, [output, 8, 0xE0DA], b'', 0)
    output_call('short destination causes no write', 0x80196044, [output, 7, 0xE0EA], b'', 0)
    for address in (actor - 16, actor + 0x180, animal + 0x540, TEST_STACK - 0x800, TEST_STACK + 0x40):
        check('fixture guard', address, edge)
    check('complete immutable V3 blob', BLOB_RAM, blob)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'imported_text_identities': 2, 'native_reset_and_setter_tested': True,
            'native_insertions_tested': True, 'ordinary_move_in_tested': False,
            'save_reload_tested': False, 'requires_checkpoint_restore': True}
