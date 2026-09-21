"""Execute the extended native HRA counter loops with checked scratch boundaries."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_npc_draw_smoke import boot_proofs
import v3_hra as hra


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(image) != report['output_sha256'] or not report.get('hra',{}).get('birth_extension'):
        raise ValueError('Acquisition counter check requires the current extended cartridge')
    files, hr, extension = by_vrom(image), report['hra'], report['hra']['birth_extension']
    count=extension['count'];cases=0;assertions=0
    data, reloc = (files[v].extract(image) for v in (hra.NEW_VROM, hra.NEW_RELOC))
    if (sha256(data) != hr['output_sha256'] or sha256(reloc) != hr['relocation_sha256']
            or count not in (23,27) or extension['stack_bytes'] != 80+count*8):
        raise ValueError('Changed acquisition-score test contract')
    boot = boot_proofs(image)

    def check(label, address, expected):
        nonlocal assertions
        actual = debug.read_memory(address, len(expected))
        record({'hra_birth_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Acquisition-score mismatch: ' + label)
        assertions+=1

    def call(address, args, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        return result['return_value']

    def put(address, value):
        debug.write_memory(address, struct.pack('>I', value))

    allocation = call(0x8009BFC0, [0xA000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x803F6000:
        raise ValueError('Acquisition-score fixture allocation failed')
    owner = allocation + 16
    layers, points, first, second = (allocation + n for n in (0x8800, 0x8820, 0x8900, 0x8C00))
    if owner + len(data) + len(reloc) >= layers - 16:
        raise ValueError('Acquisition-score owner exceeds fixture storage')
    debug.write_memory(allocation, bytes(0xA000))
    loaded = relocate_verified_data(Image(hra.RAM, len(data), struct.unpack_from('>5I', reloc)),
                                    data, reloc, owner)
    call(0x800262D0, [hra.NEW_VROM, hra.NEW_VROM + len(data), hra.RAM,
                      hra.RAM + len(data), owner, owner + len(data), len(reloc)])
    check('complete actual relocated HRA owner', owner, loaded)
    proof = owner, loaded[:hra.SECTIONS[0]]
    saved = {at: debug.read_memory(at, size) for at, size in ((0x80107B50, 4), (0x8046C000, 1232))}
    edge = b'V3HB' * 4
    guards = (allocation, layers - 16, points - 16, points + 16, first - 16,
              first + 512, second - 16, second + 512, allocation + 0x9FF0,
              TEST_STACK - 0x700, TEST_STACK + 32)
    # Reset these after loader calls, whose ordinary stack use is unrelated.
    for at in guards:
        debug.write_memory(at, edge)
    metadata_at = hr['metadata_address'] - hra.RAM
    weights = struct.unpack_from('>'+str(count)+'I', loaded, extension['points_address'] - hra.RAM)
    try:
        put(0x80107B50, owner)
        put(layers, first); put(layers + 4, second)

        def evaluate(label, expected_counts, expected_total, room=5, wall=0, floor=0):
            nonlocal cases
            put(points, 17)
            call(owner + 0x809274F8 - hra.RAM, [points, layers, room, wall, floor], proof)
            check(label + ': complete counters including last category', TEST_STACK - count*4,
                  struct.pack('>'+str(count)+'I', *expected_counts))
            check(label + ': complete products', TEST_STACK - count*8,
                  struct.pack('>'+str(count)+'I', *(n * w for n, w in zip(expected_counts, weights, strict=True))))
            if expected_total is not None:
                check(label + ': native total and caller accumulator', points, struct.pack('>I', expected_total))
            check(label + ': caller stack boundary', TEST_STACK + 32, edge)
            cases+=1
            return u32(debug.read_memory(points, 4), 0)

        baseline = evaluate('empty room', [0] * count, 119)
        # Temporary metadata exercises new categories before real reward IDs
        # are enabled. This is not an acquisition or mailbox gameplay claim.
        categories = (7, 8, 18, *range(19,count))
        for slot, category in enumerate(categories):
            word = u32(loaded, metadata_at + slot * 4)
            put(owner + metadata_at + slot * 4, word & ~0x3E00 | category << 9)
        for slot, category in enumerate(categories):
            grid = bytearray(512)
            struct.pack_into('>H', grid, 34, 0x1000 + slot * 4)
            debug.write_memory(first, grid)
            counts = [0] * count; counts[category] = 1
            evaluate(f'category {category}', counts, baseline + weights[category])
        grids, counts = [bytearray(512), bytearray(512)], [0] * count
        second_counts = [0]*count
        for slot, category in enumerate(categories):
            layer, cell = (slot%2,17+slot//2) if slot<len(categories)-1 else (1,255)
            struct.pack_into('>H', grids[layer], cell * 2, 0x1000 + slot * 4)
            counts[category] += 1
            if layer==1:second_counts[category]+=1
        debug.write_memory(first, grids[0]); debug.write_memory(second, grids[1])
        evaluate('mixed layers with far-corner final category', counts,
                 baseline + sum(n * w for n, w in zip(counts, weights, strict=True)), room=16)
        evaluate('mixed furniture with independent full surface weights', counts,
                 17+1000+1177+sum(n*w for n,w in zip(counts,weights,strict=True)),room=16,wall=75,floor=77)
        put(layers, 0)
        evaluate('null first layer retains second layer', second_counts,
                 baseline+sum(n*w for n,w in zip(second_counts,weights,strict=True)), room=16)
        put(layers + 4, 0)
        evaluate('both layers absent', [0] * count, baseline)
        evaluate('invalid surface arguments are bounded', [0]*count,17,wall=256,floor=0xFFFFFFFF)
        check('original and expanded executable remains intact', owner, loaded[:hra.SECTIONS[0]])
        for at in guards:
            check('allocation and stack guard', at, edge)
        check('no CPU fault', 0x8003CE34, bytes(4))
    finally:
        for at, data in saved.items():
            debug.write_memory(at, data)
    check('complete saved import state retained', 0x8046C000, saved[0x8046C000])
    call(0x8009C040, [allocation])
    return {'native_acquisition_counter_cases': cases, 'assertions':assertions,'birth_categories':count,
            'expanded_stack_and_products_checked': True,
            'saved_data_written': False, 'reward_acquisition_or_new_item_gameplay_tested': False,
            'requires_checkpoint_restore': True}
