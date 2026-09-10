"""Bounded letter UI probe using cartridge-loaded MIPS code and isolated data."""
import json
import struct

from aflib import by_vrom, sha256
from catalogue_names import Image
from flash_mail import SAVE_RAM, SAVE_BYTES
from letter_ui_fix import ROOT, PARTS, source_hashes
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

ROM_SHA = '0032a12d0c84810b89e2186dab524130b7f09506c6ab163c27c357fddf1d8ae3'
EDGE = b'LTUI'*4
def words(*values): return struct.pack('>'+'I'*len(values), *values)
def floating(value): return struct.unpack('>I', struct.pack('>f', value))[0]


def exercise(debug, request, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Letter probe needs an owned build')
    rom = (directory/'animal-forest-title-preview.z64').read_bytes()
    report = json.loads((directory/'fixes.json').read_text())
    if sha256(rom) != ROM_SHA or report['output_sha256'] != ROM_SHA or report['sources'] != source_hashes():
        raise ValueError('Changed compiled letter UI probe source/cartridge')
    files = by_vrom(rom); read = debug.read_memory; assertions = calls = 0
    def write(at, data):
        debug.write_memory(at, data)
        record({'letter_ui_write': f'{at:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    def check(label, at, expected):
        nonlocal assertions
        observed = read(at, len(expected)); assertions += 1
        record({'letter_ui_check': label, 'passed': observed == expected, 'address': f'{at:08X}',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected: raise ValueError('Native letter UI mismatch: '+label)
    def call(at, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(result); calls += 1; return result['return_value']
    saved = read(SAVE_RAM, SAVE_BYTES)
    size = 0x30000; allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native letter UI fixture allocation failed')
    locations = {'address': allocation+0x10, 'board': allocation+0x4010}
    board, scratch, game, graph, gfx = (allocation+v for v in (0x8000, 0x8200, 0x8400, 0x8500, 0x10000))
    guards = [allocation+size-16, board-16, board+192, scratch-16, scratch+256,
              game-16, game+16, graph-16, graph+0x300, gfx-16, gfx+0x10000,
              TEST_STACK-0x800, TEST_STACK+0x40]
    loader_at = 0x1060+0x800262D0-0x80025C60; loader = rom[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native cartridge loader')
    loaded = {}
    for name, spec in PARTS.items():
        data = files[spec['new_vrom']].extract(rom); rel = files[spec['new_reloc']].extract(rom)
        profile = report['parts'][name]; base = locations[name]
        if sha256(data) != profile['overlay_sha256'] or sha256(rel) != profile['relocation_sha256']:
            raise ValueError('Changed owned letter UI image')
        guards += [base-16, base+len(data)+len(rel)]
        expected = relocate_verified_data(Image(spec['ram'], len(data), struct.unpack_from('>5I', rel)), data, rel, base)
        call(0x800262D0, [spec['new_vrom'], spec['new_vrom']+len(data), spec['ram'], spec['ram']+len(data),
                         base, base+len(data), len(rel)], (0x800262D0, loader))
        check(name+' complete cartridge load/relocation', base, expected)
        loaded[name] = expected
    for at in guards: write(at, EDGE)
    for at, count in ((board, 192), (scratch, 256), (game, 16), (graph, 0x300)):
        write(at, bytes(count))
    def helper(part, name, args):
        start = report['parts'][part]['previous_resident_bytes']; base = locations[part]
        return call(base+report['parts'][part]['symbols'][name], args, (base+start, loaded[part][start:]))
    # The single reported Limberg case, one already-correct NPC, and a player.
    names = files[0x2C00000].extract(rom)
    cases = () if request.get('resume_after_names') else (
        (b'Limberg ', bytes.fromhex('7BCECB032020'), 1),
        (b'Buzz    ', b'Buzz  ', 1), (b'Player', b'Player', 0))
    for name, fallback, kind in cases:
        indices = [i for i in range(216) if names[32+i*8:40+i*8] == name] if kind else [0]
        if len(indices) != 1: raise ValueError('Changed English recipient table identity')
        mail_name = bytearray(18); mail_name[:6] = fallback; mail_name[12] = indices[0]; mail_name[16] = kind
        write(scratch, mail_name); write(scratch+32, b'?'*8)
        length = helper('address', 'af_ui_address_name', [scratch+32, scratch])
        if length != len(name): raise ValueError('Changed native recipient display length')
        check('reported or retained recipient name', scratch+32, name)
        check('saved recipient record retained', scratch, mail_name)
    # Real font dispatch for both native prompt arrays and the Limberg name.
    write(game, words(graph))
    for offset, english in ((0x1AD8, b'Choose an addressee.'), (0x1AE4, b'Your address book is empty!')):
        source = locations['address']+offset; write(scratch+64, words(12))
        translated = helper('address', 'af_ui_prompt', [source, scratch+64])
        check('complete English prompt', translated, english); check('English prompt length', scratch+64, words(len(english)))
        write(graph+0x298, words(gfx, gfx+0xF000))
        helper('address', 'af_ui_prompt_draw', [game, source, 12, floating(88), floating(112),
            80, 80, 230, 255, 0, 0, floating(1), floating(1), 0])
        end = int.from_bytes(read(graph+0x298, 4), 'big')
        if not gfx < end < gfx+0xE000: raise ValueError('Prompt draw escaped its owned graphics buffer')
    mail_name = bytearray(18); mail_name[:6] = bytes.fromhex('7BCECB032020'); mail_name[12] = 132; mail_name[16] = 1
    write(scratch, mail_name); write(graph+0x298, words(gfx, gfx+0xF000))
    helper('address', 'af_ui_address_draw', [game, scratch, 6, floating(133), floating(115),
        0, 135, 20, 255, 0, 1, floating(.75), floating(.75), 0])
    end = int.from_bytes(read(graph+0x298, 4), 'big')
    if not gfx < end < gfx+0xE000: raise ValueError('Recipient draw escaped its owned graphics buffer')
    check('drawing retains saved recipient', scratch, mail_name)
    # Draft normalisation only; this does not simulate the entire menu constructor.
    original = bytearray(192); original[0x1A:0x20] = b'Player'; original[5] = 3; original[7] = 8
    original[0x32:0x3C] = bytes.fromhex('0AC31C')+b' '*7
    original[0x3C:0x9C] = b'Kept body.'.ljust(96, b' ')
    original[0x9C:0xAC] = b'Player'+bytes.fromhex('607C')+b' '*8
    english = bytearray(original); english[0x32:0x35] = b'To '; english[0x2F] = 3
    english[0x9C:0xAC] = b'from Player'.ljust(16, b' '); english[7] = 11
    for mode, expected in ((0, english), (2, english), (1, original)):
        write(board, original); helper('board', 'af_ui_defaults', [board, mode])
        check('draft defaults or read-only retention', board, expected)
    custom = bytearray(original); custom[0x32:0x3C] = b'Hi there! '; custom[0x9C:0xAC] = b'Custom signoff! '
    write(board, custom); helper('board', 'af_ui_defaults', [board, 0]); check('custom text retained', board, custom)
    check('live save remains untouched', SAVE_RAM, saved)
    for at in guards: check('owned RAM/stack guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'native_letter_ui_calls': calls, 'assertions': assertions, 'save_unchanged': True,
            'code_uploaded': False, 'fixture_released': True, 'requires_checkpoint_restore': True,
            'retained_name_checks': 'build/v1-letter-ui-native-01/results.json' if not cases else None,
            'complete_constructor_tested': False, 'hardware_acceptance': False}
