"""Install every donor villager's full text without enabling incomplete move-ins."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from npc_mail_capture import ALIAS_HASH
from npc_mail_names import unpack_aliases
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_import_catalog import read_donor
from v3_registry import REGISTRY_VERSION, VILLAGERS, villager_actor
from v3_save_runtime import PROFILE_OFFSET, profile_bytes
from v3_villager_defaults import imported_outfit
from v3_villager_text import DATA, STRIDE, metadata, read_text_donor

ABI, RESIDENT, PACKAGE_BYTES = 54, 0xC000, 0xF000
BASE = ROOT/'build/v3-all-audio-runtime-01'
BASE_SHA = '0e8335fa88c5da9800d6c38adf5c1d8fc08ebe86680bcaa88d2fbff5fbc3ff4f'
DONOR = ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'
SOURCES = ('tools/v3_all_villager_text.py', 'tools/v3_villager_text.py',
           'tools/v3_villager_defaults.py', 'tools/v3_save_runtime.py',
           'tools/v3_registry.py', 'overlays/v3/villager.c',
           'overlays/v3/villager_readers.c', 'overlays/v3/save_codec.c',
           'overlays/v3/startup.c', 'overlays/v3/startup.ld')


def compatibility_aliases(base, records):
    """Check actual mail aliases and saved name fields before using six-byte keys."""
    files = by_vrom(base)
    creator = files[0x03200000].extract(base)
    start = creator.find(b'AFNA')
    if start < 0 or creator.find(b'AFNA', start+1) >= 0:
        raise ValueError('Missing or ambiguous installed native name aliases')
    native = unpack_aliases(creator[start:start+6368], ALIAS_HASH)
    original_keys = {r.key for r in native}
    saved = files[0xE04000].extract(base)
    original_keys.update(saved[8+6*i:14+6*i] for i in range(216))
    full_names = {r.name for r in native}
    seen = set()
    rows = []
    for index in range(20):
        row = records[index*STRIDE:(index+1)*STRIDE]
        name, key = row[8:16], row[8:14]
        if key in original_keys or key in seen or name in full_names:
            raise ValueError('Imported name conflicts with a native or imported saved alias')
        seen.add(key)
        rows.append({'actor_id': f'{struct.unpack_from(">H", row)[0]:04X}',
                     'full_name_hex': name.hex(), 'saved_name_hex': key.hex(),
                     'display_restores_full_name': True})
    return {'native_alias_sha256': ALIAS_HASH, 'native_alias_rows': len(native),
            'aliases': rows, 'collisions': 0, 'saved_field_bytes': 6,
            'display_field_bytes': 8}


def install_metadata(base, previous, native, donor, first, symbols):
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    old_table = bytes(blob[DATA:DATA+20*STRIDE])
    records, rows = metadata(native, donor, first, symbols, all_villagers=True)
    aliases = compatibility_aliases(base, records)
    text_report = copy.deepcopy(previous['villager_text'])
    text_report['imports'] = rows
    prefix = bytearray(blob[:RESIDENT])
    prefix[DATA:DATA+len(records)] = records
    imported_outfit(prefix, text_report, blob[0xF000:0xF220], blob[0x2820:0x2840],
                    previous['clothing']['imports'][0])
    old_rows = {int(row['actor_id'], 16): row for row in previous['villager_text']['imports']}
    if set(old_rows) != {0xE0EA, 0xE0ED}:
        raise ValueError('Changed installed pilot text identities')
    for index in range(20):
        actor, at = 0xE0DA+index, index*STRIDE
        old = old_table[at:at+STRIDE]
        if actor in old_rows:
            if (sha256(old) != old_rows[actor]['record_sha256']
                    or old != prefix[DATA+at:DATA+at+STRIDE]):
                raise ValueError('Complete text would alter an existing pilot default')
        elif any(old):
            raise ValueError('Unexpected installed non-pilot metadata')
    profile = bytes.fromhex(previous['save_runtime']['profile_hex'])
    if len(profile) != 192 or prefix[PROFILE_OFFSET:PROFILE_OFFSET+192] != profile:
        raise ValueError('Changed selected import profile')
    identities = [{'actor_id': f'{villager_actor(i):04X}', 'registry_version': REGISTRY_VERSION}
                  for i in sorted(VILLAGERS)]
    pilot_profile = profile_bytes([r for r in identities if int(r['actor_id'], 16) in old_rows], [])[:32]
    if profile[:32] != pilot_profile:
        raise ValueError('Previous profile does not match the installed text dependencies')
    expanded = profile_bytes(identities, [])[:32]+profile[32:]
    prefix[PROFILE_OFFSET:PROFILE_OFFSET+192] = expanded
    struct.pack_into('>I', prefix, 4, ABI)
    if prefix[0x1E60:0x1E74] != bytes(20):
        raise ValueError('Incomplete villagers must not be eligible for ordinary move-ins')
    blob[:RESIDENT] = prefix
    text_report.update({'metadata_sha256': sha256(prefix[DATA:DATA+20*STRIDE]),
        'compatibility_aliases': aliases, 'native_test': 'pending for complete roster metadata',
        'remaining': ['two actual aloha-shirt dependencies', 'islander house dependencies',
                      'explicit islander town behaviour', 'ordinary move-in and persistence']})
    return blob, text_report, expanded


def compose(base, blob, module):
    if sha256(base) != BASE_SHA:
        raise ValueError('Expected complete ABI-53 audio cartridge')
    files = by_vrom(base)
    image = bytearray(base)
    for vrom, data in ((BLOB, blob), (MODULE, module)):
        entry = files[vrom]
        if entry.pend or len(data) != entry.size:
            raise ValueError('Complete text must not move or resize native resources')
        image[entry.pstart:entry.pstart+entry.size] = data
    fix_checksum(image)
    return bytes(image)


def build(output, base_directory=BASE, donor_path=DONOR):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Generated resources belong in ignored build/')
    base = (base_directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('Changed current complete audio cartridge')
    previous = json.loads((base_directory/'build.json').read_text())
    if previous['output_sha256'] != BASE_SHA or previous['runtime_abi'] != 53:
        raise ValueError('Changed current input build receipt')
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    donor = read_donor(donor_path)
    first = read_text_donor(donor_path)
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    blob, text_report, profile = install_metadata(base, previous, native, donor, first, symbols)
    output.mkdir(parents=True, exist_ok=False)
    startup, compiled = compile_part('startup', output/'startup', defines=(
        f'AF_V3_BLOB_SIZE={RESIDENT}', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_BYTES}'))
    module = bytearray(by_vrom(base)[MODULE].extract(base))
    old_size = previous['startup']['bytes']
    if (sha256(module[STARTUP:STARTUP+old_size]) != previous['startup']['sha256']
            or any(module[STARTUP+old_size:CONFIG]) or len(startup) > CONFIG-STARTUP):
        raise ValueError('Changed or overflowing startup code')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, RESIDENT, zlib.crc32(blob[:RESIDENT]), ABI)
    image = compose(base, blob, module)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Complete villager text reconstruction failed')
    report = {**previous, 'build': 'v3-complete-villager-text', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_sha256': sha256(blob), 'startup': compiled, 'villager_text': text_report,
        'save_runtime': {**previous['save_runtime'], 'profile_hex': profile.hex(),
            'profile_sha256': sha256(profile)},
        'save_warning': 'This build adds all twenty villager text dependencies to the saved profile. '
            'Earlier pilot-only builds and V2 must not load its saves. Keep backups. '
            'The unchanged codec accepts the preceding subset profile; ordinary cross-build loading is not verified.',
        'complete_villager_text': {'installed_names': 20, 'installed_default_phrases': 20,
            'source_growth_retained': True, 'new_town_behaviour_enabled': False,
            'pending_outfit_ids': ['241A', '241B'], 'resident_growth_bytes': 0,
            'profile_before': previous['save_runtime']['profile_hex'], 'profile_after': profile.hex(),
            'saved_formats_changed': False, 'selected_dependencies_changed': True,
            'ordinary_move_in_or_persistence': 'not established'},
        'native_test': 'pending for complete villager text; new-instrument playback remains unresolved',
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
    print(json.dumps({k: result[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
