"""Install additive campsite scene/field loading; event/acquisition stays unfinished."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, apply_ups, by_vrom,
                   fix_checksum, make_ups, sha256, verified_rom)
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, compile_part
from v3_import_storage import PACKAGE, PACKAGE_RAM, PACKAGE_SIZE as OLD_PACKAGE_SIZE, END, replace_checked, jump
import v3_campsite_scene as scene

ROOT = scene.ROOT
ABI, PACKAGE_SIZE = 71, OLD_PACKAGE_SIZE + 0x2000
SCENE_BUILD = ROOT / 'build/v3-campsite-scene-02'
PLAY, PLAY_RAM, PLAY_RELOC = 0x741FB0, 0x80802AE0, 0x743950


def play_relocations(image, raw, changed_ranges):
    sections = struct.unpack_from('>5I', raw)
    if (sections != (0x1840, 0xA0, 0xC0, 0xF0, 128) or len(image) != sum(sections[:3])
            or len(raw) != 544 or struct.unpack_from('>I', raw, len(raw) - 4)[0] != len(raw)):
        raise ValueError('Changed complete gameplay relocation dimensions')
    keep, removed = [], []
    for record, in struct.iter_unpack('>I', raw[20:20 + 128 * 4]):
        section, kind, off = record >> 30, record >> 24 & 63, record & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6) or off % 4 or off + 4 > sections[section - 1]:
            raise ValueError('Invalid gameplay relocation')
        address = PLAY_RAM + sum(sections[:section - 1]) + off
        (removed if any(a <= address < b for a, b in changed_ranges) else keep).append(record)
    # The status-table calculation refers to resident data and has no relocation.
    # The replaced original local sound-selector JAL has one.
    if removed != [0x44000000 | (0x808042F8 - PLAY_RAM)] or any(raw[20 + 128 * 4:-4]):
        raise ValueError('Changed gameplay hook relocation ownership')
    result = bytearray(raw)
    struct.pack_into('>I', result, 16, len(keep))
    result[20:-4] = struct.pack('>' + str(len(keep)) + 'I', *keep) + bytes(len(raw) - 24 - len(keep) * 4)
    return bytes(result), removed


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = scene.BASE.read_bytes()
    prior_raw = scene.BASE.with_name('build.json').read_bytes()
    if sha256(base) != scene.BASE_SHA or sha256(prior_raw) != 'ecf0b223d51609e004a369ad2b4a2d817c9e192edff4fe2213ac9092c2e3aa7c':
        raise ValueError('Changed complete current source cartridge or report')
    native = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    prior = json.loads(prior_raw)
    files, original_files = by_vrom(base), by_vrom(native)
    old_blob = files[BLOB].extract(base)
    package = old_blob[PACKAGE:PACKAGE + OLD_PACKAGE_SIZE]
    if (prior['runtime_abi'] != 70 or len(package) != OLD_PACKAGE_SIZE
            or struct.unpack_from('>4I', old_blob, 0xF0) !=
               (BLOB + PACKAGE, OLD_PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
            or sha256(package) != prior['import_storage']['package_sha256']
            or package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or any(old_blob[PACKAGE + OLD_PACKAGE_SIZE:PACKAGE + PACKAGE_SIZE])
            or PACKAGE + PACKAGE_SIZE > 0x230000
            or PACKAGE_RAM + PACKAGE_SIZE > prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed package guard or insufficient scene reservation')
    donor_rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    donor_symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    fg = (ROOT / 'build/gamecube/files/forest_1st.arc.unpacked/data/fgdata.bin').read_bytes()
    art_raw = (scene.ART / 'art.json').read_bytes()
    prepared, contract = scene.prepare(native, base, donor_rel, donor_symbols, fg, art_raw)
    for name, data in prepared.items():
        if (SCENE_BUILD / name).read_bytes() != data:
            raise ValueError('Prepared campsite packet differs from complete source conversion')
    callbacks = json.loads((SCENE_BUILD / 'scene.json').read_bytes())
    callback_code = (SCENE_BUILD / 'code/code.bin').read_bytes()
    if sha256(callback_code) != callbacks['code']['sha256'] or callbacks['native_contract'] != contract:
        raise ValueError('Changed compiled campsite callbacks')
    symbols = callbacks['code']['symbols']
    blob = bytearray(old_blob)
    blob[PACKAGE + 8:PACKAGE + 12] = struct.pack('>I', PACKAGE_SIZE)
    code_at = PACKAGE + scene.CODE_ADDRESS - PACKAGE_RAM
    data_at = PACKAGE + scene.DATA_ADDRESS - PACKAGE_RAM
    if (len(callback_code) > 0xF00 or any(blob[code_at:code_at + 0xF00])
            or any(blob[data_at:data_at + scene.DATA_SIZE])):
        raise ValueError('Campsite code/data would overwrite existing imports')
    blob[code_at:code_at + len(callback_code)] = callback_code
    blob[data_at:data_at + scene.DATA_SIZE] = prepared['packet.bin']
    blob[PACKAGE + PACKAGE_SIZE - 16:PACKAGE + PACKAGE_SIZE] = bytes.fromhex('AFACC0DE') * 4
    resources = {scene.SCENE_VROM: prepared['scene.bin'], scene.ACTORS_VROM: prepared['actors.bin'],
        scene.FIELD_VROM: prepared['fields.bin']}
    for part, vrom in (('interior', scene.INTERIOR_VROM), ('lantern', scene.LANTERN_VROM),
                      ('exterior', scene.EXTERIOR_VROM), ('shadow', scene.SHADOW_VROM)):
        row = next(r for r in json.loads(art_raw)['objects'] if r['part'] == part)
        data = (scene.ART / row['object_file']).read_bytes()
        if len(data) != row['object_bytes'] or sha256(data) != row['object_sha256']:
            raise ValueError('Changed complete campsite scenery object')
        resources[vrom] = data
    for vrom, data in sorted(resources.items()):
        if vrom - BLOB < len(blob):
            raise ValueError('Campsite resource overlaps existing import storage')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(data)
    blob.extend(bytes(-len(blob) % 16))

    code = bytearray(files[CODE_VROM].extract(base))
    changes = []
    def patch(owner, base_ram, address, before, after, label):
        replace_checked(owner, address - base_ram, before, after)
        changes.append({'address': address, 'before': before.hex(), 'after': after.hex(), 'purpose': label})
    def address_pair(hi_at, lo_at, before, after, register):
        hi = 0x3C000000 | register << 16
        lo = 0x24000000 | register << 21 | register << 16
        for at, first, last in ((hi_at, hi | ((before + 0x8000) >> 16), hi | ((after + 0x8000) >> 16)),
                                (lo_at, lo | (before & 65535), lo | (after & 65535))):
            patch(code, CODE_RAM, at, struct.pack('>I', first), struct.pack('>I', last), 'expanded field directory')
    address_pair(0x8008684C, 0x80086850, 0x01148000, scene.FIELD_VROM, 15)
    address_pair(0x8008700C, 0x80087018, 0x011492A0, scene.FIELD_VROM + len(prepared['fields.bin']), 24)
    address_pair(0x80087010, 0x80087014, 0x01148000, scene.FIELD_VROM, 25)
    patch(code, CODE_RAM, 0x80086AF0, struct.pack('>I', jump(0x8008609C, link=True)),
          struct.pack('>I', jump(symbols['af_v3_campsite_block_info'], link=True)), 'campsite block initialization')

    play = bytearray(files[PLAY].extract(base))
    if play != original_files[PLAY].extract(native) or files[PLAY_RELOC].extract(base) != original_files[PLAY_RELOC].extract(native):
        raise ValueError('Gameplay overlay has unreviewed changes')
    status_hook = struct.pack('>6I', 0xAFA40028, jump(symbols['af_v3_campsite_scene_status'], link=True),
                              0x00C02025, 0x00402825, 0x8FA40028, 0x87A6002E)
    patch(play, PLAY_RAM, 0x8080429C, bytes.fromhex('0006708001c670213c0f801125efeaa0000e708001cf2821'),
          status_hook, 'additive scene descriptor with preserved arguments')
    patch(play, PLAY_RAM, 0x808042F8, struct.pack('>I', jump(0x80804240, link=True)),
          struct.pack('>I', jump(symbols['af_v3_campsite_room_sound'], link=True)), 'campsite room acoustics')
    reloc, removed = play_relocations(play, files[PLAY_RELOC].extract(base),
                                      ((0x8080429C, 0x808042B4), (0x808042F8, 0x808042FC)))
    # Retain both original virtual identities and directory slots. Their retail
    # compressed physical allocations are too small for uncompressed edits.
    moves = []
    for vrom, data in ((PLAY, play), (PLAY_RELOC, reloc)):
        blob.extend(bytes(-len(blob) % 16))
        offset = len(blob)
        blob.extend(data)
        moves.append({'vrom': vrom, 'bytes': len(data), 'blob_offset': offset,
                      'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})

    output.mkdir(parents=True)
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', 'AF_V3_WESTERN_LARGE=1', 'AF_V3_CAMPSITE=1'))
    module = bytearray(files[MODULE].extract(base))
    old = prior['startup']
    if sha256(module[STARTUP:STARTUP + old['bytes']]) != old['sha256'] or any(module[STARTUP + old['bytes']:CONFIG]):
        raise ValueError('Changed startup reservation')
    if len(startup) > CONFIG - STARTUP:
        raise ValueError('Campsite startup exceeds the resident reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    package = blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    struct.pack_into('>4I', blob, 0xF0, BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
    struct.pack_into('>I', blob, 4, ABI)
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    start, end = files[BLOB].pstart + len(old_blob), files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or end > len(base) or any(base[start:end])
            or any(e.pstart < end and start < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend
                   for v, e in files.items() if v != BLOB)):
        raise ValueError('Campsite expansion overlaps a live physical or virtual resource')
    replaced = {BLOB: blob, MODULE: module, CODE_VROM: code}
    result = bytearray(base)
    for vrom, data in replaced.items():
        entry = files[vrom]
        if entry.pend or vrom != BLOB and len(data) != entry.size:
            raise ValueError('Campsite requires an uncompressed fixed-size owner')
        result[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for move in moves:
        struct.pack_into('>4I', result, DMA_START + files[move['vrom']].index * 16,
                         move['vrom'], move['vrom'] + move['bytes'], move['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    if len(by_vrom(result)) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16):
        raise ValueError('Campsite changes the full DMA directory or terminator')
    patch_file = make_ups(native, result)
    if apply_ups(native, patch_file) != result:
        raise ValueError('Campsite cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-campsite-runtime', runtime_abi=ABI, input_build_sha256=scene.BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch_file), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        native_test='pending current campsite scene and field construction')
    for section in ('construction', 'garden', 'western', 'western_large', 'accessory_runtime',
                    'camping', 'tent_model', 'fire', 'import_storage'):
        report[section]['package_sha256'] = sha256(package)
    report['import_storage'].update(package_bytes=PACKAGE_SIZE,
        remaining_bytes=END - BLOB - len(blob), saved_profile_changed=False)
    report['accessory_runtime']['package_bytes'] = PACKAGE_SIZE
    report['campsite'] = {'scene': SCENE_BUILD.name, 'code': callbacks['code'], 'native_contract': contract,
        'packet_ram': scene.DATA_ADDRESS, 'packet_sha256': sha256(prepared['packet.bin']),
        'package_bytes': PACKAGE_SIZE, 'package_sha256': sha256(package), 'additional_resident_bytes': 8192,
        'resources': [{'vrom': v, 'bytes': len(d), 'sha256': sha256(d)} for v, d in sorted(resources.items())],
        'hooks': changes, 'resource_moves': moves, 'removed_play_relocations': removed, 'saved_format_changed': False,
        'saved_profile_changed': False, 'scene_loading_installed': True, 'acquisition_installed': False,
        'web_patcher_enabled': False, 'not_a_playtest_handoff': True,
        'pending': ['summer event and enterable exterior', 'camper identity and English conversations',
            'selected reward routing', 'scene lighting and floor sound', 'ordinary gameplay and persistence']}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in (
        'tools/v3_campsite_runtime.py', 'tools/v3_campsite_scene.py', 'tools/v3_asset_loader.py',
        'overlays/v3/campsite_scene.c', 'overlays/v3/campsite_scene.ld', 'overlays/v3/startup.c')})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch_file)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k: result[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}, indent=2))
