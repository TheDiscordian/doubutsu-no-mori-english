"""Install all twenty imported melodies and four additive instruments in ABI 53."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum,
                   make_ups, sha256, u32, verified_rom)
from apply_translation import write_new
from v3_asset_loader import BLOB, BLOB_RAM, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_audio_runtime import TABLE
from v3_accessory_runtime import PACKAGE_RAM, PACKAGE_VROM, GUARD
from v3_speed_bag_sound_runtime import permanent_budget
from v3_villager_audio import NATIVE_HEADERS, extended_native_interpreter, extended_sequence_programs

ABI, RESIDENT, PACKAGE_BYTES = 53, 0xC000, 0xF000
BASE = ROOT/'build/v3-accessory-runtime-01'
BASE_SHA = '18af2aad25285b9ab5bc01a9a47ed9a79e9b819fb9fa3c63e81699118043c4fc'
AUDIO = ROOT/'build/v3-all-villager-audio-02'
AUDIO_SHA = '4899fbd32c0f7b954aa080d634b19f9e13c9f18843959616db52162726719333'
MELODY_START, MELODY_END = PACKAGE_RAM+0xC000, PACKAGE_RAM+PACKAGE_BYTES-16
FONT_OFFSET, WAVE_OFFSET = 0x80000, 0x84000
SOURCES = ('tools/v3_all_audio_runtime.py', 'tools/v3_villager_audio.py',
    'tools/v3_asset_loader.py', 'overlays/v3/melody.c', 'overlays/v3/melody_expanded.ld',
    'overlays/v3/startup.c', 'overlays/v3/startup.ld', 'overlays/v3/accessory.h')


def load_audio(directory=AUDIO):
    raw = (directory/'audio.json').read_bytes()
    if sha256(raw) != AUDIO_SHA:
        raise ValueError('Expected complete verified and compacted villager audio')
    report = json.loads(raw)
    resources = {}
    for row in report['villagers']:
        data = (directory/row['file']).read_bytes()
        if len(data) != row['bytes'] or sha256(data) != row['sha256']:
            raise ValueError('Changed complete donor melody')
        extended_sequence_programs(data)
        resources[row['file']] = data
    if (len(report['villagers']) != 20 or len(resources) != 20
            or {r['voice'] for r in report['villagers']} != set(range(260, 278)) | {285, 286}):
        raise ValueError('Incomplete or duplicate imported voice identities')
    for kind, filename in (('font', 'villager.soundfont.bin'), ('wave', 'villager.wave.bin')):
        data = (directory/filename).read_bytes()
        extension = report['instrument_extension']
        if len(data) != extension[kind+'_bytes'] or sha256(data) != extension[kind+'_sha256']:
            raise ValueError('Changed complete instrument or sample resource')
        resources[kind] = data
    return report, resources


def install_melodies(blob, previous, audio, resources, helper):
    package_offset = PACKAGE_VROM-BLOB
    package = bytearray(blob[package_offset:])
    if (len(package) != 0xC000 or sha256(package) != previous['accessory_runtime']['package_sha256']
            or any(package[0x500:0x1000]) or not 0 < len(helper) <= 0xB00):
        raise ValueError('Changed accessory package or occupied melody helper reservation')
    package.extend(bytes(PACKAGE_BYTES-len(package)))
    struct.pack_into('>I', package, 8, PACKAGE_BYTES)
    package[0x500:0x500+len(helper)] = helper
    package[-16:] = struct.pack('>4I', GUARD, GUARD, GUARD, GUARD)
    table = bytearray(43*8)
    old_table = bytearray(43*8)
    for row in previous['villager_audio']['imports']:
        at = (row['voice']-256)*8
        struct.pack_into('>II', old_table, at, int(row['ram'], 16), row['bytes'])
    if blob[TABLE:TABLE+len(table)] != old_table:
        raise ValueError('Changed existing melody table')
    cursor, installed = 0xC000, []
    for row in sorted(audio['villagers'], key=lambda r: r['voice']):
        data = resources[row['file']]
        if cursor % 16 or cursor+len(data) > PACKAGE_BYTES-16:
            raise ValueError('Imported melodies exceed the expanded resident package')
        package[cursor:cursor+len(data)] = data
        address = PACKAGE_RAM+cursor
        struct.pack_into('>II', table, (row['voice']-256)*8, address, len(data))
        installed.append({'id': row['id'], 'name': row['name'], 'voice': row['voice'],
                          'bytes': len(data), 'ram': f'{address:08X}', 'sha256': sha256(data)})
        cursor += len(data)
    result = bytearray(blob[:package_offset])+package
    result[TABLE:TABLE+len(table)] = table
    struct.pack_into('>I', result, 4, ABI)
    struct.pack_into('>4I', result, 0xF0, PACKAGE_VROM, PACKAGE_BYTES, zlib.crc32(package), PACKAGE_RAM)
    return result, installed, package


def install_audio_headers(base, code, blob, resources):
    files = by_vrom(base)
    before = permanent_budget(code)
    records = {}
    for kind, resource_kind, offset, source_vrom, expected in (
            ('bank', 'font', FONT_OFFSET, 0x019F0000, '00003be000003cf0020002ff53000000'),
            ('wave', 'wave', WAVE_OFFSET, 0x01A50000, '00046ea00005bfb00204000000000000')):
        data = resources[resource_kind]
        if len(blob) > offset or offset+len(data) > 0x200000:
            raise ValueError('Extended audio asset overlaps another V3 resource')
        blob.extend(bytes(offset-len(blob))+data)
        at = NATIVE_HEADERS[kind]+16+2*16-CODE_RAM
        old = bytes(code[at:at+16])
        if old != bytes.fromhex(expected):
            raise ValueError('Changed original voice audio entry')
        initializer_base = files[source_vrom].pstart
        physical = files[BLOB].pstart+offset
        if files[source_vrom].pend or not initializer_base < physical <= len(base)-len(data):
            raise ValueError('Expanded audio needs bounded direct cartridge addresses')
        new = bytearray(old)
        struct.pack_into('>II', new, 0, physical-initializer_base, len(data))
        if kind == 'bank': new[12] = 88
        code[at:at+16] = new
        records[kind] = {'vrom': BLOB+offset, 'blob_offset': offset, 'physical_rom': physical,
            'bytes': len(data), 'sha256': sha256(data), 'initializer_vrom': source_vrom,
            'initializer_base': initializer_base, 'header_address': CODE_RAM+at,
            'header_before': old.hex(), 'header_after': new.hex(),
            'source_offset': physical-initializer_base}
    after = permanent_budget(code)
    if before['conservative_spare'] != 608 or after['conservative_spare'] != 32:
        raise ValueError('Unexpected complete permanent audio budget')
    return records, before, after


def compose(base, blob, module, code):
    if sha256(base) != BASE_SHA:
        raise ValueError('Expected exact ABI-52 accessory cartridge')
    files = by_vrom(base)
    entry = files[BLOB]
    end = max(e.pend or e.pstart+e.size for e in files.values() if e.pstart != 0xFFFFFFFF)
    if (entry.pend or entry.pstart+entry.size != end or len(blob) % 16
            or not entry.size < len(blob) <= 0x200000 or entry.pstart+len(blob) > len(base)
            or any(base[end:entry.pstart+len(blob)])):
        raise ValueError('Expanded V3 file cannot safely extend its current physical allocation')
    if any(e.vstart < BLOB+len(blob) and BLOB < e.vend for v, e in files.items() if v != BLOB):
        raise ValueError('Expanded audio collides with another virtual resource')
    image = bytearray(base)
    for vrom, data in ((MODULE, module), (CODE_VROM, code)):
        owner = files[vrom]
        if owner.pend or len(data) != owner.size:
            raise ValueError('Unexpected changed code owner size or compression')
        image[owner.pstart:owner.pstart+owner.size] = data
    image[entry.pstart:entry.pstart+len(blob)] = blob
    struct.pack_into('>4I', image, DMA_START+entry.index*16, BLOB, BLOB+len(blob), entry.pstart, 0)
    fix_checksum(image)
    return bytes(image)


def build(output, base_directory=BASE, audio_directory=AUDIO):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Generated resources belong in ignored build/')
    base = (base_directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('Changed current accessory cartridge')
    previous = json.loads((base_directory/'build.json').read_text())
    files = by_vrom(base)
    audio, resources = load_audio(audio_directory)
    output.mkdir(parents=True, exist_ok=False)
    helper, compiled = compile_part('melody_expanded', output/'melody',
        primary_source='overlays/v3/melody.c', defines=(
            f'AF_V3_MELODY_BEGIN=0x{MELODY_START:X}u', f'AF_V3_MELODY_END=0x{MELODY_END:X}u'))
    blob, imports, package = install_melodies(files[BLOB].extract(base), previous, audio, resources, helper)
    code = bytearray(files[CODE_VROM].extract(base))
    extended_native_interpreter(lambda a, n: code[a-CODE_RAM:a-CODE_RAM+n])
    for address, name in ((0x800FCEEC, 'af_v3_melody_start'), (0x800FD0D4, 'af_v3_melody_count')):
        expected = (0x08000000 | (previous['asset']['symbols'][name] >> 2 & 0x3FFFFFF), 0)
        if struct.unpack_from('>II', code, address-CODE_RAM) != expected:
            raise ValueError('Changed installed melody entry')
        struct.pack_into('>II', code, address-CODE_RAM,
                         0x08000000 | (compiled['symbols'][name] >> 2 & 0x3FFFFFF), 0)
    audio_files, before_budget, after_budget = install_audio_headers(base, code, blob, resources)
    startup, startup_report = compile_part('startup', output/'startup', defines=(
        f'AF_V3_BLOB_SIZE={RESIDENT}', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_BYTES}'))
    module = bytearray(files[MODULE].extract(base))
    old_size = previous['startup']['bytes']
    if (sha256(module[STARTUP:STARTUP+old_size]) != previous['startup']['sha256']
            or any(module[STARTUP+old_size:CONFIG]) or len(startup) > CONFIG-STARTUP):
        raise ValueError('Changed or overflowing current startup helper')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, RESIDENT, zlib.crc32(blob[:RESIDENT]), ABI)
    image = compose(base, blob, module, code)
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Complete audio cartridge reconstruction failed')
    report = {**previous, 'build': 'v3-complete-villager-audio', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_sha256': sha256(blob), 'blob_file_bytes': len(blob), 'startup': startup_report,
        'storage': {**previous['storage'], 'bytes': len(blob)},
        'native_test': 'pending for complete villager audio', 'hardware_test': 'not performed',
        'accessory_runtime': {**previous['accessory_runtime'], 'package_bytes': PACKAGE_BYTES,
            'package_sha256': sha256(package), 'additional_audio_bytes': PACKAGE_BYTES-0xC000},
        'villager_audio': {**previous['villager_audio'], 'imports': imports, 'conversion': audio,
            'native_instruments_and_samples_reused': False,
            'original_instruments_retained': 83, 'new_instruments_installed': 4,
            'full_native_playback_test': 'pending for expanded sources/instruments'},
        'complete_villager_audio': {'code': compiled, 'files': audio_files,
            'audio_manifest_sha256': AUDIO_SHA, 'before_budget': before_budget, 'after_budget': after_budget,
            'resident_begin': f'{MELODY_START:08X}', 'resident_end': f'{MELODY_END:08X}',
            'ordinary_heap_growth': 0, 'saved_formats_changed': False, 'move_in_enabled': []},
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
