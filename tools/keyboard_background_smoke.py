"""One native keyboard draw with cartridge-loaded code and bounded display lists."""
import json
import struct

from aflib import by_vrom, sha256
from birthday_draw_scenario import CALLBACK
from catalogue_names import Image
from flash_mail import SAVE_RAM, SAVE_BYTES
from keyboard_background_fix import ROOT, SPEC, source_hashes
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

ROM_SHA = '63794bd31fe5c7c9ae786b15a41d6a80c2390c890b2edd963ace9a9e5edb8d37'
EDGE = b'KBGC'*4
def words(*values): return struct.pack('>'+'I'*len(values), *values)


def rectangles(data):
    result = []
    for at in range(0, len(data)-23, 8):
        a, b, e, st, f, delta = struct.unpack_from('>6I', data, at)
        if a >> 24 != 0xE4: continue
        if e != 0xE1000000 or f != 0xF1000000: raise ValueError('Incomplete RDP rectangle')
        result.append({'bounds': [((b>>12)&4095)//4, (b&4095)//4, ((a>>12)&4095)//4, (a&4095)//4],
                       'st': list(struct.unpack('>2h', words(st))),
                       'delta': list(struct.unpack('>2h', words(delta)))})
    return result


def exercise(debug, request, record):
    directory = (ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Keyboard probe needs an owned build')
    rom = (directory/'animal-forest-title-preview.z64').read_bytes()
    report = json.loads((directory/'fixes.json').read_text())
    followup = request.get('rc1_followup', False)
    expected_sha, expected_sources = ROM_SHA, source_hashes()
    if followup:
        from keyboard_rc1_fix import source_hashes as rc1_sources
        expected_sha = '7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb'
        expected_sources = rc1_sources()
    if sha256(rom) != expected_sha or report['output_sha256'] != expected_sha or report['sources'] != expected_sources:
        raise ValueError('Changed compiled background source/cartridge')
    files = by_vrom(rom); read = debug.read_memory; assertions = calls = 0
    def write(at, data):
        debug.write_memory(at, data); record({'background_write': f'{at:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    def check(label, at, expected):
        nonlocal assertions
        observed = read(at, len(expected)); assertions += 1
        record({'background_check': label, 'passed': observed == expected, 'address': f'{at:08X}',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected: raise ValueError('Native background mismatch: '+label)
    def call(at, args=(), proof=None):
        nonlocal calls
        result = debug.call(f'{at:08X}', list(args), verified_code=proof); record(result); calls += 1
        return result['return_value']
    saved = read(SAVE_RAM, SAVE_BYTES); size = 0x50000; allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native keyboard fixture allocation failed')
    # The parent owns 67376 BSS bytes as well as its 12016-byte file image.
    base, parent, ovl = allocation+0x10, allocation+0xA000, allocation+0x20000
    submenu, menu, ed, text, game, graph, gfx = (allocation+v for v in (0x32000,0x32100,0x32200,0x32300,0x32400,0x32500,0x38000))
    guards = [allocation+size-16, ovl-16, ovl+0x10720, submenu-16, submenu+0x40,
        menu-16, menu+0x48, ed-16, ed+0x34, text-16, text+64, game-16, game+16,
        graph-16, graph+0x300, gfx-16, gfx+0x10000, TEST_STACK-0x800, TEST_STACK+0x40]
    loader_at = 0x1060+0x800262D0-0x80025C60; loader = rom[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Changed native cartridge loader')
    loaded = {}
    for name, vrom, reloc, ram, destination in (
        ('editor', SPEC['new_vrom'], SPEC['new_reloc'], SPEC['ram'], base),
        ('parent', 0x7749C0, 0x7778B0, 0x8085BAC0, parent)):
        data, rel = files[vrom].extract(rom), files[reloc].extract(rom)
        sections = struct.unpack_from('>5I', rel); resident = sum(sections[:4])
        expected = relocate_verified_data(Image(ram, resident, sections), data, rel, destination)
        if destination+resident+len(rel) >= (parent-16 if name == 'editor' else ovl-16):
            raise ValueError('Keyboard native fixture ranges overlap')
        guards += [destination-16, destination+resident+len(rel)]
        call(0x800262D0, [vrom, vrom+len(data), ram, ram+resident, destination, destination+resident, len(rel)],
             (0x800262D0, loader))
        check(name+' complete cartridge load', destination, expected); loaded[name] = expected
    if loaded['parent'][0x218:0x248] != CALLBACK: raise ValueError('Changed native matrix callback')
    for at in guards: write(at, EDGE)
    for at, count in ((ovl,0x10720),(submenu,0x40),(menu,0x48),(ed,0x34),(text,64),(game,16),(graph,0x300)):
        write(at, bytes(count))
    write(submenu+0x2C, words(ovl)); write(ovl+0x106E0, words(ed)); write(ovl+0x106B4, words(parent+0x218))
    write(game, words(graph)); write(menu+0x28, words(text)); write(menu+0x38, words(3))
    write(ed+0x18, struct.pack('>2h', 6, 1)); write(ed+0x24, words(text))
    context = base+28608
    write(context, bytes([0,0,1])+bytes(9)+words(submenu,menu,ed,text,0,0))
    original_ed = read(ed,0x34); original_ovl = read(ovl,0x10720)
    write(graph+0x298, words(gfx, gfx+0xF000))
    start = report['editor']['previous_resident_bytes']
    call(base+report['editor']['symbols']['af_bg_editor_draw'], [submenu,menu,game], (base+start, loaded['editor'][start:]))
    front, back = struct.unpack('>2I', read(graph+0x298,8))
    if not gfx < front < back <= gfx+0xF000: raise ValueError('Keyboard display lists escape owned storage')
    commands = read(gfx, front-gfx); drawn = rectangles(commands)
    # Keep the actual emitted data even if a later verification assertion fails.
    (directory/'native-background-commands.bin').write_bytes(commands)
    expected = [([42,170,160,227],[0,0],[555,575]), ([160,113,278,170],[2048,1024],[-555,-575]),
                ([160,170,278,227],[2048,0],[-555,575]), ([42,113,160,170],[0,0],[555,575])]
    if followup:
        expected[1] = ([160,111,278,168],[2048,1024],[-555,-575])
        expected[2] = ([160,168,278,225],[2048,1024],[-555,-575])
    if len(drawn) != 44 or drawn[:4] != [dict(bounds=b,st=s,delta=d) for b,s,d in expected]:
        raise ValueError('GC frame bounds, clamped directions, or key count changed')
    for i, rect in enumerate(drawn[4:]):
        x=60+16*(i%10)+(0,3,7,10)[i//10]; y=133+16*(i//10)
        if rect != dict(bounds=[x,y,x+16,y+16],st=[0,0],delta=[2048,2048]):
            raise ValueError('Native GC key placement or UV changed')
    rows = list(struct.iter_unpack('>2I',commands))
    textures = [b for a,b in rows if a >> 24 == 0xFD]
    for symbol in ('af_bg_frame_b','af_bg_frame_a'):
        if textures.count(base+report['editor']['symbols'][symbol]) != 1:
            raise ValueError('Keyboard does not load the complete donor frame')
    if any(a >> 24 == 0xF6 for a,_ in rows): raise ValueError('Beige fill rectangle remains active')
    # GC stores its material in cycle zero only. Native macros repeat the same
    # equation in both RDP cycles, so the complete packed words differ.
    if (0xFC30FE61,0x55FEF379) not in rows or (0xFA0000FF,0xE1CDE1FF) not in rows or (0xFB000000,0xA05AF5FF) not in rows:
        raise ValueError('GC frame combiner or colours changed')
    glyphs = sum(a == 0xFD88005F for a,_ in rows)
    if glyphs < 100: raise ValueError('Keyboard lost its keys or control hints')
    record({'native_background_geometry': drawn[:4], 'retained_key_rectangles':40,
            'glyphs':glyphs,'display_list_bytes':len(commands),'back_bytes':gfx+0xF000-back})
    check('one complete draw without grid error', context+28, words(1,0))
    check('editor input/capacity retained', ed, original_ed); check('submenu retained', ovl, original_ovl)
    check('live save retained', SAVE_RAM, saved)
    for at in guards: check('owned RAM/stack guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'native_background_calls':calls,'assertions':assertions,'code_uploaded':False,
        'cartridge_loader_and_matrix_callback':True,'save_unchanged':True,'fixture_released':True,
        'requires_checkpoint_restore':True,'hardware_acceptance':False,'ordinary_screen_tested':False}
