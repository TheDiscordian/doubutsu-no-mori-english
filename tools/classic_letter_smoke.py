"""One bounded native classic-loader, allocator, reader, and fallback check."""
import struct
from aflib import sha256
from accent_mail_overlays import Overlay, FONT_POINTER
from accent_mail_font import HOOKS
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_record import Record, Field, pack
from mail_catalog import templates
from mail_format import format_letter
from classic_letters import fields

EDGE = b'CLAS'*4


def words(*values):
    return struct.pack('>'+'I'*len(values), *values)


def exercise(debug, request, record):
    read = debug.read_memory
    calls = assertions = 0
    def write(at, data):
        debug.write_memory(at, data)
        record({'classic_write': f'{at:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected)); assertions += 1
        record({'classic_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native classic-letter mismatch: '+label)
    def call(at, args=(), expect=None, proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(result); calls += 1
        if expect is not None and result['return_value'] != expect:
            raise ValueError(f'Native classic-letter {at:08X} returned {result["return_value"]}, expected {expect}')
        return result['return_value']
    module = request['module']
    font = module['extended_font']['font']
    blob = bytes.fromhex(request['font_blob'])
    image, reloc = blob[:font['bytes']], blob[font['bytes']:]
    base = int.from_bytes(read(FONT_POINTER, 4), 'big')
    spec = Overlay(font['ram'], len(image), struct.unpack_from('>5I', reloc))
    moved = relocate_verified_data(spec, image, reloc, base)
    prior = font['classic_letters']
    old_sections = struct.unpack_from('>3I', bytes.fromhex(prior['previous_relocation']))
    check('retained startup font and mail code', base, moved[:sum(old_sections)])
    check('complete appended classic loader', base+prior['prefix_bytes'], moved[prior['prefix_bytes']:])
    classic_jump = words(0x08000000 | (((base+font['symbols']['af_classic_load']) >> 2) & 0x3FFFFFF), 0)
    check('installed native classic entry', 0x80093F04, classic_jump)
    for address, (_, _, name) in HOOKS.items():
        check('retained resident mail entry', address, words(0x08000000 | (((base+font['symbols'][name]) >> 2) & 0x3FFFFFF), 0))
    saved = read(SAVE_RAM, SAVE_BYTES)
    original_fields = read(0x80140680, 200)
    capital_address = int(module['symbols']['af_mail_generation_capital'], 16)
    original_capital = read(capital_address, 4)
    size = 0x2000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Classic fixture allocation failed before any writes')
    mail, split, output, work = allocation+0x20, allocation+0xE0, allocation+0x100, allocation+0x600
    guards = (allocation, mail+164, split+16, output+1040, work+3552,
              allocation+size-16, TEST_STACK-0x1800, TEST_STACK+0x40)
    for at in guards:
        write(at, EDGE)
    catalog = bytes.fromhex(request['catalog'])
    for number in (0x182, 0x53, 1):
        value = Record(4, 0, (number,), tuple((i, Field(b'English   ')) for i in sorted(fields(number))))
        reference = format_letter(value, templates(catalog, value))
        write(0x80140680, b'English   '*20)
        write(capital_address, words(0))
        before = bytes(range(164))
        write(mail, before); write(split, words(0xA5A5))
        call(0x80093F04, [mail+42, split, mail+148, mail+52, number], proof=(0x80093F04, classic_jump))
        check('complete classic snapshot with unchanged metadata', mail, before[:42]+pack(value))
        check('separate classic split output', split, words(128))
        call(int(module['symbols']['af_mail_restore'], 16), [output, mail+42, 122, work], 1)
        chunks = (reference.header, reference.body, reference.footer)
        offsets = [0, 0, 0]; payload = b''
        for index in (0, 2, 1):
            offsets[index] = len(payload); payload += chunks[index]
        expected = struct.pack('>7H2B', *offsets, *(len(s) for s in chunks), reference.header_split,
                               int(reference.final_capital), 0)+payload.ljust(1024, b'\0')
        check('complete native classic English text', output, expected)
    write(mail, bytes(range(164))); write(split, words(0xA5A5))
    call(0x80093F04, [mail+42, split, mail+148, mail+52, 0xC0], proof=(0x80093F04, classic_jump))
    check('native fallback metadata retained', mail, bytes(range(42)))
    check('translated native reserve body', mail+52, b'Extra'+b'\xCD'*91)
    check('translated native reserve footer', mail+148, b'Extra'+b' '*11)
    write(0x80140680, original_fields); write(capital_address, original_capital)
    for at in guards:
        check('retained allocation and stack guard', at, EDGE)
    check('saved payload unchanged', SAVE_RAM, saved)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    check('startup owner retained after fixture release', FONT_POINTER, words(base))
    return {'classic_letters': 'passed', 'native_calls': calls, 'memory_assertions': assertions,
            'allocated_test_bytes': size, 'image_uploads': 0, 'saved_layout_changed': False,
            'requires_checkpoint_restore': True}
