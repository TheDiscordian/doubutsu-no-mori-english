"""Real submenu loading and native English glyph drawing in isolated owned RAM.

The fixture supplies submenu state and an asset arena, not a normal gameplay
menu. Original loader, constructor, destructor, controls, DMA, and font code run
unchanged. Complete checkpoint restoration is required after the batch.
"""

import struct
from dataclasses import dataclass
from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_reader_smoke import glyph_advances
from notice_overlay import OWNER_RAM, OWNER_VROM, RAM, RESIDENT, METADATA
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

POSTS, EDGE = 0x80129E0A, b'NBED'*4


@dataclass(frozen=True)
class Image:
    ram: int
    file_bytes: int
    sections: tuple

    @property
    def resident_bytes(self): return self.file_bytes+self.sections[3]


def words(*values): return struct.pack('>'+'I'*len(values), *values)


def floating(value): return struct.unpack('>I', struct.pack('>f', value))[0]


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    proofs = []
    assertions = draws = glyph_count = 0
    treasure = request.get('treasure_only', False)
    seasonal = request.get('seasonal_only', False)
    if type(treasure) is not bool or (treasure and request['report'].get('treasure') is not True):
        raise ValueError('Invalid native treasure reader profile')
    if (type(seasonal) is not bool or (seasonal and request['report'].get('seasonal') is not True)
            or (treasure and seasonal)):
        raise ValueError('Invalid native seasonal reader profile')
    complete = treasure or seasonal

    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'notice_reader_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Native notice reader mismatch: '+label)
        assertions += 1

    def call(at, args=(), expected=None, proof=None):
        if proof is None:
            proof = next(((base, data) for base, data in proofs if base <= at < base+len(data)), None)
        result = debug.call(f'{at:08X}', args, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Notice call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    for at, value in request['guards'].items():
        check('unchanged native helper', int(at, 16), bytes.fromhex(value))
    data, reloc, owner, owner_reloc, assets = (bytes.fromhex(request[k]) for k in
        ('data', 'relocation', 'owner', 'owner_relocation', 'assets'))
    owner_spec = Image(OWNER_RAM, len(owner), struct.unpack_from('>5I', owner_reloc))
    notice_spec = Image(RAM, len(data), struct.unpack_from('>5I', reloc))
    saved = read(SAVE_RAM, SAVE_BYTES)
    saved_globals = {at: read(at, size) for at, size in
                     ((0x801458D0, 4), (0x80123F0C, 4), (0x8013A680, 0x6000),
                      (0x80106AF4, 256), (0x80104F94, 4))}
    game_live = int.from_bytes(read(0x8010EF90, 4), 'big')
    if not MODULE_RAM+RESERVATION <= game_live <= 0x80400000-0x100:
        raise ValueError('Invalid native game input owner')
    saved_globals[game_live+0x14] = read(game_live+0x14, 0x18)
    # The native owner's first 64 KiB of BSS is its asset storage. Use that
    # existing buffer instead of allocating an unnecessary second asset copy.
    # Separate owner and reader/graphics allocations avoid demanding a single
    # large contiguous block in the title checkpoint's ordinary heap.
    call(0x8009C0C0, [0x8019B000, 0x8019B004, 0x8019B008])
    record({'notice_heap_before_fixture': list(struct.unpack('>3I', read(0x8019B000, 12)))})
    allocations = []
    auxiliary_size = 0xF000 if seasonal else 0xD000 if treasure else 0xC000
    for size in (0x13B00, auxiliary_size):
        pointer = call(0x8009BFC0, [size])
        if pointer & 15 or not MODULE_RAM+RESERVATION <= pointer <= 0x80400000-size:
            raise ValueError('Notice fixture allocation failed')
        allocations.append(pointer)
    allocation, auxiliary = allocations
    owner_at, scratch, submenu = (allocation+offset for offset in (0x10, 0x13640, 0x13900))
    state_owner = owner_at+len(owner)
    asset_at = state_owner+16
    base = auxiliary+0x10
    delta = 0x2800 if seasonal else 0x800 if treasure else 0
    game, metrics, end, graph, arena = (
        auxiliary+offset+delta for offset in (0x3800, 0x3920, 0x3940, 0x3A00, 0x3E00))
    arena_end = auxiliary+auxiliary_size-16
    if (owner_at+owner_spec.resident_bytes > scratch-16 or scratch+len(owner_reloc) > submenu-16
            or submenu+0xF0 > allocation+0x13B00-16 or base+len(data) > game-16
            or asset_at+len(assets) > state_owner+0x10000-16 or game+0x100 > metrics-16
            or metrics+12 > end-16 or end+8 > graph-16 or graph+0x300 > arena-16):
        raise ValueError('Notice fixture ranges overlap')
    edges = (allocation, scratch-16, scratch+len(owner_reloc), submenu-16,
             allocation+0x13B00-16, base-16,
             base+len(data), asset_at-16, asset_at+len(assets), game-16, game+0x100,
             metrics+12, end+8, graph-16, graph+0x300, arena-16, arena_end,
             TEST_STACK-0x1000, TEST_STACK+0x30)
    # Owner BSS is zeroed by its actual loader; write interior guards afterwards.
    for at in edges:
        if not owner_at <= at < owner_at+owner_spec.resident_bytes: write(at, EDGE)
    loaded_owner = relocate_verified_data(owner_spec, owner, owner_reloc, owner_at)
    call(0x800262D0, [OWNER_VROM, OWNER_VROM+len(owner), OWNER_RAM,
                     OWNER_RAM+owner_spec.resident_bytes, owner_at, scratch, len(owner_reloc)],
         proof=(0x800262D0, bytes.fromhex(request['loader'])))
    check('complete cartridge owner and zeroed BSS', owner_at, loaded_owner)
    proofs.append((owner_at, loaded_owner[:owner_spec.sections[0]]))
    for at in edges:
        if owner_at <= at < owner_at+owner_spec.resident_bytes: write(at, EDGE)
    menu, state = state_owner+0x10238, base+0x1A00
    metadata = owner_at+METADATA
    loader = owner_at+0x8085D128-OWNER_RAM
    write(submenu, bytes(0xF0))
    write(submenu+0x24, words(base, base, state_owner))
    write(state_owner+0x10000, words(asset_at))
    write(state_owner+0x106B0, words(owner_at+0x8085D4D4-OWNER_RAM))
    write(state_owner+0x106CC, words(owner_at+0x8085D43C-OWNER_RAM))
    rtc = bytes.fromhex('00120e04040907d1')
    first = request['cases'][::2][:4]
    posts = b''.join(bytes.fromhex(case['wire'])+rtc for case in first)
    posts += bytes.fromhex(request['empty_post'])*11
    write(POSTS, posts)
    write(base, b'!'*len(data))
    write(asset_at, b'!'*len(assets))
    call(0x8009C0C0, [metrics, metrics+4, metrics+8])
    heap = read(metrics, 12)
    call(loader, [submenu, metadata])
    loaded = relocate_verified_data(notice_spec, data, reloc, base)
    symbols = request['report']['symbols']
    code_end = request['report']['code_end']
    proofs += [(base, loaded[:6512]), (base+RESIDENT, loaded[RESIDENT:code_end])]
    check('native reader code retained after actual owner construction', base, loaded[:6512])
    check('appended relocated English reader code', base+RESIDENT, loaded[RESIDENT:code_end])
    check('native linked allocation advances by complete aligned size', submenu+0x28,
          words(base+((len(data)+63) & ~63)))
    check('native owner installs relocated callbacks and loaded flag', metadata+16,
          words(base+symbols['af_notice_construct'], base+0x80895B9C-RAM, base+0x80895A30-RAM, 1))
    check('native owner records one live notice overlay', state_owner+0x10064, words(1, metadata))
    check('constructor loads complete original board assets', asset_at, assets)
    check('constructor advances asset cursor', state_owner+0x10000, words(asset_at+len(assets)))
    check('constructor assigns original notice state', state_owner+0x1070C, words(state))
    check('constructor retains post count and last-post selection', state+3, bytes((4, 3, 3)))
    cache_at = base+symbols['af_notice_cache']
    check('constructor clears both full-text caches', cache_at, bytes(2432))
    call(0x8009C0C0, [metrics, metrics+4, metrics+8])
    check('owner releases temporary relocation memory', metrics, heap)
    write(game, words(graph)+bytes(0xFC))
    write(graph, bytes(0x300))
    widths = [12-cut for cut in saved_globals[0x80106AF4]]

    def verify_draws(lines):
        nonlocal draws, glyph_count
        count = sum(len(glyph_advances(text, widths)) for text, _, _, _ in lines)
        front, back = struct.unpack('>2I', read(graph+0x298, 8))
        if (front-arena != 24*len(lines)+72*count or arena_end-back != 64*count
                or not arena <= front <= back <= arena_end):
            raise ValueError(f'Notice graphics allocation differs: {front-arena}, {arena_end-back}, glyphs={count}')
        vertices = read(back, count*64)
        index = 0
        for text, x, y, scale in lines:
            for advance in glyph_advances(text, widths):
                left, top = int((x-160)*16), int((120-y)*16)
                right, bottom = left+int(advance*16*scale), top-int(256*scale)
                for corner, expected in enumerate(((left, top, 0), (left, bottom, 0),
                                                    (right, bottom, 0), (right, top, 0))):
                    actual = struct.unpack_from('>3h', vertices, (count-index-1)*64+corner*16)
                    if actual != expected:
                        raise ValueError(f'Notice glyph {index} corner {corner}: {actual}, expected {expected}')
                x += advance*scale
                index += 1
        record({'notice_native_draw': True, 'glyphs_verified': count,
                'vertex_positions_verified': count*4,
                'lines': [{'text': text.hex(), 'x': x, 'y': y, 'scale': scale}
                          for text, x, y, scale in lines]})
        draws += 1
        glyph_count += count

    def arena_reset():
        for offset in (0x290, 0x2B0):
            write(graph+offset, words(arena_end-arena, arena, arena, arena_end))

    def draw_body(slot, body, status=2, page=0):
        source = POSTS+slot*104
        if complete:
            from notice_native_layout import rows
            spans = rows(body, widths)
            all_lines = [text for _, text, _ in spans]
        else:
            all_lines = body.rstrip(b'\xcd').split(b'\xcd') if body else []
        if any(sum(glyph_advances(line, widths)) > 192 for line in all_lines):
            raise ValueError('Selected notice fixture requires independent soft-wrap modelling')
        lines = all_lines[page*6:page*6+6]
        total = max(1, (len(all_lines)+5)//6)
        arena_reset()
        write(menu+4, words(1))
        call(base+symbols['af_notice_draw_body'], [menu, game, source, 96,
             floating(63), floating(63), end, end+4])
        caches = [(cache_at+i*1216, read(cache_at+i*1216, 1216)) for i in range(2)]
        matches = [(at, value) for at, value in caches
                   if int.from_bytes(value[:4], 'big') == source and value[12:108] == read(source, 96)]
        if len(matches) != 1: raise ValueError('Missing or duplicate notice cache owner')
        at, value = matches[0]
        check('cache retains complete source and body', at,
              words(source, status, page)+read(source, 96)+words(len(body))+body)
        layout = bytearray(words(total, len(lines)))
        if complete:
            for offset, line, width in spans[page*6:page*6+6]: layout += words(offset, len(line), width)
        else:
            offset = sum(len(line)+1 for line in all_lines[:page*6])
            for line in lines:
                layout += words(offset, len(line), sum(glyph_advances(line, widths)))
                offset += len(line)+1
        check('complete six-line page layout', at+1136, bytes(layout).ljust(80, b'\0'))
        drawing = [(line, 63, 63+row*16, 1) for row, line in enumerate(lines) if line]
        if total > 1: drawing.append((f'L/R: page {page+1}/{total}'.encode(), 63, 163, 0.75))
        verify_draws(drawing)
        expected_end = (63+(sum(glyph_advances(lines[-1], widths)) if lines else 0)-160,
                        120-63-(len(lines)-1)*16 if lines else 120-63)
        check('native body end coordinates', end, struct.pack('>2f', *expected_end))
        return at

    if complete:
        call(0x8007D91C, [0], 0)
        call(0x8007D90C, expected=0)
    for case in request['cases'][request.get('skip_initial', 0):]:
        wire, body = bytes.fromhex(case['wire']), bytes.fromhex(case['body'])
        write(POSTS, wire+rtc)
        draw_body(0, body)
        if complete:
            from notice_native_layout import rows
            pages = max(1, (len(rows(body, widths))+5)//6)
            for page in range(1, pages):
                write(state, bytes((0, 8, 0, 4, 0, 0, 0, 0)))
                write(game_live+0x20, struct.pack('>H', 0x10))
                call(base+symbols['af_notice_read_control'], [submenu, menu, state])
                draw_body(0, body, page=page)
            for _ in range(pages-1):
                write(game_live+0x20, struct.pack('>H', 0x20))
                call(base+symbols['af_notice_read_control'], [submenu, menu, state])
        check('reader leaves compact post and timestamp unchanged', POSTS, wire+rtc)
        call(0x8009C0C0, [metrics, metrics+4, metrics+8])
        check('cache miss releases full decoder workspace', metrics, heap)
        record({('notice_seasonal_body' if seasonal else 'notice_treasure_body' if treasure else 'notice_initial_body'): case['template'],
                'capital': case['capital'], **({'item': case['item']} if treasure else {}), 'passed': True})
    if not complete and not request.get('edges_only'):
        # Two cached posts must survive alternating animation draws and reopening.
        for slot, case in enumerate(first[:2]): write(POSTS+slot*104, bytes.fromhex(case['wire'])+rtc)
        for slot in (0, 1, 0, 1): draw_body(slot, bytes.fromhex(first[slot]['body']))
        call(loader, [submenu, metadata])
        check('reopening clears both caches', cache_at, bytes(2432))
        check('reopening does not duplicate owner allocation', submenu+0x28, words(base+((len(data)+63) & ~63)))
        check('reopening retains single ownership record', state_owner+0x10064, words(1, metadata))
        check('reopening does not duplicate asset allocation', state_owner+0x10000, words(asset_at+len(assets)))
        # Corruption must display a complete error and never alter the saved bytes.
        bad = b'\x7fBN\x02'+bytes(92)
        write(POSTS, bad+rtc)
        draw_body(0, b'Unable to read this post.\xcdClose and reopen to retry.', status=3)
        check('malformed record retained', POSTS, bad+rtc)
        write(POSTS, bytes.fromhex(first[0]['wire'])+rtc)
        call(loader, [submenu, metadata])
        draw_body(0, bytes.fromhex(first[0]['body']))
    if not complete:
        # Retained initial-only edge batch; do not replay it for treasure bodies.
        # Native controller helpers read the paused game's input. The original
        # setter enables ordinary input in this isolated title fixture.
        call(0x8007D91C, [0], 0)
        call(0x8007D90C, expected=0)
        manual = b'A\xcd'*7
        write(POSTS, manual.ljust(96, b' ')+rtc)
        draw_body(0, manual, status=1)
        for buttons, page in ((0x10, 1), (0x10, 1), (0x20, 0), (0x30, 0)):
            write(state, bytes((0, 8, 0, 4, 0, 0, 0, 0)))
            write(game_live+0x20, struct.pack('>H', buttons))
            call(0x80078DF4, expected=buttons)
            call(base+symbols['af_notice_read_control'], [submenu, menu, state])
            draw_body(0, manual, status=1, page=page)
            record({'notice_native_page_control': buttons, 'page': page, 'passed': True})
        for entry in (1, 15):
            arena_reset()
            call(base+symbols['af_notice_draw_entry'], [game, entry, floating(63), floating(46)])
            verify_draws([(f'entry {entry}'.encode(), 63, 46, 0.75)])
        months = ('January February March April May June July August September October November December').split()
        for month, name in enumerate(months, 1):
            timestamp = bytes((0, 12, 14, 31, 0, month, 7, 0xD1))
            write(POSTS+96, timestamp)
            text = f'{name} 31, 2001'.encode()
            arena_reset()
            call(base+symbols['af_notice_draw_date'], [game, POSTS+96, floating(63), floating(46)])
            x = 63+194-sum(glyph_advances(text, widths))*0.75
            verify_draws([(text, x, 46, 0.75)])
    call(base+0x80895B9C-RAM, [submenu])
    check('native destructor releases notice ownership', state_owner+0x1070C, words(0))
    check('owner code retained', owner_at, loaded_owner[:owner_spec.sections[0]])
    check('native reader code retained', base, loaded[:6512])
    check('English reader code retained', base+RESIDENT, loaded[RESIDENT:code_end])
    check('board assets retained', asset_at, assets)
    call(0x8009C0C0, [metrics, metrics+4, metrics+8])
    check('complete batch retains heap accounting', metrics, heap)
    for at in edges: check('fixture and stack guard', at, EDGE)
    check('resident guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    write(SAVE_RAM, saved)
    check('complete saved payload restored', SAVE_RAM, saved)
    for at, value in saved_globals.items():
        write(at, value)
        check('native global or input restored', at, value)
    for pointer in reversed(allocations): call(0x8009C040, [pointer])
    return {'notice_initial_bodies': 0 if complete else 8-request.get('skip_initial', 0),
            **({'notice_treasure_bodies': len(request['cases'])-request.get('skip_initial', 0)} if treasure else {}),
            **({'notice_seasonal_bodies': len(request['cases'])-request.get('skip_initial', 0)} if seasonal else {}),
            'notice_native_draws': draws,
            'notice_glyphs_verified': glyph_count, 'notice_reader_assertions': assertions,
            'actual_owner_loader': True, 'normal_submenu_initialization': False,
            'debugger_uploaded_reader_bytes': 0, 'requires_checkpoint_restore': True,
            'save_io_tested': False, 'hardware_verified': False}
