"""Current-cartridge museum and credits budget check in isolated native memory."""
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from catalogue_names import Image
import credits_strings as c
from credits_smoke import CLIP, EVENT, alpha, words
from flash_mail import SAVE_RAM, SAVE_BYTES
from letter_ui_fix import PARTS
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, GUARD_ADDRESS, GUARD_WORD
from v2_performance_fix import ROOT, credits_rows

ROM_SHA = '08aa1c4418848138803059a68de667f473f9da490d7c0866ee501c58b8d0896b'
EDGE = b'V208'*4
CAPACITY = 0x3800


def floating(value):
    return struct.unpack('>I', struct.pack('>f', value))[0]


def f32(value):
    return struct.unpack('>f', struct.pack('>f', value))[0]


def exercise(debug, request, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Performance probe must use an isolated current build')
    rom = (directory/'Animal Forest English V2.z64').read_bytes()
    report = json.loads((directory/'build.json').read_text())
    if sha256(rom) != ROM_SHA or report['output_sha256'] != ROM_SHA:
        raise ValueError('Performance probe requires the checked current cartridge')
    files = by_vrom(rom); read = debug.read_memory
    assertions = calls = 0
    def write(at, value):
        debug.write_memory(at, value)
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected)); assertions += 1
        record({'performance_check': label, 'passed': actual == expected,
                'expected_sha256': sha256(expected), 'actual_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Native performance mismatch: '+label)
    def call(at, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof)
        record(result); calls += 1
        return result['return_value']
    saved, clip, event = read(SAVE_RAM, SAVE_BYTES), read(CLIP, 4), read(EVENT, 44)
    # Only cartridge-loaded executable owners need ordinary heap space.
    # Drawing data uses the existing upper diagnostic region, outside the
    # production font/title reservations and below the fault framebuffer.
    size = 0x4000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Performance fixture allocation failed')
    base, address = allocation+0x10, allocation+0x1800
    diagnostic, diagnostic_size = 0x80510000, 0x10000
    preserved_diagnostic = read(diagnostic, diagnostic_size)
    scratch, game, graph = diagnostic+0x10, diagnostic+0x100, diagnostic+0x200
    font, vertex_start, vertex_end = diagnostic+0x1000, diagnostic+0x7100, diagnostic+diagnostic_size-16
    guards = (allocation, allocation+size-16, scratch-16, scratch+128, game-16, game+16, graph-16,
              graph+0x310, font-16, font+0x6000, vertex_end)
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = rom[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native overlay loader')
    def load(vrom, rel_vrom, ram, location):
        data, rel = files[vrom].extract(rom), files[rel_vrom].extract(rom)
        sections = struct.unpack_from('>5I', rel)
        resident = len(data)+sections[3]
        expected = relocate_verified_data(Image(ram, resident, sections), data, rel, location)
        call(0x800262D0, [vrom, vrom+len(data), ram, ram+resident,
                         location, location+resident, len(rel)], (0x800262D0, loader))
        check('complete cartridge owner and relocation', location, expected)
        return expected, (location, expected[:sections[0]])
    loaded, proof = load(c.VROM, c.RELOCATION, c.RAM, base)
    spec = PARTS['address']
    address_loaded, address_proof = load(spec['new_vrom'], spec['new_reloc'], spec['ram'], address)
    for at in guards: write(at, EDGE)
    write(game, words(graph)); write(graph, bytes(0x310))
    # Canonical museum, complete villager lookup, player, and unknown identity.
    cases = ((2, 0, b'\x7B\xCE\xCB\x03  ', b'Museum'),
             (1, 132, b'\x7B\xCE\xCB\x03  ', b'Limberg '),
             (0, 0, b'Player', b'Player'), (7, 0, b'Custom', b'Custom'))
    for kind, index, name, expected in cases:
        identity = bytearray(18); identity[:6] = name; identity[12] = index; identity[16] = kind
        write(scratch, identity); write(scratch+32, b'?'*8)
        length = call(address+report['address']['symbols']['af_ui_address_name'],
                      [scratch+32, scratch], address_proof)
        if length != len(expected): raise ValueError('Recipient draw length differs')
        check('museum/villager/player/unknown display', scratch+32, expected)
        check('recipient saved identity retained', scratch, identity)
    write(CLIP, words(base+c.FILE_BYTES))
    fixture = bytearray(event); struct.pack_into('>I', fixture, 0, 1)
    fixture[4:6] = bytes((0x21, 10)); struct.pack_into('>H', fixture, 14, 0x4000)
    write(EVENT, fixture)
    if call(0x8008033C, [0x21, 10]) != EVENT+12:
        raise ValueError('Credits event fixture not selected')
    rows = credits_rows(rom); buffer = base+c.BUFFER-c.RAM
    code = files[CODE_VROM].extract(rom)
    font_proof = (0x80090E1C, code[0x80090E1C-CODE_RAM:0x80090E98-CODE_RAM])
    def reset_graph():
        write(graph+0x290, words(vertex_end-vertex_start, vertex_start, vertex_start, vertex_end))
        # Reserve more backing memory for the rejected baseline, but give the
        # native arena its real 0x3800-byte capacity. No list is submitted.
        write(graph+0x2B0, words(CAPACITY, font, font, font+CAPACITY))
    def drawing():
        front = int.from_bytes(read(graph+0x2B8, 4), 'big')
        back = int.from_bytes(read(graph+0x29C, 4), 'big')
        if not font <= front <= font+0x6000 or not vertex_start <= back <= vertex_end:
            raise ValueError('Graphics escaped the larger isolated backing allocation')
        commands = read(font, front-font)
        all_vertices = read(back, vertex_end-back)
        quads = []
        for first, second in struct.iter_unpack('>II', commands):
            if first >> 24 == 1:
                pointer = 0x80000000 | (second & 0x1FFFFFFF)
                if not back <= pointer <= vertex_end-64:
                    raise ValueError('Unexpected font vertex pointer')
                quads.append(all_vertices[pointer-back:pointer-back+64])
        colours = [b for a, b in struct.iter_unpack('>II', commands) if a == 0xFA000000]
        exhausted = call(0x800D1520, [graph+0x2B0])
        return {'commands': len(commands)//8, 'bytes': len(commands), 'exhausted': exhausted,
                'quads': quads, 'colours': colours}
    def load_page(page):
        start, end = c.PAGES[page:page+2]
        write(buffer, b'G'*256)
        call(base+0x80AA3D08-c.RAM, [page], proof)
        expected = b''.join(rows[min(start+i,109)].ljust(25,b' ') for i in range(10))+b'G'*6
        check('complete stored credit rows and bounds', buffer, expected)
        return start, end, expected
    # Execute the former untrimmed calls once on the current native font. This
    # reproduces actual arena exhaustion without booting an old build or
    # uploading executable bytes to the emulator.
    start, end, expected = load_page(2); reset_graph()
    call(0x80090F10, [graph, 1])
    retained = []
    for i, row in enumerate(range(start,end)):
        scale = f32(.9)
        if i == 0 or row in c.ROLE_LINES: scale = f32(scale*f32(.85))
        call(0x80090E1C, [game, buffer+i*25, 25, floating(150), floating(30+(10+start-end)*10+i*18),
                          255,255,255,255,0,1,1,floating(scale),floating(scale),1], font_proof)
    call(0x8009104C, [graph, 1]); baseline = drawing()
    if not baseline['exhausted'] or baseline['bytes'] <= CAPACITY:
        raise ValueError('Untrimmed native credits did not reproduce the budget failure')
    if len(baseline['quads']) != 25*(end-start):
        raise ValueError('Untrimmed credits glyph count differs')
    for i, row in enumerate(range(start,end)):
        retained.extend(baseline['quads'][i*25:i*25+len(rows[row].rstrip(b' '))])
    record({'untrimmed_credits': {k:v for k,v in baseline.items() if k not in ('quads','colours')},
            'capacity_bytes': CAPACITY, 'gpu_submission': False})
    results = []
    for page, timer in [(i,100) for i in range(16)]+[(2,t) for t in (19,20,21,59,60,183,184,222,223,224)]:
        start, end, expected = load_page(page); reset_graph()
        call(base+0x80AA3D94-c.RAM, [game,timer,page], proof)
        measured = drawing()
        lengths = [len(row.rstrip(b' ')) for row in rows[start:end]]
        if measured['exhausted'] or measured['bytes']+8 > CAPACITY:
            raise ValueError('Corrected credits still exhaust the actual font arena')
        if len(measured['quads']) != sum(lengths):
            raise ValueError('Corrected credits lost a non-padding character')
        if measured['colours'] != [0xFFFFFF00|alpha(timer)]*sum(bool(n) for n in lengths):
            raise ValueError('Corrected credits change row colour or fading')
        if page == 2 and measured['quads'] != retained:
            raise ValueError('Corrected credits move existing glyph vertices')
        check('draw retains complete rows', buffer, expected)
        item = {'page':page,'timer':timer,'commands':measured['commands'],
                'glyphs':len(measured['quads']),'headroom_bytes':CAPACITY-measured['bytes']-8}
        record({'corrected_credits':item}); results.append(item)
    check('original credits state and executable preserved', base, loaded[:c.FILE_BYTES+c.OLD_BSS])
    check('address executable preserved', address, address_loaded)
    write(EVENT, event); write(CLIP, clip)
    check('saved data restored', SAVE_RAM, saved)
    for at in guards: check('isolated memory guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    write(diagnostic, preserved_diagnostic)
    check('diagnostic region restored', diagnostic, preserved_diagnostic)
    call(0x8009C040, [allocation])
    return {'performance_calls':calls, 'assertions':assertions, 'pages':16, 'draws':len(results),
            'untrimmed_commands':baseline['commands'], 'maximum_corrected_commands':max(r['commands'] for r in results),
            'font_capacity_commands':CAPACITY//8, 'minimum_headroom_bytes':min(r['headroom_bytes'] for r in results),
            'museum_display_passed':True, 'retained_geometry_passed':True, 'save_unchanged':True,
            'normal_hardware_performance':False, 'requires_checkpoint_restore':True}
