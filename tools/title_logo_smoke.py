"""Read-only actual loading, animation-state, and guard checks for the English logo."""
import struct

from aflib import by_vrom, sha256
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from title_overlay import NEW_ACTOR, NEW_RELOC, ASSETS, RAM, validate
from title_start_smoke import locate
from title_memory import BASE, GUARD

PREVIEW_SHA256 = 'a69f8ca9cdde8eece5d85e9b0a97ab70e31ebd58bb8164a16ab84ed29fb440f7'
COMBINED_SHA256 = 'fd5ea14491387de19229847fdd3fbf5dd46dd14c461bb07a2fe6b9d7515682da'


def diagnose(debug):
    """Retain read-only loading evidence even if actor verification cannot start."""
    game = struct.unpack('>I', debug.read_memory(0x8010EF90, 4))[0]
    registers = debug.command('g')
    result = {'title_loading_observation': True, 'game': f'{game:08X}',
              'detected_ram_bytes': int.from_bytes(debug.read_memory(0x80000318, 4), 'big'),
              'metadata': debug.read_memory(0x801021F0, 32).hex(),
              'resident_guard': debug.read_memory(0x8019C8D0, 16).hex(),
              'registers': registers, 'read_only': True}
    for name, address in (('scene_heap', 0x80141FA0), ('main_heap', 0x800419C0)):
        node = struct.unpack('>I', debug.read_memory(address, 4))[0]
        seen, nodes = set(), []
        while node and len(seen) < 256:
            if node in seen or node & 15 or not 0x80000400 <= node <= 0x80400000-16:
                nodes.append({'invalid_link': f'{node:08X}'})
                break
            seen.add(node)
            magic, free, size, following, previous = struct.unpack('>2H3I', debug.read_memory(node, 16))
            nodes.append({'address': f'{node:08X}', 'magic': f'{magic:04X}', 'free': free,
                          'bytes': size, 'next': f'{following:08X}', 'previous': f'{previous:08X}'})
            if magic != 0x7373: break
            node = following
        result[name] = nodes
    if 0x8019C8E0 <= game <= 0x80400000-0x1CA4 and not game & 3:
        graph = struct.unpack('>I', debug.read_memory(game, 4))[0]
        if 0x80000400 <= graph <= 0x80400000-0x308 and not graph & 3:
            result['graphics_arenas'] = debug.read_memory(graph+0x280, 96).hex()
        count, actor = struct.unpack('>2I', debug.read_memory(game+0x1C9C, 8))
        result.update(background_count=count, background_head=f'{actor:08X}', actors=[])
        seen = set()
        while actor and len(seen) < min(count, 64):
            if actor in seen or actor & 3 or not 0x8019C8E0 <= actor <= 0x80400000-0x174:
                result['invalid_actor_link'] = f'{actor:08X}'
                break
            seen.add(actor)
            data = debug.read_memory(actor, 0x174)
            result['actors'].append({'address': f'{actor:08X}', 'header': data[:16].hex(),
                                     'callbacks': data[0x15C:0x16C].hex()})
            actor = struct.unpack_from('>I', data, 0x158)[0]
    return result


