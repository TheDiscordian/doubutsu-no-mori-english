"""Repair callback-owned tent DMA without changing content, saves, or either patcher."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import by_vrom, sha256, fix_checksum, verified_rom, make_ups, apply_ups
from apply_translation import write_new
from v3_asset_loader import ROOT, BLOB, MODULE, CONFIG, compile_part
from v3_import_storage import DEFINES, ROOM, ROOM_RAM, replace_checked, jump

BASE = ROOT / 'build/v3-tent-model-runtime-01'
BASE_SHA = '29f5d1e6760dbfb4acc015f2a3482470fdbd43f1ce6ef03d156ecb1902ddab6a'
REPORT_SHA = '7d177af03b8ad4a19796c7034fc3a097a705b8d3654ba050ec8f697c7915b693'
SOURCES = ('tools/v3_tent_model_loader.py', 'overlays/v3/furniture.c',
    'overlays/v3/furniture_expanded.ld', 'overlays/v3/furniture_entry.S',
    'overlays/v3/sparse_furniture.h', 'overlays/v3/construction.h',
    'overlays/v3/furniture_tables.h', 'overlays/v3/furniture_banks.h')


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
    if (sha256(base), sha256(raw)) != (BASE_SHA, REPORT_SHA):
        raise ValueError('Changed complete tent integration source')
    prior = json.loads(raw)
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    expanded = copy.deepcopy(prior['furniture']['expanded_tables'])
    old = expanded['expanded_code']
    if (prior['runtime_abi'] != 69 or sha256(blob) != prior['blob_sha256']
            or sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256']
            or any(blob[0x5800 + old['bytes']:0x6000])):
        raise ValueError('Changed complete furniture-loader reservation')
    output.mkdir(parents=True)
    helper, compiled = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=DEFINES + ('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
            'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_EXPANDED_BANKS=1', 'AF_V3_TENT_MODEL=1'),
        primary_source='overlays/v3/furniture.c', extra_sources=('overlays/v3/furniture_entry.S',))
    if len(helper) > 0x800:
        raise ValueError('Tent loader exceeds the existing code reservation')
    blob[0x5800:0x6000] = helper + bytes(0x800 - len(helper))
    for row in expanded['public_entries']:
        target = compiled['symbols'][row['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, row['entry'] - 0x80460000, bytes.fromhex(row['after']), after)
        row.update(before=row['after'], after=after.hex(), target=target)
    room = bytearray(files[ROOM].extract(base))
    banks = copy.deepcopy(prior['furniture']['bank_pool'])
    hook = banks['hook']
    if sha256(room) != banks['output_owner_sha256']:
        raise ValueError('Changed native model-bank owner')
    before = bytes.fromhex(hook['after'])
    if struct.unpack_from('>I', before, 4)[0] != jump(old['symbols']['af_v3_furniture_secure_banks'], link=True):
        raise ValueError('Unbound native bank-allocation call')
    after = before[:4] + struct.pack('>I', jump(compiled['symbols']['af_v3_furniture_secure_banks'], link=True)) + before[8:]
    replace_checked(room, hook['address'] - ROOM_RAM, before, after)
    hook.update(before=before.hex(), after=after.hex())
    banks.update(source_owner_sha256=banks['output_owner_sha256'], output_owner_sha256=sha256(room))
    expanded.update(expanded_code=compiled, output_sha256=sha256(room))
    # The owner currently has its own allocation, but preserve parent-resource
    # accounting if a later supported layout places that owner inside the blob.
    inside = files[ROOM].pstart - files[BLOB].pstart
    if 0 <= inside <= len(blob) - len(room):
        blob[inside:inside + len(room)] = room
    module = bytearray(files[MODULE].extract(base))
    if struct.unpack_from('>4I', module, CONFIG) != (BLOB, 0xC000, zlib.crc32(files[BLOB].extract(base)[:0xC000]), 69):
        raise ValueError('Changed complete current loader checksum descriptor')
    struct.pack_into('>I', module, CONFIG + 8, zlib.crc32(blob[:0xC000]))
    result = bytearray(base)
    for v, data in ((BLOB, blob), (ROOM, room), (MODULE, module)):
        entry = files[v]
        if entry.pend or len(data) != entry.size:
            raise ValueError('Loader repair unexpectedly changes a resource allocation')
        result[entry.pstart:entry.pstart + len(data)] = data
    fix_checksum(result)
    result = bytes(result)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result or by_vrom(result) != files:
        raise ValueError('Tent loader changes the directory or fails patch reconstruction')
    report = copy.deepcopy(prior)
    report.update(build='v3-tent-model-loader', input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        native_test='pending actual current callback-owned model DMA')
    report['furniture'].update(expanded_tables=expanded, bank_pool=banks)
    report['tent_model']['loader'] = {'code_sha256': sha256(helper), 'code_bytes': len(helper),
        'accepts_complete_callback_object': True, 'item_dependent_dma_callback': False,
        'only_added_identity': '336C', 'only_added_vtable': '80483700',
        'saved_format_changed': False, 'saved_profile_changed': False,
        'runtime_abi_changed': False, 'web_patcher_enabled': False}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({'sha256': report['output_sha256'], 'loader': report['tent_model']['loader']}))
