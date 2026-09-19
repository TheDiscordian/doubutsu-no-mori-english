"""Focused current-ROM execution of museum header editing and reading."""
import json
import struct

from aflib import by_vrom, sha256
from catalogue_names import Image
from flash_mail import SAVE_RAM, SAVE_BYTES
import letter_names as names
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, MODULE_VROM, GUARD_ADDRESS, GUARD_WORD
from v2_museum_header_fix import ROOT, NAME_ENTRY

ROM_SHA = 'a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee'
EDGE = b'MSHD'*4
def words(*values): return struct.pack('>'+'I'*len(values), *values)
def floating(value): return struct.unpack('>I', struct.pack('>f', value))[0]


def exercise(debug, request, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Museum header probe requires an ignored build')
    rom = (directory/'Animal Forest English V2.z64').read_bytes()
    report = json.loads((directory/'build.json').read_text())
    if sha256(rom) != ROM_SHA or report['output_sha256'] != ROM_SHA:
        raise ValueError('Changed museum header test ROM')
    files = by_vrom(rom); read, write = debug.read_memory, debug.write_memory
    assertions = calls = 0
    def check(label, actual, expected):
        nonlocal assertions
        assertions += 1
        record({'museum_header_check': label, 'passed': actual == expected})
        if actual != expected: raise ValueError('Museum header mismatch: '+label)
    def call(at, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        calls += 1; record(result); return result['return_value']
    saved = read(SAVE_RAM, SAVE_BYTES)
    size = 0x16000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not 0x8019C8E0 <= allocation <= 0x80400000-size:
        raise ValueError('Museum header fixture allocation failed')
    base, overlay, submenu = allocation+0x10, allocation+0x4000, allocation+0x14700
    board, menu, scratch = allocation+0x14800, allocation+0x14900, allocation+0x14A00
    diagnostic, diagnostic_size = 0x80510000, 0x10000
    preserved = read(diagnostic, diagnostic_size)
    game, graph, colour = diagnostic+0x100, diagnostic+0x200, diagnostic+0x600
    font, vertex_start, vertex_end = diagnostic+0x1000, diagnostic+0x7100, diagnostic+0xFFF0
    guards = (allocation, allocation+size-16, board-16, board+192, scratch-16,
              scratch+128, font-16, font+0x6000, vertex_end)
    data, rel = (files[v].extract(rom) for v in (names.NEW_VROM, names.NEW_RELOC))
    expected = relocate_verified_data(Image(names.RAM, len(data), struct.unpack_from('>5I', rel)), data, rel, base)
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = rom[loader_at:loader_at+0xF0]
    call(0x800262D0, [names.NEW_VROM, names.NEW_VROM+len(data), names.RAM,
         names.RAM+len(data), base, base+len(data), len(rel)], (0x800262D0, loader))
    check('complete cartridge-loaded board relocation', read(base, len(data)), expected)
    module = files[MODULE_VROM].extract(rom)
    check('cartridge-loaded resident museum adapter', read(MODULE_RAM+0x90, 84), module[0x90:0xE4])
    for at in guards: write(at, EDGE)
    write(submenu, bytes(64)); write(submenu+0x2C, words(overlay))
    write(overlay+0x106E4, words(board)); write(menu, bytes(96))
    write(graph, bytes(0x310)); write(game, words(graph)); write(colour, bytes((70,40,50,255)))
    check('complete resident name reader', read(NAME_ENTRY, 180),
          module[NAME_ENTRY-MODULE_RAM:NAME_ENTRY-MODULE_RAM+180])
    name_table = files[0x2C00000].extract(rom)
    cases = ((2, 0, bytes.fromhex('1907F81105C3'), b'Museum'),
             (0, 0, b'Player', b'Player'), (7, 0, b'Custom', b'Custom'),
             (1, 132, b'Native', name_table[32+132*8:40+132*8].rstrip(b' ')))
    for kind, index, original, english in cases:
        identity = bytearray(18); identity[:6] = original; identity[12] = index; identity[16] = kind
        write(scratch, identity); write(scratch+32, b'?'*10)
        result = call(NAME_ENTRY, [scratch+33, scratch, 6])
        check('reader name and length', (result, read(scratch+33, result)), (len(english), english))
        check('reader retains saved identity', read(scratch, 18), identity)
        check('reader output guards', (read(scratch+32, 1), read(scratch+41, 1)), (b'?', b'?'))
    def drawing(status, recipient_type, name, reader=False):
        state = bytearray(192)
        state[3], state[5], state[0x2F], state[0x18] = 6, 3, 3, recipient_type
        state[8:14] = name; state[0x32:0x3C] = b'To        '
        write(board, state); write(menu+4, words(status))
        write(graph+0x290, words(vertex_end-vertex_start, vertex_start, vertex_start, vertex_end))
        write(graph+0x2B0, words(0x3800, font, font, font+0x3800))
        if reader:
            address = 0x80198960
            check('resident read-mode header entry', read(address, 16),
                  module[address-MODULE_RAM:address-MODULE_RAM+16])
            call(address, [submenu, game, menu, floating(64), floating(36), colour])
        else:
            address = base+names.HEADER-names.RAM
            call(address, [submenu, game, menu, floating(64), floating(36), colour], (base, expected))
        # This letter draw uses the two-dimensional renderer and poly list,
        # unlike the credits' separate font list. It need not allocate vertices.
        front = int.from_bytes(read(graph+0x298, 4), 'big')
        back = int.from_bytes(read(graph+0x29C, 4), 'big')
        record({'museum_header_graph': {'front': f'{front:08X}', 'back': f'{back:08X}',
                                       'start': f'{vertex_start:08X}', 'end': f'{vertex_end:08X}'}})
        if not vertex_start < front <= back <= vertex_end:
            raise ValueError('Museum header draw exceeds the owned graphics arena')
        check('draw retains the entire saved letter and editing state', read(board, 192), state)
        return read(vertex_start, front-vertex_start), read(back, vertex_end-back)
    for status, reader in ((1, False), (0, False), (3, False), (4, False), (1, True)):
        actual = drawing(status, 2, bytes.fromhex('1907F81105C3'), reader)
        reference = drawing(status, 0, b'Museum', reader)
        check('museum renders the complete English header, mode '+str((status, reader)), actual, reference)
    check('live save unchanged', read(SAVE_RAM, SAVE_BYTES), saved)
    for at in guards: check('owned memory guard', read(at, 16), EDGE)
    check('resident guard', read(GUARD_ADDRESS, 16), words(*([GUARD_WORD]*4)))
    write(diagnostic, preserved)
    call(0x8009C040, [allocation])
    return {'native_museum_header_calls': calls, 'assertions': assertions,
            'save_unchanged': True, 'code_uploaded': False, 'requires_checkpoint_restore': True,
            'hardware_acceptance': False}
