"""Install complete fire sounds with coordinated audio capacity and wave storage."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, fix_checksum,
    sha256, u32, verified_rom, make_ups, apply_ups)
from apply_translation import write_new
from v3_asset_loader import ROOT, BLOB
from v3_import_storage import END, replace_checked
from v3_fire_audio import BASE, BASE_SHA, REPORT_SHA, NATIVE_VROMS
from v3_villager_audio import NATIVE_HEADERS, header_entry, span

AUDIO = ROOT / 'build/v3-fire-audio-02'
AUDIO_SHA = 'fe3a4bd43eb5118960585719c0dbec0ccd187c276c1a9c263d2df6794f4f3746'
WAVE_PHYSICAL = 0x03800000
HEAP_SETTINGS = (0x47E00, 0x1DC00, 0x1AC00)


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
    audio_raw = (AUDIO / 'audio.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(audio_raw)) != (BASE_SHA, REPORT_SHA, AUDIO_SHA):
        raise ValueError('Changed fire audio or complete current source cartridge')
    prior, audio = json.loads(raw), json.loads(audio_raw)
    if audio['converter_sha256'] != sha256((ROOT / 'tools/v3_fire_audio.py').read_bytes()):
        raise ValueError('Fire audio converter no longer matches the reviewed output')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files = by_vrom(base)
    code = bytearray(files[CODE_VROM].extract(base))
    read = lambda at, size: span(code, at - CODE_RAM, size)
    data = {}
    for kind, identity in audio['resources'].items():
        value = (AUDIO / f'fire.{kind}.bin').read_bytes()
        if (len(value), sha256(value)) != (identity['bytes'], identity['sha256']):
            raise ValueError('Changed complete converted fire resource')
        data[kind] = value
    if set(data) != {'seq', 'bank', 'wave'}:
        raise ValueError('Incomplete fire resource set')
    if (prior['runtime_abi'] != 69 or len(base) != 0x4000000
            or sha256(files[BLOB].extract(base)) != prior['blob_sha256']):
        raise ValueError('Changed current storage or ABI')

    patches = []
    def patch(at, before, after):
        replace_checked(code, at - CODE_RAM, before, after)
        if before != after:
            patches.append({'address': at, 'before': before.hex(), 'after': after.hex()})

    # Both actual malloc arguments must grow along with fixed/permanent pools.
    # Session/cache capacity and the fixed non-permanent remainder stay intact.
    patch(0x800D28D8, bytes.fromhex('34847A00'), bytes.fromhex('34847E00'))
    patch(0x800D28F8, bytes.fromhex('34A57A00'), bytes.fromhex('34A57E00'))
    patch(0x80119A44, struct.pack('>3I', 0x47A00, 0x1D800, 0x1A800), struct.pack('>3I', *HEAP_SETTINGS))

    # The old wave file has no adjacent space. Preserve its entire contents,
    # append only the additional wave-five samples, and move the file as a unit.
    wave_file = files[NATIVE_VROMS['wave']]
    wave_source = wave_file.extract(base)
    wh = bytes.fromhex(audio['original_headers']['wave'])
    start, size = struct.unpack_from('>II', wh)
    if (header_entry(read, NATIVE_HEADERS['wave'], 5) != wh or wave_file.pend
            or start + size != len(wave_source) or data['wave'][:size] != wave_source[start:]):
        raise ValueError('Wave-five append does not preserve the complete current wave file')
    waves = wave_source + data['wave'][size:]
    if (wave_file.vstart + len(waves) > 0x02000000 or WAVE_PHYSICAL + len(waves) > len(base)
            or any(base[WAVE_PHYSICAL:WAVE_PHYSICAL + len(waves)])
            or any(e.pstart < WAVE_PHYSICAL + len(waves) and WAVE_PHYSICAL < (e.pend or e.pstart + e.size)
                   for e in files.values() if e.pstart != 0xFFFFFFFF)):
        raise ValueError('Complete relocated wave file exceeds its physical or virtual reservation')
    # Native header relocation uses unsigned ADDU. External wave two keeps its
    # absolute physical address even though the new group base is above it.
    if read(0x800EA944, 12) != bytes.fromhex('8CD800100305C821ACD90010'):
        raise ValueError('Native audio headers no longer use the reviewed unsigned base addition')
    headers = []
    count = struct.unpack('>H', read(NATIVE_HEADERS['wave'], 2))[0]
    if count != 6:
        raise ValueError('Changed native wave resource count')
    for index in range(count):
        before = header_entry(read, NATIVE_HEADERS['wave'], index)
        offset, length = struct.unpack_from('>II', before)
        if not length or before[8:10] != bytes((2, 4)):
            raise ValueError('Changed native streamed-wave medium or cache policy')
        physical_before = (wave_file.pstart + offset) & 0xFFFFFFFF
        outside = not (0 <= offset <= len(wave_source) - length)
        if outside != (index == 2) or physical_before + length > len(base):
            raise ValueError('Unexpected external current waveform binding')
        physical = physical_before if outside else WAVE_PHYSICAL + offset
        new_size = len(data['wave']) if index == 5 else length
        after = bytearray(before)
        struct.pack_into('>II', after, 0, (physical - WAVE_PHYSICAL) & 0xFFFFFFFF, new_size)
        address = NATIVE_HEADERS['wave'] + 16 + index * 16
        patch(address, before, after)
        headers.append({'index': index, 'address': address, 'before': before.hex(), 'after': after.hex(),
            'physical_before': physical_before, 'physical': physical, 'bytes': new_size,
            'external_resource_retained': outside})
    old_load = struct.pack('>II', 0x3C0E0000 | ((wave_file.pstart + 0x8000) >> 16),
                           0x25CE0000 | (wave_file.pstart & 0xFFFF))
    new_load = struct.pack('>II', 0x3C0E0000 | ((WAVE_PHYSICAL + 0x8000) >> 16),
                           0x25CE0000 | (WAVE_PHYSICAL & 0xFFFF))
    patch(0x800D28DC, old_load, new_load)

    # The much smaller sequence/font fit the existing import resource. These
    # are streamed through native audio headers, not loaded as resident code.
    blob = bytearray(files[BLOB].extract(base))
    resources = {}
    for kind, index in (('seq', 199), ('bank', 140)):
        payload = data[kind]
        blob.extend(bytes(-len(blob) % 16))
        at = len(blob)
        blob.extend(payload)
        physical = files[BLOB].pstart + at
        old = header_entry(read, NATIVE_HEADERS[kind], index)
        if old.hex() != audio['original_headers'][kind]:
            raise ValueError('Changed current fire sequence/font header')
        new = bytearray(old)
        struct.pack_into('>II', new, 0, physical - files[NATIVE_VROMS[kind]].pstart, len(payload))
        if kind == 'bank':
            new[12] = audio['instrument_count']
        address = NATIVE_HEADERS[kind] + 16 + index * 16
        patch(address, old, new)
        resources[kind] = {'index': index, 'blob_offset': at, 'physical': physical,
            'vrom': BLOB + at, 'bytes': len(payload), 'sha256': sha256(payload),
            'header_address': address, 'header_before': old.hex(), 'header_after': new.hex()}
    resources['wave'] = {'index': 5, 'physical': WAVE_PHYSICAL + start,
        'vrom': wave_file.vstart + start, 'bytes': len(data['wave']), 'sha256': sha256(data['wave'])}
    begin, end = files[BLOB].pstart + files[BLOB].size, files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or end > WAVE_PHYSICAL or any(base[begin:end])
            or any(e.pstart < end and begin < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)):
        raise ValueError('New fire sequence/font overlap existing cartridge resources')
    # Recompute the complete permanent resource budget using actual new headers.
    budget = copy.deepcopy(audio['permanent_audio']['before'])
    budget['capacity'] = HEAP_SETTINGS[2]
    for row in budget['all_permanent_resources']:
        header = header_entry(read, NATIVE_HEADERS[row['kind']], row['index'])
        row['bytes'] = u32(header, 4)
        row['conservative_allocation'] = (row['bytes'] + 31) & -32
    budget['conservative_required'] = sum(r['conservative_allocation'] for r in budget['all_permanent_resources'])
    budget['conservative_spare'] = budget['capacity'] - budget['conservative_required']
    budget['audio_heap_growth'] = 1024
    if budget['conservative_required'] != 109312 or budget['conservative_spare'] != 256:
        raise ValueError('New complete audio allocation does not supply the measured capacity')

    result = bytearray(base)
    result[files[CODE_VROM].pstart:files[CODE_VROM].pstart + len(code)] = code
    result[files[BLOB].pstart:end] = blob
    result[WAVE_PHYSICAL:WAVE_PHYSICAL + len(waves)] = waves
    for entry, size, physical in ((files[BLOB], len(blob), files[BLOB].pstart), (wave_file, len(waves), WAVE_PHYSICAL)):
        struct.pack_into('>4I', result, DMA_START + entry.index * 16, entry.vstart, entry.vstart + size, physical, 0)
    fix_checksum(result)
    result = bytes(result)
    directory = by_vrom(result)
    if len(directory) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16):
        raise ValueError('Fire audio changes the full directory count or terminator')
    for row in headers:
        if row['index'] != 5 and result[row['physical']:row['physical'] + row['bytes']] != base[
                row['physical_before']:row['physical_before'] + row['bytes']]:
            raise ValueError('Wave relocation changes an original or imported waveform resource')
    patch_data = make_ups(original, result)
    if apply_ups(original, patch_data) != result:
        raise ValueError('Fire-audio cartridge fails complete patch reconstruction')
    report = copy.deepcopy(prior)
    report.update(build='v3-fire-sound-runtime', input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch_data), blob_sha256=sha256(blob),
        native_test='pending current audio allocation, complete font, and sample playback')
    report['fire_sound'] = {'audio_report_sha256': AUDIO_SHA, 'resources': resources,
        'wave_file': {'vrom': wave_file.vstart, 'physical': WAVE_PHYSICAL, 'bytes': len(waves),
            'sha256': sha256(waves), 'old_physical': wave_file.pstart, 'retains_old_allocation': True},
        'wave_headers': headers, 'code_patches': patches, 'after_budget': budget,
        'heap_settings': list(HEAP_SETTINGS), 'sound_ids': {'bonfire': 0x5C, 'campfire': 0x5D},
        'programs': audio['programs'], 'instruments': audio['imports'],
        'level_table': audio['level_table'], 'level_table_count': 128,
        'sound_resources_installed': True, 'furniture_callbacks_installed': False,
        'runtime_abi_changed': False, 'saved_format_changed': False, 'saved_profile_changed': False,
        'web_patcher_changed': False}
    report['speed_bag_sound']['current_audio_resource_map'] = 'fire_sound'
    report['complete_villager_audio']['current_wave_initializer_map'] = 'fire_sound.wave_headers'
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in
        ('tools/v3_fire_sound_runtime.py', 'tools/v3_fire_audio.py')})
    output.mkdir(parents=True)
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch_data)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({'sha256': report['output_sha256'], 'audio': report['fire_sound']['after_budget']}, indent=2))
