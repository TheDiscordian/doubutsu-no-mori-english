"""Isolated current scene loading and real field construction; no event fixture."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
import v3_campsite_runtime as runtime
import v3_campsite_scene as scene


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 71:
        raise ValueError('Campsite probe requires the current ABI 71 cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    dma = rom[0x1F44:0x1FC0]
    if sha256(dma) != '2afa01edf9346c8c9f4a0c6b5fbadb03970d0e348c25f045d09af4ee2602f8d1':
        raise ValueError('Changed complete native synchronous DMA function')
    boot[0x80026B44] = (0x80026B44, dma)
    blob = files[BLOB].extract(rom)
    symbols = report['campsite']['code']['symbols']

    def check(label, address, expected):
        observed = debug.read_memory(address, len(expected))
        record({'campsite_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if observed == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected:
            raise ValueError('Native campsite mismatch: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native campsite return value')
        return result['return_value']

    def pointer(address):
        return struct.unpack('>I', debug.read_memory(address, 4))[0]

    def bounded(address, size):
        if address & 15 or not MODULE_RAM + 0x8000 <= address <= 0x80400000 - size:
            raise ValueError('Campsite fixture allocation is outside the native heap')
        return address

    check('complete resident prefix', BLOB_RAM, blob[:0xC000])
    package = blob[runtime.PACKAGE:runtime.PACKAGE + runtime.PACKAGE_SIZE]
    check('complete expanded resident package', runtime.PACKAGE_RAM, package)
    saved_scene = debug.read_memory(0x80126EB4, 4)
    saved_runtime = debug.read_memory(0x8046C000, 864)
    allocation = bounded(call(0x8009BFC0, [0x2100]), 0x2100)
    play_ram, bridge = allocation + 16, allocation + 0x2080
    edge = b'V3CS' * 4
    for at in (allocation, bridge - 16, bridge + 8, allocation + 0x20F0):
        debug.write_memory(at, edge)
    # The original loader must relocate the moved gameplay resource and leave
    # its new resident calls unchanged. Do not execute scene actors yet.
    source, reloc = files[runtime.PLAY].extract(rom), files[runtime.PLAY_RELOC].extract(rom)
    sections = struct.unpack_from('>5I', reloc)
    spec = SimpleNamespace(ram=runtime.PLAY_RAM, resident_bytes=len(source) + sections[3], sections=sections)
    expected_play = relocate_verified_data(spec, source, reloc, play_ram,
                                           address_constants=(runtime.PLAY_RAM + spec.resident_bytes,))
    call(0x800262D0, [runtime.PLAY, runtime.PLAY + len(source), runtime.PLAY_RAM,
         runtime.PLAY_RAM + spec.resident_bytes, play_ram, play_ram + spec.resident_bytes, len(reloc)])
    check('complete actual relocated gameplay overlay and BSS', play_ram, expected_play)

    def resident_call(name, args, expected):
        target = symbols[name]
        stub = struct.pack('>II', 0x08000000 | ((target >> 2) & 0x3FFFFFF), 0)
        debug.write_memory(bridge, stub)
        call(0x8002FE00, [bridge, len(stub)])
        call(0x80034CE0, [bridge, len(stub)])
        call(bridge, args, expected, (bridge, stub))

    resident_call('af_v3_campsite_scene_status', [34], 0x8010EAA0 + 34 * 20)
    resident_call('af_v3_campsite_scene_status', [35], scene.DATA_ADDRESS + 0x20)
    resident_call('af_v3_campsite_scene_status', [36], 0)
    resident_call('af_v3_campsite_room_sound', [35], 2)
    resident_call('af_v3_campsite_room_sound', [20], 1)
    debug.write_memory(0x80126EB4, struct.pack('>I', scene.SCENE))
    field = bounded(call(0x800867F0, [scene.SCENE, 0xA000, 1]), 0x168)
    check('additive field ID', field, bytes.fromhex('3012'))
    check('native background allocation and block dimensions', field + 0x160,
          bytes.fromhex('a000010000000101'))
    check('no player-house foreground alias', field + 0x14C, bytes(4))
    block = bounded(pointer(field + 0x148), 0x614)
    foreground = bounded(pointer(block + 0x584), 512)
    background = bounded(pointer(field + 0x38), 0xA000)
    packet = package[0x2E000:0x2F000]
    check('native full collision height records', block + 0x20, packet[0x5C:0x45C])
    check('native complete foreground including both exits', foreground, packet[0x482:0x682])
    check('native compact camper actor placement', block + 0x58C, bytes.fromhex('d08f0303ff000000'))
    check('native field model bindings', block + 4, packet[0x44:0x50])
    check('native field ROM object range', block + 0x18, struct.pack('>II', scene.INTERIOR_VROM, 19872))
    resource = blob[scene.INTERIOR_VROM - BLOB:scene.INTERIOR_VROM - BLOB + 19872]
    debug.write_memory(background, b'\xA5' * 0xA000)
    call(0x80026B44, [background, scene.INTERIOR_VROM, len(resource)])
    check('actual complete interior DMA and intact allocation padding', background,
          resource + b'\xA5' * (0xA000 - len(resource)))
    for at in (allocation, bridge - 16, bridge + 8, allocation + 0x20F0):
        check('private fixture guard', at, edge)
    check('complete save runtime retained', 0x8046C000, saved_runtime)
    check('complete resident prefix retained', BLOB_RAM, blob[:0xC000])
    check('complete expanded package retained', runtime.PACKAGE_RAM, package)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(0x80126EB4, saved_scene)
    for owned in (foreground, background, block, field, allocation):
        call(0x8009C040, [owned])
    return {'native_campsite_field_constructor': True, 'actual_interior_model_dma': True,
        'actual_gameplay_overlay_relocation': True, 'scene_actor_entry_tested': False,
        'event_acquisition_or_persistence_tested': False, 'gpu_or_hardware_tested': False,
        'requires_checkpoint_restore': True}