def verify(debug, rom, profile):
    if sha256(rom) not in (PREVIEW_SHA256, COMBINED_SHA256):
        raise ValueError('Title animation observation requires the exact English logo preview')
    files = by_vrom(rom)
    overlay, reloc, assets = [files[v].extract(rom) for v in (NEW_ACTOR, NEW_RELOC, ASSETS)]
    validate(overlay, reloc, profile)
    if debug.read_memory(0x80000318, 4) != bytes.fromhex('00800000'):
        raise ValueError('English title preview requires detected eight-MiB RAM')
    read, actor, base, bank = locate(debug, memory_end=0x80800000)
    if base != BASE or actor >= 0x80400000:
        raise ValueError('Title overlay or actor is outside its declared owner')
    guard = struct.pack('>4I', *([GUARD]*4))
    if read(base-16, 16) != guard or read(base+len(overlay), 16) != guard:
        raise ValueError('Title Expansion Pak boundary guard changed')
    expected = relocate_verified_data(Image(RAM, len(overlay), struct.unpack_from('>5I', reloc)),
                                     overlay, reloc, base, memory_end=0x80800000)
    for at in range(0, len(expected), 4096):
        chunk = expected[at:at+4096]
        if read(base+at, len(chunk)) != chunk:
            raise ValueError(f'Loaded English title differs at overlay offset {at:08X}')
    if read(bank, len(assets)) != assets:
        raise ValueError('Loaded English Press Start bank differs')
    state = read(actor+0x330, 1152)
    magic, phase, draws, error, alpha = struct.unpack_from('>5I', state)
    if (magic != 0x41465453 or phase != 2 or draws < 5 or error != 0 or alpha != 220
            or struct.unpack_from('>I', state, 1148)[0] != 0xC17E5AFE):
        raise ValueError(f'English title animation or graphics guard failed: {magic:08X}/{phase}/{draws}/{error}/{alpha}')
    frames = [struct.unpack_from('>f', state, 20+i*112+16)[0] for i in range(3)]
    if frames != [121.0]*3:
        raise ValueError('English title animations did not reach their source final frame')
    flags = read(actor+0x31C, 8)
    if flags[:6] != bytes([1]*6):
        raise ValueError('English title did not release the native completion flags')
    for group in (1, 2):
        at = 20+3*112+group*22*6+15*6
        if state[at:at+7*6] != bytes(7*6):
            raise ValueError('English title animation exceeded its joint work area')
    return {'title_logo_memory': 'passed', 'actor': f'{actor:08X}', 'overlay': f'{base:08X}',
            'overlay_bytes': len(overlay), 'asset_bank': f'{bank:08X}', 'animation_frames': frames,
            'draws': draws, 'phase': phase, 'background_alpha': alpha, 'error': error,
            'read_only': True, 'visual_validation': False, 'main_logo_replaced': True}


def verify_warning(debug, rom):
    """Check the actual unsupported-machine framebuffer without a screenshot."""
    if sha256(rom) != COMBINED_SHA256:
        raise ValueError('Expansion warning check requires the complete combined title build')
    if debug.read_memory(0x80000318, 4) != bytes.fromhex('00400000'):
        raise ValueError('Expansion warning check requires actual four-MiB emulation')
    if debug.read_memory(0x80102200, 4) != bytes(4):
        raise ValueError('Unsupported machine has a loaded high-memory title pointer')
    if debug.read_memory(0x800418D8, 4) != bytes(4):
        raise ValueError('Expansion warning caused a native fault')
    state, flags, thread_id = struct.unpack('>2HI', debug.read_memory(0x80145640, 8))
    if state != 1 or thread_id != 4 or flags:
        raise ValueError('Expansion warning has not cleanly stopped its graph caller')
    data = debug.read_memory(0x80041960, 60)
    fb, width, height, top, bottom, left, right, fg, bg, x, y, font, cw, ch, wp, hp = struct.unpack_from('>I10HI2B2b', data)
    if (width, height, top, bottom, left, right, fg, bg, font, cw, ch, wp, hp) != (
            320, 240, 16, 223, 22, 297, 0xFFFF, 0, 0x8003DE50, 8, 8, 0, 0):
        raise ValueError('Expansion warning drawer differs from the checked native format')
    if fb & 1 or not 0x80000400 <= fb <= 0x80400000-width*height*2:
        raise ValueError('Expansion warning framebuffer exceeds four MiB')
    pixels = bytearray()
    for start in range(0, width*height*2, 4096):
        pixels.extend(debug.read_memory(fb+start, min(4096, width*height*2-start)))
    glyphs = debug.read_memory(font, 2048)
    message = 'Expansion Pak required.\n\nPower off and install it.'
    cursor_x, cursor_y, checked = left, top, 0
    for char in message:
        if char == '\n':
            cursor_x, cursor_y = left, cursor_y+8
            continue
        code = ord(char)
        for row in range(8):
            word = struct.unpack_from('>I', glyphs, ((code//8)*16+((code&4)>>2)+row*2)*4)[0]
            mask = 0x10000000 << (code%4)
            for column in range(8):
                actual = struct.unpack_from('>H', pixels, ((cursor_y+row)*width+cursor_x+column)*2)[0]
                if actual != (0xFFFF if word & (mask>>(column*4)) else 1):
                    raise ValueError(f'Expansion instruction framebuffer differs at character {checked}, row {row}, column {column}')
        cursor_x += 8
        checked += 1
    if (x, y) != (cursor_x, cursor_y):
        raise ValueError('Expansion instruction was not completely printed')
    return {'title_expansion_warning': 'passed', 'framebuffer': f'{fb:08X}',
            'message': message, 'verified_glyphs': checked, 'verified_pixels': checked*64,
            'detected_ram_bytes': 0x400000, 'graph_thread_stopped': True,
            'faulted_thread': False, 'read_only': True, 'hardware_acceptance': False}
