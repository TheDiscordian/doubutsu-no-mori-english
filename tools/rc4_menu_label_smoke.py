"""Execute both assembled price-adapter branches with a temporary font capture."""
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from catalogue_names import Image
from flash_mail import SAVE_BYTES, SAVE_RAM
from npc_mail_show import relocate_verified_data
from rc4_menu_labels import CAT, CAT_REL, RAM, ROOT, START, checked_adapter, source_hashes
from runtime_layout import GUARD_ADDRESS, GUARD_WORD, TEST_STACK


def words(*values):
    return struct.pack('>'+'I'*len(values), *values)


def floating(value):
    return struct.unpack('>I', struct.pack('>f', value))[0]


def exercise(debug, request, rom, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Unowned menu-label test build')
    report = json.loads((directory/'fixes.json').read_text())
    if report['output_sha256'] != sha256(rom) or report['sources'] != source_hashes():
        raise ValueError('Stale menu-label fixture or cartridge')
    files = by_vrom(rom)
    data, relocation = files[CAT].extract(rom), files[CAT_REL].extract(rom)
    checked_adapter(data[START:])
    read, write = debug.read_memory, debug.write_memory
    saved = read(SAVE_RAM, SAVE_BYTES)
    guard = words(*([GUARD_WORD]*4))
    if read(GUARD_ADDRESS, 16) != guard or read(0x8003CE34, 4) != bytes(4):
        raise ValueError('Existing module guard or faulted-thread failure')
    entry = files[CODE_VROM].extract(rom)[0x80090E98-CODE_RAM:0x80090EA0-CODE_RAM]
    if read(0x80090E98, 8) != entry:
        raise ValueError('Unexpected actual native font entry')
    def call(at, args=(), proof=None):
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(result)
        return result
    allocation = call(0x8009BFC0, (0xE000,))['return_value']
    if allocation & 15 or not 0x801A0000 <= allocation <= 0x80400000-0xE000:
        raise ValueError('No bounded native menu-label test allocation')
    base = allocation+16
    spec = Image(RAM, len(data), struct.unpack_from('>5I', relocation))
    moved = relocate_verified_data(spec, data, relocation, base)
    stub, text = allocation+0xD200, allocation+0xD240
    if base+len(moved)+16 > stub:
        raise ValueError('Price fixture overlaps relocated catalogue')
    capture = words(0x00A01025, 0x00C01825, 0xAFA70000, 0x03E00008, 0)
    edge = b'RCLB'*4
    guards = (allocation, base+len(moved), stub-16, stub+len(capture), text-16, text+16,
              allocation+0xE000-16)
    write(base, moved)
    write(stub, capture)
    for at in guards: write(at, edge)
    jump = words(0x08000000 | (stub >> 2 & 0x3FFFFFF), 0)
    write(0x80090E98, jump)
    cases = []
    for price, raw in ((12345, b'12345'), (0, bytes.fromhex('1af6011ac3'))):
        write(text, raw+b'\xA5'*11)
        write(TEST_STACK+0x40, words(price))
        args = [0, text, 5, floating(57), floating(168), 205, 0, 0, 255, 0, 0,
                floating(.75), floating(.75), 0]
        result = call(base+START, args, (base, moved))
        expected_pointer, length = (text, 5) if price else (base+START+84, 12)
        expected_text = raw if price else b'Not for Sale'
        if ((result['return_value'], result['return_value_v1']) != (expected_pointer, length)
                or read(expected_pointer, length) != expected_text
                or read(TEST_STACK, 4) != words(floating(57 if price else 48))
                or read(TEST_STACK+0x10, 4) != words(floating(168 if price else 167))
                or read(TEST_STACK+0x2C, 8) != words(*([floating(.75 if price else .875)]*2))
                or read(TEST_STACK+0x14, 24) != words(205, 0, 0, 255, 0, 0)
                or read(TEST_STACK+0x34, 4) != words(0)
                or read(TEST_STACK+0x40, 4) != words(price)
                or read(text, 16) != raw+b'\xA5'*11):
            raise ValueError('Native catalogue adapter arguments or caller buffer differ')
        cases.append({'price': price, 'text': expected_text.hex(), 'length': length,
                      'stack_restored': True, 'caller_buffer_retained': True,
                      'coordinates_and_scales_match': True})
        record({'price_adapter_case': cases[-1]})
    write(0x80090E98, entry)
    if (read(0x80090E98, 8) != entry or read(base, len(moved)) != moved
            or read(stub, len(capture)) != capture or read(SAVE_RAM, SAVE_BYTES) != saved
            or read(GUARD_ADDRESS, 16) != guard
            or any(read(at, 16) != edge for at in guards)
            or read(0x8003CE34, 4) != bytes(4)):
        raise ValueError('Price fixture changed code, save data, guards, or fault state')
    call(0x8009C040, (allocation,))
    return {'price_adapter_native_cases': cases, 'font_entry_restored': True,
            'save_unchanged': True, 'guards_intact': True, 'allocation_released': True,
            'rom_sha256': sha256(rom), 'fixture_sha256': sha256((ROOT/'tools/rc4_menu_label_smoke.py').read_bytes()),
            'requires_checkpoint_restore': True, 'font_drawing_stubbed': True,
            'ordinary_menu_entry': False, 'native_drawing_verified': False}
