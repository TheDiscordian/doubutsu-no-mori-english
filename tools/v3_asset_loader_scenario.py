"""Generate a bounded, silent current-V3 startup and native object-DMA check."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from apply_translation import write_new
from v3_asset_loader import BLOB, BLOB_RAM, MODULE_RAM, ROOT, TABLE_OFFSET


def scenario(rom, report):
    if sha256(rom) != report['output_sha256'] or report['object_capacity'] != 430:
        raise ValueError('Native V3 scenario does not match its loader build')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    # Do not use the former +6000 test return: V3 owns +6000..63FF.
    arena, return_pc, destination = MODULE_RAM + 0x6500, MODULE_RAM + 0x6480, 0x80463000
    jump = 0x08000000 | (report['asset']['symbols']['af_v3_object_status'] >> 2 & 0x3FFFFFF)
    actions = [{'wait': 10}, {'read': ['8019ACD0', 4], 'expect': '00000001'},
        {'read': [f'{BLOB_RAM:08X}', len(blob)], 'expect': blob.hex()},
        {'read': ['800C5AA0', 8], 'expect': struct.pack('>2I', jump, 0).hex()},
        {'read': ['8003CE34', 4], 'expect': '00000000'},
        {'save_state': True}, {'pause_game_thread': True}]
    for bank in (133, 426, 429, 410, 430):
        memory = bytearray(0x1824)
        struct.pack_into('>2I', memory, 0x1800, destination, destination + 0x2000)
        actions.append({'write': [f'{arena:08X}', memory.hex()]})
        valid = bank in (133, 426, 429)
        actions.append({'call': {'address': '800C5B74', 'arguments': [arena, bank],
                                 'return_address': return_pc, 'expect_return': int(valid)}})
        if valid:
            start, end = struct.unpack_from('>2I', blob, TABLE_OFFSET + bank * 8)
            data = files[start].extract(rom)
            if end - start != len(data) or len(data) >= 0x2000:
                raise ValueError('Unexpected test object size')
            struct.pack_into('>H', memory, 0, bank)
            struct.pack_into('>4I', memory, 4, destination, destination, start, len(data))
            struct.pack_into('>H', memory, 0x50, 1)
            struct.pack_into('>I', memory, 0x17F4, 1)
            struct.pack_into('>I', memory, 0x1800, (destination + len(data) + 15) & ~15)
            actions.append({'read': [f'{destination:08X}', len(data)], 'expect': data.hex()})
        actions.append({'read': [f'{arena:08X}', len(memory)], 'expect': memory.hex()})
    memory = bytearray(0x1824)
    struct.pack_into('>2I', memory, 0x1800, destination, destination + 0x2000)
    actions.extend([
        {'write': [f'{arena:08X}', memory.hex()]},
        {'call': {'address': '800C5AA0', 'arguments': [arena, arena, 0x123401AD],
                  'return_address': return_pc, 'expect_return': 1}}])
    start, end = struct.unpack_from('>2I', blob, TABLE_OFFSET + 429 * 8)
    struct.pack_into('>h', memory, 0, -429)
    struct.pack_into('>4I', memory, 4, 0, destination, start, end - start)
    memory[0x53] = 1
    struct.pack_into('>I', memory, 0x1800, (destination + end - start + 15) & ~15)
    actions.append({'read': [f'{arena:08X}', len(memory)], 'expect': memory.hex()})
    actions.extend([
        {'read': ['8019C8D0', 16], 'expect': 'AF32C0DE' * 4},
        {'read': ['80461FF0', 16], 'expect': 'AF33C0DE' * 4},
        {'read': ['80450000', 16], 'expect': 'AF46C0DE' * 4},
        {'read': ['80457FF0', 16], 'expect': 'AF46C0DE' * 4},
        {'read': ['8003CE34', 4], 'expect': '00000000'},
        {'load_state': True}, {'wait': 2},
        {'read': ['8019ACD0', 4], 'expect': '00000001'},
        {'read': ['8003CE34', 4], 'expect': '00000000'}])
    return actions


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT / 'build/v3-asset-loader-02')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if not args.output.resolve().is_relative_to(ROOT / 'build'):
        raise ValueError('Generated native expectations contain local game assets; keep under ignored build/')
    actions = scenario((args.build / 'animal-forest-v3-asset-loader.z64').read_bytes(),
                       json.loads((args.build / 'build.json').read_text()))
    write_new(args.output, (json.dumps(actions, indent=2) + '\n').encode())
    print(json.dumps({'output': str(args.output), 'actions': len(actions)}))


if __name__ == '__main__':
    main()
