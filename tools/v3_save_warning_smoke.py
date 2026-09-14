"""Disposable incompatible-profile seed and read-only native warning verification."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

from aflib import sha256
from v3_save_codec import BANK

ROOT = Path(__file__).resolve().parents[1]
MESSAGE = 'V3 save needs other imports.\n\nPower off. Rebuild with the\nsame imports, or add the\nmissing ones. Keep your save.'


def make_seed(source, destination):
    manifest = json.loads((source / 'manifest.json').read_text())
    chip = (source / 'test.flash').read_bytes()
    if (sha256(chip) != manifest['flash_sha256'] or len(chip) != BANK * 2
            or chip[:BANK] != chip[BANK:] or not manifest['asynchronous_two_banks_passed']):
        raise ValueError('Warning seed needs the verified complete two-bank V3 export')
    if destination.exists() or not destination.resolve().is_relative_to(ROOT / 'build'):
        raise ValueError('Warning seed requires a fresh ignored build directory')
    spec = importlib.util.spec_from_file_location('v3_save_reference', ROOT / 'tests/test_v3_save_codec.py')
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    state = bytearray.fromhex(manifest['working_state_hex'])
    if state[27] & 4:
        raise ValueError('Warning seed requires unselected reserved actor index 218')
    state[27] |= 4
    # Keep the second bank compatible: loading must stop instead of silently
    # reverting to that bank and overwriting the incompatible town copy.
    modified = bytes(reference.reference_pack(chip[:BANK], state)) + chip[BANK:]
    destination.mkdir()
    (destination / 'test.flash').write_bytes(modified)
    result = {'rom_sha256': manifest['rom_sha256'], 'flash_sha256': sha256(modified),
              'missing_actor_index': 218, 'expected_message': MESSAGE, 'source_flash_sha256': sha256(chip)}
    (destination / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def verify(debug, rom_path, seed):
    rom = Path(rom_path).read_bytes()
    manifest = json.loads((seed / 'manifest.json').read_text())
    if sha256(rom) != manifest['rom_sha256'] or manifest['expected_message'] != MESSAGE:
        raise ValueError('Warning probe does not match its cartridge/seed')
    if debug.read_memory(0x8046C004, 4) != bytes.fromhex('FFFFFFF9'):
        raise ValueError('Native load has not reached the missing-import warning')
    state, flags, thread_id = struct.unpack('>2HI', debug.read_memory(0x80145640, 8))
    if (state, flags, thread_id) != (1, 0, 4) or debug.read_memory(0x8003CE34, 4) != bytes(4):
        raise ValueError('Warning must stop its graph caller without a CPU fault')
    data = debug.read_memory(0x80041960, 60)
    fb, width, height, top, bottom, left, right, fg, bg, x, y, font, cw, ch, wp, hp = struct.unpack_from('>I10HI2B2b', data)
    if (width, height, top, bottom, left, right, fg, bg, font, cw, ch, wp, hp) != (
            320, 240, 16, 223, 22, 297, 0xFFFF, 0, 0x8003DE50, 8, 8, 0, 0):
        raise ValueError('Changed native warning font/drawer layout')
    if fb & 1 or not 0x80000400 <= fb <= 0x80400000 - width * height * 2:
        raise ValueError('Warning framebuffer is outside its verified memory range')
    pixels = b''.join(debug.read_memory(fb + start, min(4096, width * height * 2 - start))
                      for start in range(0, width * height * 2, 4096))
    glyphs = debug.read_memory(font, 2048)
    cursor_x, cursor_y, checked = left, top, 0
    for char in MESSAGE:
        if char == '\n':
            cursor_x, cursor_y = left, cursor_y + 8
            continue
        if cursor_x + 7 > right or cursor_y + 7 > bottom:
            raise ValueError('Save warning exceeds the native text area')
        code = ord(char)
        for row in range(8):
            word = struct.unpack_from('>I', glyphs, ((code // 8) * 16 + ((code & 4) >> 2) + row * 2) * 4)[0]
            mask = 0x10000000 << (code % 4)
            for column in range(8):
                actual = struct.unpack_from('>H', pixels, ((cursor_y + row) * width + cursor_x + column) * 2)[0]
                if actual != (0xFFFF if word & (mask >> (column * 4)) else 1):
                    raise ValueError('Native save warning differs from its complete English message')
        cursor_x += 8
        checked += 1
    if (x, y) != (cursor_x, cursor_y):
        raise ValueError('Save warning was not completely printed')
    return {'v3_save_warning': 'passed', 'message': MESSAGE, 'verified_glyphs': checked,
            'verified_pixels': checked * 64, 'graph_thread_stopped': True, 'faulted_thread': False,
            'expected_unchanged_flash_sha256': manifest['flash_sha256'],
            'read_only_probe': True, 'hardware_tested': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(make_seed(args.source, args.output), indent=2))


if __name__ == '__main__':
    main()
