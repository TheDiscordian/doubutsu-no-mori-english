"""Install real aloha garments and complete islander outfits without move-ins."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_clothing import convert
from v3_import_catalog import read_donor
from v3_registry import clothing_slot
from v3_villager_text import read_text_donor

ABI, RESIDENT, PACKAGE_OFFSET, PACKAGE_BYTES = 55, 0xC000, 0x70000, 0xF000
BASE = ROOT/'build/v3-all-villager-text-01'
BASE_SHA = 'eb611e2bade707270d8c72cd11349b344fecb3cd262918c31a4ffc1303ac8101'
DONOR = ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'
SOURCES = ('tools/v3_aloha_runtime.py', 'tools/v3_clothing.py', 'tools/v3_registry.py',
           'tools/v3_asset_loader.py', 'overlays/v3/clothing_roster.c',
           'overlays/v3/clothing_roster.S', 'overlays/v3/clothing_roster.ld', 'overlays/v3/clothing.h',
           'overlays/v3/startup.c', 'overlays/v3/startup.ld')


def install(blob, previous, native, donor, first, symbols, helper, compiled):
    if len(blob) != 0xE1D50 or previous['runtime_abi'] != 54:
        raise ValueError('Expected complete text/audio storage')
    original = bytes(blob)
    blob = bytearray(blob)
    clothing = copy.deepcopy(previous['clothing'])
    text = copy.deepcopy(previous['villager_text'])
    profile = bytearray.fromhex(previous['save_runtime']['profile_hex'])
    if (len(profile) != 192 or blob[0x20:0xE0] != profile
            or any(blob[0x2840:0x2900]) or blob[0x1E60:0x1E74] != bytes(20)):
        raise ValueError('Changed metadata reservation, profile, or move-in flags')
    cherry, cherry_record, _ = convert(native, first, donor['rel'], symbols)
    if cherry != blob[0xF000:0xF220] or cherry_record != blob[0x2820:0x2840]:
        raise ValueError('The existing cherry shirt must remain intact')
    converted = {}
    for slot, donor_item in enumerate((0x241A, 0x241B), 1):
        resource, record, row = convert(native, first, donor['rel'], symbols, donor_item=donor_item)
        item, index, vrom = clothing_slot(donor_item)
        if row['price'] != 0 or len(resource) != 544 or len(record) != 32:
            raise ValueError('Changed exclusive aloha-shirt resource or donor price')
        offset = vrom-BLOB
        if len(blob) > offset or offset+len(resource) > 0x200000:
            raise ValueError('Aloha artwork overlaps installed resources')
        blob.extend(bytes(offset-len(blob))+resource)
        blob[0x2820+slot*32:0x2840+slot*32] = record
        bit = item&255
        if profile[160+(bit>>3)] & 1 << (bit&7):
            raise ValueError('Unexpected existing aloha profile bit')
        profile[160+(bit>>3)] |= 1 << (bit&7)
        row.update({'save_profile_installed': True, 'metadata_ram': f'{0x80462820+slot*32:08X}',
                    'ordinary_shop_stock_added': False,
                    'remaining': ['mannequin/display', 'catalogue listing', 'ordinary acquisition and persistence']})
        clothing['imports'].append(row)
        converted[donor_item] = (resource, record, row)
    blob[0x20:0xE0] = profile
    defaults = []
    for row in text['imports']:
        actor = int(row['actor_id'], 16)
        at = 0x2C00+(actor-0xE0DA)*32
        old = bytes(blob[at:at+32])
        if sha256(old) != row['record_sha256']:
            raise ValueError('Changed installed full-name/default metadata')
        if actor in (0xE0EA, 0xE0ED):
            continue
        donor_item = int(row['donor_clothing_id'], 16)
        if (donor_item not in converted or old[6:8] != b'\x02\x01' or old[30:] != bytes(2)
                or row['initial_defaults_applied']):
            raise ValueError('Unexpected islander outfit or growth adaptation')
        resource, record, garment = converted[donor_item]
        identity = row['clothing_identity']
        if (sha256(resource[:512]) != identity['converted_texture_sha256']
                or sha256(resource[512:]) != identity['converted_palette_sha256']):
            raise ValueError('Aloha outfit differs from the actual villager dependency')
        item = int(garment['item_id'], 16)
        struct.pack_into('>H', blob, at+30, item)
        row.update({'applied_clothing_id': garment['item_id'], 'clothing_applied': True,
                    'initial_defaults_applied': True, 'record_sha256': sha256(blob[at:at+32])})
        defaults.append({'actor_id': row['actor_id'], 'donor_item_id': f'{donor_item:04X}',
                         'item_id': garment['item_id'], 'before_sha256': sha256(old),
                         'after_sha256': row['record_sha256']})
    if len(defaults) != 18:
        raise ValueError('Incomplete islander starting-outfit coverage')
    code_offset = PACKAGE_OFFSET+0xA00
    if (not 0 < len(helper) <= 0x600 or any(blob[code_offset:PACKAGE_OFFSET+0x1000])
            or sha256(original[PACKAGE_OFFSET:PACKAGE_OFFSET+PACKAGE_BYTES])
            != previous['accessory_runtime']['package_sha256']):
        raise ValueError('Clothing helper overlaps existing accessory/audio code')
    blob[code_offset:code_offset+len(helper)] = helper
    hooks = []
    for address, offset, before, name in (
            (0x804608F0, 0x8F0, '2ca3000210600025', 'af_v3_roster_clothing_source'),
            (0x80460B8C, 0xB8C, '1080001e00000000', 'af_v3_roster_clothing_index'),
            (0x80464084, 0x4084, '2483dc002c630100', 'af_v3_roster_outfit_ready'),
            (0x8046D7D8, 0xFBD8, '240234bf14820013', 'af_v3_roster_clothing_record')):
        target = compiled['symbols'][name+'_bridge']
        if (blob[offset:offset+8] != bytes.fromhex(before) or target & 3
                or not 0x80473A00 <= target < 0x80473A00+len(helper)):
            raise ValueError('Changed public clothing dependency entry')
        after = struct.pack('>II', 0x08000000 | (target>>2 & 0x3FFFFFF), 0)
        blob[offset:offset+8] = after
        hooks.append({'address': f'{address:08X}', 'blob_offset': offset,
                      'target': f'{target:08X}', 'before': before, 'after': after.hex(), 'helper': name})
    # The old compiler folded find_clothing's sole possible result to 80462820.
    # Preserve the returned record before the name loop reuses v0, and use the
    # actual selected record's price rather than the former single-shirt row.
    readers = []
    for address, before, after in (
            (0x8046D93C, 0x00000000, 0x00401825),  # move v1,v0
            (0x8046D94C, 0x3C038046, 0x00000000),
            (0x8046D954, 0x24632820, 0x00000000),
            (0x8046DB68, 0x3C028046, 0x00000000),
            (0x8046DB6C, 0x94422828, 0x94420008)):
        offset = 0xF400+address-0x8046D000
        if struct.unpack_from('>I', blob, offset)[0] != before:
            raise ValueError('Changed compiled single-shirt name or price reader')
        struct.pack_into('>I', blob, offset, after)
        readers.append({'address': f'{address:08X}', 'blob_offset': offset,
                        'before': f'{before:08x}', 'after': f'{after:08x}'})
    # Only the item predicate and its name/price consumers change in this resource.
    # Preserve every save-code instruction and all existing public entry addresses.
    extra = previous['clothing']['save_extension']
    size = extra['resource_bytes']
    if (sha256(original[0xF400:0xF400+size]) != extra['resource_sha256']
            or struct.unpack_from('>4I', original, 0xE0) !=
            (0x0220F400, size, zlib.crc32(original[0xF400:0xF400+size]), 0x8046D000)):
        raise ValueError('Changed complete save/item resource descriptor')
    updated = bytes(blob[0xF400:0xF400+size])
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(updated))
    clothing['save_extension']['resource_sha256'] = sha256(updated)
    package = bytes(blob[PACKAGE_OFFSET:PACKAGE_OFFSET+PACKAGE_BYTES])
    struct.pack_into('>I', blob, 0xF8, zlib.crc32(package))
    struct.pack_into('>I', blob, 4, ABI)
    text['metadata_sha256'] = sha256(blob[0x2C00:0x2E80])
    text['remaining'] = ['islander house dependencies', 'explicit islander town behaviour',
                         'ordinary move-in and persistence']
    text['native_test'] = 'pending for eighteen complete initial outfits; full-name/phrase checks retained'
    return blob, clothing, text, bytes(profile), {'hooks': hooks, 'reader_fixes': readers, 'code': compiled,
        'defaults': defaults, 'installed_items': ['34BF', '341A', '341B'],
        'resident_growth_bytes': 0, 'ordinary_heap_growth_bytes': 0,
        'saved_formats_changed': False, 'selected_dependencies_changed': True,
        'ordinary_shop_stock_changed': False, 'move_in_enabled': [],
        'save_item_resource_sha256': sha256(updated), 'package_sha256': sha256(package),
        'native_test': 'pending'}


def compose(base, blob, module):
    if sha256(base) != BASE_SHA:
        raise ValueError('Expected complete ABI-54 text cartridge')
    files = by_vrom(base)
    entry = files[BLOB]
    end = max(e.pend or e.pstart+e.size for e in files.values() if e.pstart != 0xFFFFFFFF)
    if (entry.pend or entry.pstart+entry.size != end or len(blob)%16
            or not entry.size < len(blob) <= 0x200000 or entry.pstart+len(blob)>len(base)
            or any(base[end:entry.pstart+len(blob)])):
        raise ValueError('Aloha resources cannot extend the final physical allocation safely')
    if any(e.vstart < BLOB+len(blob) and BLOB < e.vend for v,e in files.items() if v!=BLOB):
        raise ValueError('Aloha resources overlap another virtual file')
    owner = files[MODULE]
    if owner.pend or len(module)!=owner.size:
        raise ValueError('Changed translation-module size or compression')
    image = bytearray(base)
    image[owner.pstart:owner.pstart+owner.size] = module
    image[entry.pstart:entry.pstart+len(blob)] = blob
    struct.pack_into('>4I', image, DMA_START+entry.index*16, BLOB, BLOB+len(blob), entry.pstart, 0)
    fix_checksum(image)
    return bytes(image)


def build(output, base_directory=BASE, donor_path=DONOR):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Generated resources belong in ignored build/')
    base = (base_directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    previous = json.loads((base_directory/'build.json').read_text())
    if sha256(base)!=BASE_SHA or previous['output_sha256']!=BASE_SHA:
        raise ValueError('Changed complete-text input cartridge')
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    donor, first = read_donor(donor_path), read_text_donor(donor_path)
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    output.mkdir(parents=True, exist_ok=False)
    helper, compiled = compile_part('clothing_roster', output/'clothing_roster',
                                    extra_sources=('overlays/v3/clothing_roster.S',))
    files = by_vrom(base)
    blob, clothing, text, profile, installed = install(files[BLOB].extract(base), previous,
        native, donor, first, symbols, helper, compiled)
    startup, startup_report = compile_part('startup', output/'startup', defines=(
        f'AF_V3_BLOB_SIZE={RESIDENT}', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_BYTES}'))
    module = bytearray(files[MODULE].extract(base))
    old_size = previous['startup']['bytes']
    if (sha256(module[STARTUP:STARTUP+old_size])!=previous['startup']['sha256']
            or any(module[STARTUP+old_size:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed or overflowing startup code')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, RESIDENT, zlib.crc32(blob[:RESIDENT]), ABI)
    image = compose(base, blob, module)
    patch = make_ups(native, image)
    if apply_ups(native, patch)!=image:
        raise ValueError('Aloha cartridge reconstruction failed')
    report = {**previous, 'build': 'v3-aloha-outfits', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_sha256': sha256(blob), 'blob_file_bytes': len(blob), 'startup': startup_report,
        'storage': {**previous['storage'], 'bytes': len(blob)},
        'clothing': clothing, 'villager_text': text, 'aloha_outfits': installed,
        'accessory_runtime': {**previous['accessory_runtime'], 'package_sha256': installed['package_sha256']},
        'save_runtime': {**previous['save_runtime'], 'profile_hex': profile.hex(), 'profile_sha256': sha256(profile)},
        'complete_villager_text': {**previous['complete_villager_text'], 'pending_outfit_ids': []},
        'save_warning': 'This build adds red and blue aloha-shirt dependencies. Earlier builds lacking '
            'these garments reject its saves. V2 must not load imported saves. Preserve backups. '
            'Ordinary cross-build loading is not newly verified.',
        'native_test': 'pending for aloha artwork, readers, and full defaults; new-instrument playback unresolved',
        'sources': {**previous['sources'], **{p: sha256((ROOT/p).read_bytes()) for p in SOURCES}}}
    write_new(output/'animal-forest-v3-asset-loader.z64', image)
    write_new(output/'asset-loader.ups', patch)
    write_new(output/'build.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({k: result[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
