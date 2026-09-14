"""Attach complete islander accessories and install all twenty native draw rows."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import (DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom)
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import BLOB, BLOB_RAM, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_import_catalog import REL_SHA, SYMBOLS_SHA
from v3_npc_draw import DRAW_OFFSET, STRIDE, relocation_offsets
from v3_registry import villager_actor
from v3_villager_art import native_species
from v3_villager_assets_runtime import ART, ART_SHA, CAPACITY, RESIDENT, load_art

ABI = 52
BASE = ROOT/'build/v3-complete-villager-assets-01'
BASE_SHA = 'ac0f03c94b94a7eea434a0a112c745205cc76f4006f3a7383dc13c7669cad57f'
PACKAGE_VROM, PACKAGE_RAM, PACKAGE_SIZE = 0x02270000, 0x80473000, 0xC000
MAGIC, GUARD = 0x41464133, 0xAFACC0DE
OWNERS = (
    (0x8681F0, 0x878550, 0x809735B0, 0x809780E4, 0x8097866C, 0x80978654,
     'f55de38cd185c9b61e147471c012f3911d7245ee528a518c69982b944175ba23',
     'f67e224488e497b3c5ee2ad5c8b182545845e6d256a68c6f5c0776f09c53fd38'),
    (0x8798C0, 0x886FA0, 0x80995BF0, 0x80999D70, 0x8099A2F8, 0x8099A2E0,
     'b792f1cf5c68c896f5b25675e3a8e3dd588feccb6732c5f57f1c1e45baa3060f',
     '1202043ce27a0d124a425db35def68a6d42589986a53c35d1e20f0db2925af87'),
)
SOURCES = ('tools/v3_accessory_runtime.py', 'overlays/v3/accessory.c', 'overlays/v3/accessory.h',
    'overlays/v3/accessory.ld', 'overlays/v3/startup.c', 'overlays/v3/startup.ld',
    'tools/v3_asset_loader.py', 'tools/v3_villager_assets_runtime.py')


def prepare_rows(native, rel, symbols, manifest, records):
    if sha256(rel) != REL_SHA or sha256(symbols) != SYMBOLS_SHA:
        raise ValueError('Unknown donor REL or symbol map')
    source = symbol_data(rel, symbols.decode(), 'npc_draw_data_tbl')
    banks = {(r['id'], r['kind']): r for r in records}
    output, result = bytearray(20*STRIDE), []
    for row in manifest['villagers']:
        donor = int(row['id'].split('/')[-1], 16)
        actor = villager_actor(donor)
        original = source[donor*108:(donor+1)*108]
        if sha256(original) != row['donor_draw_record_sha256'] or original[0x5F:0x62] != bytes(3):
            raise ValueError('Changed donor draw flags or identity')
        draw = bytearray(native_species(native, row['species'])[0])
        texture = banks[(row['id'], 'texture')]
        model = banks.get((row['id'], 'model'))
        struct.pack_into('>H', draw, 2, texture['bank'])
        if model:
            struct.pack_into('>H', draw, 0, model['bank'])
            struct.pack_into('>I', draw, 4, int(model['skeleton'], 16))
        draw[0x54:0x5F] = original[0x54:0x5F]
        draw[0x5F] = 255
        draw[0x60:0x64] = original[0x64:0x68]
        voice = struct.unpack_from('>H', original, 0x62)[0]
        if voice != row['donor_voice_id'] or not 0 <= voice < 299:
            raise ValueError('Changed imported voice identity')
        accessory = banks.get((row['id'], 'accessory'))
        tool, joint = struct.unpack_from('>hh', original, 0x68)
        if ((accessory and (tool, joint) != (accessory['donor_tool'], accessory['joint']))
                or (not accessory and (tool, joint) != (-1, -1))):
            raise ValueError('Changed donor attachment binding')
        at = (actor-0xE0DA)*STRIDE
        output[at:at+STRIDE] = struct.pack('>HH', actor, voice)+draw
        result.append({'id': row['id'], 'name': row['name'], 'actor_id': f'{actor:04X}',
            'object_bank': texture['bank'], 'model_bank': struct.unpack_from('>H', draw)[0],
            'skeleton': f'{struct.unpack_from(">I", draw, 4)[0]:08X}',
            'voice_id': voice, 'record_sha256': sha256(draw), 'registry_version': 1,
            'audio_playback_ready': donor in (232, 235), 'move_in_enabled': False,
            'accessory_bank': accessory['bank'] if accessory else None})
    if len(result) != 20:
        raise ValueError('Incomplete native draw set')
    return output, sorted(result, key=lambda r: r['actor_id'])


def package_art(code, records, resources):
    if not 0 < len(code) <= 0xF00:
        raise ValueError('Accessory helper exceeds code reservation')
    package = bytearray(PACKAGE_SIZE)
    struct.pack_into('>4I', package, 0, MAGIC, 1, PACKAGE_SIZE, 20)
    package[0x100:0x100+len(code)] = code
    package[-16:] = struct.pack('>4I', *([GUARD]*4))
    cursor, result = 0x2000, []
    for row in records:
        if row['kind'] != 'accessory':
            continue
        cursor = (cursor+31) & ~31
        data = resources[row['bank']]
        if cursor+len(data) > PACKAGE_SIZE-16:
            raise ValueError('Accessory artwork exceeds its shared reservation')
        actor = villager_actor(int(row['id'].split('/')[-1], 16))
        at = 0x1000+(actor-0xE0DA)*16
        if any(package[at:at+16]):
            raise ValueError('Duplicate accessory consumer')
        address, display = PACKAGE_RAM+cursor, int(row['display_list'], 16)
        if display >> 24 != 6 or (display & 0xFFFFFF) >= len(data):
            raise ValueError('Accessory display list escapes its object')
        struct.pack_into('>HHIIBBH', package, at, actor, row['bank'], address,
                         display, row['joint'], 1, len(data))
        package[cursor:cursor+len(data)] = data
        result.append({**row, 'actor_id': f'{actor:04X}', 'resident_address': f'{address:08X}',
                       'runtime_attached': True})
        cursor += len(data)
    if len(result) != 16:
        raise ValueError('Incomplete resident attachment set')
    return package, result


def patch_owners(base, target):
    files, changes, reports = by_vrom(base), {}, []
    for vrom, reloc, ram, start, end, call, digest, function_digest in OWNERS:
        old = files[vrom].extract(base)
        reloc_data = files[reloc].extract(base)
        at = call-ram
        if (sha256(old) != digest or sha256(old[start-ram:end-ram]) != function_digest
                or old[at:at+8] != bytes.fromhex('0c014c36afa80014')
                or at in relocation_offsets(reloc_data, len(old))):
            raise ValueError('Changed complete NPC renderer, skeleton call, or relocation')
        data = bytearray(old)
        struct.pack_into('>I', data, at, 0x0C000000 | (target >> 2 & 0x3FFFFFF))
        changes[vrom] = data
        reports.append({'vrom': f'{vrom:08X}', 'ram': f'{ram:08X}', 'call': f'{call:08X}',
            'renderer_start': f'{start:08X}', 'renderer_end': f'{end:08X}',
            'input_sha256': digest, 'output_sha256': sha256(data),
            'renderer_sha256': function_digest, 'relocation_sha256': sha256(reloc_data),
            'delay_slot_preserved': True, 'relocations_unchanged': True})
    return changes, reports


def compose(base, blob, changes):
    if sha256(base) != BASE_SHA or set(changes) != {MODULE, 0x8681F0, 0x8798C0}:
        raise ValueError('Unreviewed accessory input or resource set')
    files = by_vrom(base)
    last = max(e.pend or e.pstart+e.size for e in files.values() if e.pstart != 0xFFFFFFFF)
    start = (last+15) & ~15
    if any(base[last:]) or start+len(blob) > len(base) or len(blob) != 0x7C000:
        raise ValueError('Accessory package does not fit its checked physical/virtual reservation')
    if any(e.vstart < BLOB+len(blob) and BLOB < e.vend for v, e in files.items() if v != BLOB):
        raise ValueError('Accessory resource overlaps an existing virtual file')
    result = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or len(data) != entry.size:
            raise ValueError('Changed in-place resource size or compression')
        result[entry.pstart:entry.pstart+entry.size] = data
    result[start:start+len(blob)] = blob
    struct.pack_into('>4I', result, DMA_START+files[BLOB].index*16, BLOB, BLOB+len(blob), start, 0)
    fix_checksum(result)
    return bytes(result)


def build(output, base_directory=BASE, art_directory=ART):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Generated resources belong under ignored build/')
    base = (base_directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('Expected current complete-artwork ABI-51 cartridge')
    previous = json.loads((base_directory/'build.json').read_text())
    records, resources = load_art(art_directory)
    manifest = json.loads((art_directory/'art.json').read_text())
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    draw, draw_report = prepare_rows(native, rel, symbols, manifest, records)
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    if any(blob[0xF0:0x100]) or len(blob) >= PACKAGE_VROM-BLOB:
        raise ValueError('Occupied accessory descriptor or resource span')
    for slot in range(20):
        at = DRAW_OFFSET+slot*STRIDE
        if slot in (16, 19):
            if blob[at:at+STRIDE] != draw[slot*STRIDE:(slot+1)*STRIDE]:
                raise ValueError('Existing pilot draw row changed')
        elif any(blob[at:at+STRIDE]):
            raise ValueError('Occupied new villager draw row')
    output.mkdir(parents=True, exist_ok=False)
    code, compiled = compile_part('accessory', output/'accessory')
    package, attachments = package_art(code, records, resources)
    blob.extend(bytes(PACKAGE_VROM-BLOB-len(blob)))
    blob.extend(package)
    blob[DRAW_OFFSET:DRAW_OFFSET+len(draw)] = draw
    struct.pack_into('>I', blob, 4, ABI)
    struct.pack_into('>4I', blob, 0xF0, PACKAGE_VROM, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
    startup, startup_report = compile_part('startup', output/'startup', defines=(
        f'AF_V3_BLOB_SIZE={RESIDENT}', f'AF_V3_ABI={ABI}', f'AF_V3_OBJECT_CAPACITY={CAPACITY}',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1', 'AF_V3_ACCESSORIES=1'))
    if len(startup) > CONFIG-STARTUP:
        raise ValueError('Accessory startup overlaps configuration')
    module = bytearray(files[MODULE].extract(base))
    old_size = previous['startup']['bytes']
    if sha256(module[STARTUP:STARTUP+old_size]) != previous['startup']['sha256']:
        raise ValueError('Changed current startup helper')
    if any(module[STARTUP+old_size:CONFIG]):
        raise ValueError('Accessory startup growth overlaps existing code')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, RESIDENT, zlib.crc32(blob[:RESIDENT]), ABI)
    changes, owners = patch_owners(base, compiled['symbols']['af_v3_accessory_draw'])
    changes[MODULE] = module
    image = compose(base, blob, changes)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Accessory cartridge patch reconstruction failed')
    report = {**previous, 'build': 'v3-accessory-runtime', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_sha256': sha256(blob), 'blob_file_bytes': len(blob), 'startup': startup_report,
        'storage': {**previous['storage'], 'bytes': len(blob)},
        'native_test': 'pending for accessory attachment and new draw rows', 'hardware_test': 'not performed',
        'npc_draw': {**previous['npc_draw'], 'imports': draw_report,
            'owners': [{**r, 'patched_sha256': next(o['output_sha256'] for o in owners if o['vrom'] == r['vrom'])}
                       for r in previous['npc_draw']['owners']]},
        'accessory_runtime': {'code': compiled, 'owners': owners, 'imports': attachments,
            'package_vrom': f'{PACKAGE_VROM:08X}', 'package_ram': f'{PACKAGE_RAM:08X}',
            'package_bytes': PACKAGE_SIZE, 'package_sha256': sha256(package),
            'registry_offset': 0x1000, 'art_manifest_sha256': ART_SHA,
            'per_actor_allocation_bytes': 0, 'ordinary_heap_growth': 0,
            'matrix_lifetime': 'one draw call; graphics matrix lives in the current frame buffer',
            'gameplay_and_hardware': 'pending', 'move_in_enabled': []},
        'villager_assets': {**previous['villager_assets'], 'accessories_attached': True,
            'additional_draw_rows_installed': True},
        'sources': {**previous['sources'], **{p: sha256((ROOT/p).read_bytes()) for p in SOURCES}}}
    write_new(output/'animal-forest-v3-asset-loader.z64', image)
    write_new(output/'asset-loader.ups', patch)
    write_new(output/'build.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k: result[k] for k in ('output_sha256', 'patch_sha256', 'runtime_abi')}))
