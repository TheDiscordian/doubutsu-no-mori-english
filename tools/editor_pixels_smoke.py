"""One isolated native draft batch: real loader, editing helpers, and body draws."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from catalogue_names import Image
from editor_pixel_fix import ROOT, PARTS, sources
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

ROM_SHA = '7c43f742009e391cae42bdf410f239f8a9c3aaf58003fd4f27371561109313ad'
EDGE = b'PXED'*4
def words(*values): return struct.pack('>'+'I'*len(values), *values)
def half(*values): return struct.pack('>'+'h'*len(values), *values)
def floating(value): return struct.unpack('>I', struct.pack('>f', value))[0]


def exercise(debug, request, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Pixel probe needs an owned build')
    rom = (directory/'animal-forest-title-preview.z64').read_bytes()
    report = json.loads((directory/'fixes.json').read_text())
    if sha256(rom) != ROM_SHA or report['output_sha256'] != ROM_SHA or report['sources'] != sources():
        raise ValueError('Changed compiled pixel probe source/cartridge')
    files = by_vrom(rom); read = debug.read_memory; assertions = calls = 0
    def write(at, data):
        debug.write_memory(at, data)
        record({'pixel_write': f'{at:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    def check(label, at, expected):
        nonlocal assertions
        observed = read(at, len(expected)); assertions += 1
        record({'pixel_check': label, 'passed': observed == expected, 'address': f'{at:08X}',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected: raise ValueError('Native pixel-editor mismatch: '+label)
    def call(at, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(result); calls += 1; return result['return_value']
    saved = read(SAVE_RAM, SAVE_BYTES)
    size = 0x40000; allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native pixel fixture allocation failed')
    locations = {'editor': allocation+0x10, 'letter': allocation+0x9000, 'notice': allocation+0xD000}
    ovl, submenu, menu = allocation+0x16000, allocation+0x27000, allocation+0x27100
    ed, board, game, graph, scratch, gfx = (allocation+v for v in (0x27200, 0x27300, 0x27400, 0x27500, 0x27900, 0x28000))
    guards = [allocation, allocation+size-16, ovl-16, ovl+0x10720, submenu-16, submenu+0x40,
              menu-16, menu+0x48, ed-16, ed+0x34, board-16, board+192, game-16,
              graph-16, graph+0x300, scratch-16, scratch+64, gfx-16, gfx+0x10000,
              TEST_STACK-0x800, TEST_STACK+0x40]
    loader_at = 0x1060+0x800262D0-0x80025C60; loader = rom[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native cartridge loader')
    loaded = {}
    for name, spec in PARTS.items():
        data = files[spec['vrom']].extract(rom); rel = files[spec['reloc']].extract(rom)
        p = report['parts'][name]; base = locations[name]
        if sha256(data) != p['overlay_sha256'] or sha256(rel) != p['relocation_sha256']:
            raise ValueError('Changed owned pixel-editor image')
        guards += [base-16, base+len(data)+len(rel)]
        expected = relocate_verified_data(Image(spec['ram'], len(data), struct.unpack_from('>5I', rel)), data, rel, base)
        call(0x800262D0, [spec['vrom'], spec['vrom']+len(data), spec['ram'], spec['ram']+len(data),
                         base, base+len(data), len(rel)], (0x800262D0, loader))
        check(name+' complete cartridge load/relocation', base, expected)
        loaded[name] = expected
    for at in guards: write(at, EDGE)
    for at, count in ((ovl, 0x10720), (submenu, 0x40), (menu, 0x48), (ed, 0x34),
                      (board, 192), (game, 16), (graph, 0x300), (scratch, 64)):
        write(at, bytes(count))
    write(submenu+0x2C, words(ovl)); write(ovl+0x106E0, words(ed, board))
    write(menu+4, words(1)); write(menu+0x38, words(0, 0, board+0x3C))
    write(board, b'\1'); write(board+0x3C, b'A'*40+b' '*56); write(board+6, bytes([40]))
    base = locations['editor']; ram = PARTS['editor']['ram']
    # Prefix proof excludes the mutable editor/grid contexts and static key data.
    prefix_proof = (base, loaded['editor'][:0x33C0])
    suffix_start = report['parts']['editor']['previous_bytes']
    suffix_proof = (base+suffix_start, loaded['editor'][suffix_start:])
    call(base+24940, [submenu, menu], prefix_proof if 24940 < 0x33C0 else (base+23168, loaded['editor'][23168:27776]))
    check('native initialization retains body capacity', ed+0x16, half(0, 16, 6, 40))
    def position(index):
        call(base+0x80885AEC-ram, [ed, scratch, scratch+2, index], prefix_proof)
        return read(scratch, 4)
    if position(17) != half(17, 0): raise ValueError('Native editing still wraps after sixteen bytes')
    if position(32) != half(0, 1): raise ValueError('Native editing does not wrap at measured width')
    for length in (31, 95, 96):
        write(board+0x3C, b'A'*length+b' '*(96-length))
        write(ed+0x16, half(length, 16, 6, length)); write(ed+0x13, b'A\0\0')
        call(base+0x80885DD4-ram, [ed], prefix_proof)
        expected = min(length+1, 96)
        check('native insert respects ninety-six saved bytes', ed+0x16, half(expected, 16, 6, expected))
        check('native insert retains adjacent footer storage', board+0x9C, bytes(16))
    text = b'AAAA\xcd'+b'i'*12+b'\xcdAAAA'
    write(board+0x3C, text.ljust(96, b' ')); write(board+6, bytes([len(text)]))
    write(ed+0x16, half(2, 16, 6, len(text))); write(ed+0x20, half(2, 0)); write(ed+0x15, b'\0')
    call(base+0x80885FCC-ram, [ed], prefix_proof)
    widths = read(0x80106AF4, 256); pixel = 2*(12-widths[ord('A')]); narrow = 12-widths[ord('i')]
    nearest = min(range(13), key=lambda n: abs(n*narrow-pixel))
    check('native vertical navigation follows English pixel position', ed+0x16, half(5+nearest))
    # Native body edge selects the header, then the grid refreshes ownership.
    write(ed+0x16, half(0)); write(ed+0x20, half(0, 0)); write(ed+0x11, b'\3'); write(ed+0x15, b'\0')
    call(base+0x80886674-ram, [submenu, menu], prefix_proof)
    check('native letter dispatcher selects header', board, b'\0')
    check('header retains native pointer and capacity', ed+0x18, half(10, 1, 0))
    grid = base+28608
    call(base+report['parts']['editor']['symbols']['af_pixel_grid_input'], [submenu], suffix_proof)
    check('grid accepts native header switch', grid+24, words(board+0x32))
    check('grid reports no field ownership error', grid+32, words(0))
    # Real font calls from both draft body entry points, into isolated lists.
    write(game, words(graph)); write(graph+0x298, words(gfx, gfx+0xF000))
    write(board+6, bytes([len(text)])); write(scratch, words(floating(64), 0, 0, 0x1E0000FF))
    letter = locations['letter']; lram = PARTS['letter']['ram']
    call(letter+0x80889A9C-lram, [submenu, menu, game, floating(64), scratch, scratch+4, scratch+8, scratch+12],
         (letter, loaded['letter'][:0x1910]))
    check('mail edit body advances six lines', scratch, words(floating(160)))
    end = int.from_bytes(read(graph+0x298, 4), 'big')
    if not gfx < end < gfx+0xE000: raise ValueError('Mail edit draw escaped the owned graphics buffer')
    write(graph+0x298, words(gfx, gfx+0xF000))
    notice = locations['notice']; nram = PARTS['notice']['ram']
    call(notice+0x8089542C-nram, [menu, game, board+0x3C, len(text), floating(63), floating(63), scratch+4, scratch+8],
         (notice, loaded['notice'][:0x19C0]))
    end = int.from_bytes(read(graph+0x298, 4), 'big')
    if not gfx < end < gfx+0xE000: raise ValueError('Notice edit draw escaped the owned graphics buffer')
    check('live save remains untouched', SAVE_RAM, saved)
    for at in guards: check('owned RAM/stack guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'native_pixel_editor_calls': calls, 'assertions': assertions, 'save_unchanged': True,
            'code_uploaded': False, 'fixture_released': True, 'requires_checkpoint_restore': True,
            'hardware_acceptance': False}
