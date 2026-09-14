"""Native attachment transforms and graphics commands on a bounded synthetic rig."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_accessory_runtime import BLOB, BLOB_RAM, PACKAGE_RAM, PACKAGE_SIZE, PACKAGE_VROM
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record, *, tail_only=False):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or report.get('runtime_abi') not in (52, 53):
        raise ValueError('Native accessory check needs its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    package_size = report['accessory_runtime']['package_bytes']
    if package_size not in (PACKAGE_SIZE, 0xF000):
        raise ValueError('Unexpected accessory/audio package size')
    package = blob[PACKAGE_VROM-BLOB:PACKAGE_VROM-BLOB+package_size]
    proofs = boot_proofs(rom)
    edge = b'V3AC'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'accessory_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native accessory mismatch: '+label+'; observed '+actual.hex())

    def call(address, args):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result)
        return result['return_value']

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    check('complete loaded accessory code, registry, and all sixteen graphics', PACKAGE_RAM, package)
    before_state = debug.read_memory(0x8046C000, 864)
    segments = debug.read_memory(0x801458A0, 64)
    old_matrix = debug.read_memory(0x801462B4, 4)
    allocation = call(0x8009BFC0, [0x5000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x5000:
        raise ValueError('Accessory native fixture allocation failed')
    game, actor, graph, model, state, joints, matrices, matrix_stack, display, bridge, output = (
        allocation+n for n in (0x10, 0x200, 0x400, 0x800, 0xA00, 0xB00, 0xC00,
                               0xD00, 0x1100, 0x3400, 0x3500))
    guards = (allocation, actor-16, actor+0x100, graph-16, graph+0x308,
        model-16, model+0x180, state-16, state+0x70, joints-16, joints+0xB0,
        matrices-16, matrices+64, matrix_stack-16, matrix_stack+0x300,
        display-16, display+0x1200, bridge-16, bridge+32, output-16, output+104,
        allocation+0x4FF0, TEST_STACK-0x800, TEST_STACK+0x40)
    debug.write_memory(allocation, bytes(0x5000))
    for at in guards: debug.write_memory(at, edge)
    wrappers = b''.join(struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0)
                       for target in (report['accessory_runtime']['code']['symbols']['af_v3_accessory_draw'],
                                      report['asset']['symbols']['af_v3_npc_draw']))
    debug.write_memory(bridge, wrappers)
    call(0x8002FE00, [bridge, len(wrappers)])
    call(0x80034CE0, [bridge, len(wrappers)])
    proofs[bridge] = proofs[bridge+16] = (bridge, wrappers)
    debug.write_memory(game, struct.pack('>I', graph))
    # A root with 25 leaf joints exercises actual native matrix traversal without
    # exceeding its 20-matrix stack or relying on an ordinary NPC actor fixture.
    rig = bytearray(8+26*12)
    struct.pack_into('>BBHI', rig, 0, 26, 0, 0, 0x06000008)
    for joint in range(26):
        struct.pack_into('>IBBhhh', rig, 8+joint*12, 0, 25 if not joint else 0, 0,
                         joint*2, joint*3, joint*4)
    debug.write_memory(model, rig)
    pose = bytearray(27*6)
    struct.pack_into('>3h', pose, 0, 7, 8, 9)
    debug.write_memory(joints, pose)
    debug.write_memory(state+0x18, struct.pack('>I', model))
    debug.write_memory(state+0x24, struct.pack('>I', joints))
    debug.write_memory(actor+0x5C, struct.pack('>f', 0.005))
    world = struct.pack('>16f', 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 100, 200, 300, 1)
    debug.write_memory(matrix_stack, world)
    debug.write_memory(0x801462B4, struct.pack('>I', matrix_stack))
    debug.write_memory(0x801458B8, struct.pack('>I', model-0x80000000))
    imported = {r['name']: r for r in report['accessory_runtime']['imports']}
    try:
        for name in (() if tail_only else ('Maelle', 'Yodel')):
            row = imported[name]
            identity = int(row['actor_id'], 16)
            debug.write_memory(output, b'\xA5'*104)
            if call(bridge+16, [output, identity]) != 1:
                raise ValueError('Native imported draw-copy failed')
            at = 0x2000+(identity-0xE0DA)*104
            check('complete new '+name+' draw record', output, blob[at+4:at+104]+b'\xA5'*4)
        cases = [('Maelle', False, False), ('Yodel', False, False),
                 ('native', False, False), ('Yodel', True, False), ('Yodel', False, True)]
        for name, tight, no_matrices in (cases[-1:] if tail_only else cases):
            row = imported.get(name)
            identity = int(row['actor_id'], 16) if row else 0xE000
            debug.write_memory(actor+6, struct.pack('>H', identity))
            debug.write_memory(display, b'\xA5'*0x1200)
            tail = display+(128 if tight else 0x1000)
            debug.write_memory(graph+0x298, struct.pack('>II', display, tail))
            debug.write_memory(graph+0x2A8, struct.pack('>II', display+0x1100, display+0x1200))
            call(bridge, [game, state, 0 if no_matrices else matrices, 0, 0, actor])
            attached = bool(row) and not tight and not no_matrices
            commands = [] if no_matrices else [(0xDB060034, matrices)]
            if attached:
                commands += [(0xDE000000, 0x8010CB30+10*48), (0xE7000000, 0),
                    (0xFA000080, 0xFFFFFFFF),
                    (0xDB060018, int(row['resident_address'], 16)-0x80000000),
                    (0xDA380003, tail-64), (0xDE000000, int(row['display_list'], 16)),
                    (0xDB060018, model-0x80000000)]
                j = row['joint']
                values = (2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 107+j*2, 208+j*3, 309+j*4, 1)
                check(name+' native joint attachment matrix', tail-64,
                      struct.pack('>16H', *values)+bytes(32))
            raw = b''.join(struct.pack('>II', *words) for words in commands)
            check(name+' complete opaque commands or untouched empty output', display, raw or b'\xA5'*16)
            check(name+' command and matrix allocation', graph+0x298,
                  struct.pack('>II', display+len(raw), tail-(64 if attached else 0)))
            if not no_matrices:
                check(name+' retained translucent skeleton command', display+0x1100,
                      struct.pack('>II', 0xDB060034, matrices))
            check(name+' matrix stack pointer restored', 0x801462B4, struct.pack('>I', matrix_stack))
            check(name+' world transform retained', matrix_stack, world)
        check('complete shared package remains immutable', PACKAGE_RAM, package)
        check('complete prefix remains intact', BLOB_RAM, blob[:0xC000])
        check('save/profile state unchanged', 0x8046C000, before_state)
        for address in guards: check('fixture and stack guard', address, edge)
        for address, marker in ((0x8019C8D0, 'AF32C0DE'), (0x80472850, 'AF46C0DE'),
                                (PACKAGE_RAM+package_size-16, 'AFACC0DE')):
            check('production memory guard', address, bytes.fromhex(marker)*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        debug.write_memory(0x801458A0, segments)
        debug.write_memory(0x801462B4, old_matrix)
        call(0x8009C040, [allocation])
    return {'native_head_and_torso_transforms': not tail_only, 'real_accessory_graphics_commands': not tail_only,
            'unfinished_tail_only': tail_only,
            'synthetic_rig': True, 'ordinary_npc_or_gpu_rendering': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
