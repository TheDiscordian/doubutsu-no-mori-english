"""Extend native HRA acquisition counters before admitting donor reward furniture."""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum,
                   make_ups, sha256, u32, verified_rom)
from apply_translation import write_new
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_furniture_art import verify_sources
import v3_hra as hra

BASE = ROOT / 'build/v3-aloha-scoring-01'
BASE_SHA = 'e6a890c37e972422fe44cbbfb322dcccd17805186baa96ed7c20a45a2d4022f3'
REPORT_SHA = '33959d0d3224ace91e14cedf5215eeffa3cd7e15c1f7d067fea0290a9b5c4c6b'
ABI, COUNT, OLD_COUNT, TABLE = 63, 23, 19, 0x80928680
ENTRY, END = 0x809274F8, 0x809277F8
FUNCTION_SHA = 'c9fa9099ece06af915881edd4b4f5aaeb47a697f08adc13c505939dce84cecf7'
# Complete SP-based instruction inventory, including preserved product/s0 slots.
STACK = {
    0x809274F8: 0x27BDFF18, 0x809274FC: 0xAFB00004,
    0x80927500: 0xAFA400E8, 0x80927504: 0xAFA700F4,
    0x80927508: 0xAFA0009C, 0x8092750C: 0xAFA00050,
    0x80927510: 0xAFA000A0, 0x80927514: 0xAFA00054,
    0x80927518: 0xAFA000A4, 0x8092751C: 0xAFA00058,
    0x80927520: 0x27A300A8, 0x80927524: 0x27A4005C,
    0x80927528: 0x27A2009C, 0x80927568: 0x27A3009C,
    0x809276C4: 0x8FAF009C, 0x809276D4: 0x8FB900A0,
    0x809276E0: 0x8FAF00A4, 0x809276EC: 0x27A4005C,
    0x809276F0: 0x27A300A8, 0x809276F4: 0x27AA00E8,
    0x809276FC: 0xAFA70050, 0x80927710: 0xAFA80054,
    0x8092771C: 0xAFA90058, 0x80927794: 0x8FB800F8,
    0x809277B0: 0x8FB900F4, 0x809277CC: 0x8FAE00E8,
    0x809277EC: 0x8FB00004, 0x809277F4: 0x27BD00E8,
}
POINTERS = {
    0x809276C0: (0x809276BC, TABLE),
    0x809276CC: (0x809276C8, TABLE + 4),
    0x809276DC: (0x809276D8, TABLE + 8),
    0x809276E8: (0x809276E4, TABLE + 12),
    0x809277A8: (0x8092779C, TABLE),
}
SOURCES = ('tools/v3_hra_birth.py', 'tools/v3_asset_loader.py',
           'overlays/v3/startup.c', 'overlays/v3/startup.ld')


def extend(data, relocation, report, rel, symbols):
    verify_sources(rel, symbols)
    if (sha256(data) != report['output_sha256'] or len(data) != 31296
            or sha256(relocation) != report['relocation_sha256']
            or struct.unpack_from('>5I', relocation) != (31296, 0, 0, 0, 288)
            or sha256(data[ENTRY - hra.RAM:END - hra.RAM + 4]) != FUNCTION_SHA):
        raise ValueError('Changed complete current HRA owner or native evaluator')
    found = {hra.RAM + at: u32(data, at) for at in range(ENTRY - hra.RAM, END - hra.RAM, 4)
             if u32(data, at) >> 21 & 31 == 29}
    if found != STACK or COUNT != 3 + 4 * 5:
        raise ValueError('Changed evaluator stack inventory or unrolled-loop shape')
    points = data[TABLE - hra.RAM:TABLE - hra.RAM + OLD_COUNT * 4]
    donor = symbol_data(rel, symbols.decode(), 'mMkRm_birth_point_table')
    values = struct.unpack('>38I', donor)
    if (sha256(points) != '9b99f983607e5c84318a9fe05d71fa3ecf3d3ffefcb18b0ee809f664094dc5f9'
            or values != (51, 51, 51, 412, 1000, 1031, 821, 1029, 3, 3, 3, 3, 300, 1000,
                          700, 1224, 0, 888, 1031, 1111, 1111, 1111, 412, 1000, 1983,
                          1300, 1983, 3, 1983, 1111, 412, 0, 412, 412, 1000, 1177, 1400, 412)):
        raise ValueError('Changed native or donor acquisition point weights')
    # Keep all nineteen N64 weights, including its different lottery value.
    points += donor[OLD_COUNT * 4:COUNT * 4]
    table_at = len(data) + 4
    image = bytearray(data + bytes(4) + points)
    if len(image) % 16 or len(image) > 0x8000:
        raise ValueError('Extended HRA table exceeds aligned native image capacity')
    patches = []

    def word(address, before, after):
        at = address - hra.RAM
        if u32(image, at) != before:
            raise ValueError('Changed acquisition-score instruction')
        if before == after:
            return
        struct.pack_into('>I', image, at, after)
        patches.append({'address': address, 'before': before, 'after': after})

    for address, before in STACK.items():
        immediate = before & 65535
        if address == ENTRY:
            immediate = (-264) & 65535
        elif immediate >= 0xE8:
            immediate += 32
        elif immediate >= 0x9C:
            immediate += 16
        word(address, before, before & 0xFFFF0000 | immediate)
    high, found_pointers = {}, {}
    for (value,) in struct.iter_unpack('>I', relocation[20:20 + 288 * 4]):
        kind, at = value >> 24 & 63, value & 0xFFFFFF
        if value >> 30 != 1:
            raise ValueError('Changed HRA relocation section')
        instruction = u32(data, at)
        if kind == 5:
            high[instruction >> 16 & 31] = at, instruction
        elif kind == 6:
            h_at, upper = high[instruction >> 21 & 31]
            target = (upper & 65535) * 65536 + (instruction & 65535) - (65536 if instruction & 32768 else 0)
            if TABLE <= target < TABLE + OLD_COUNT * 4:
                found_pointers[hra.RAM + at] = hra.RAM + h_at, target
                new = hra.RAM + table_at + target - TABLE
                word(hra.RAM + h_at, upper, upper & 0xFFFF0000 | (new + 0x8000) >> 16 & 65535)
                word(hra.RAM + at, instruction, instruction & 0xFFFF0000 | new & 65535)
    if found_pointers != POINTERS:
        raise ValueError('Changed complete acquisition-score table-reference inventory')
    updated_reloc = bytearray(relocation)
    struct.pack_into('>I', updated_reloc, 0, len(image))
    allowed = {offset for p in patches for offset in range(p['address'] - hra.RAM, p['address'] - hra.RAM + 4)}
    for destination in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(SimpleNamespace(ram=hra.RAM, resident_bytes=len(data),
            sections=(len(data), 0, 0, 0, 288)), data, relocation, destination)
        after = relocate_verified_data(SimpleNamespace(ram=hra.RAM, resident_bytes=len(image),
            sections=(len(image), 0, 0, 0, 288)), image, updated_reloc, destination)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Acquisition extension changes unrelated relocated code or data')
    return bytes(image), bytes(updated_reloc), {
        'old_count': OLD_COUNT, 'count': COUNT, 'old_stack_bytes': 232, 'stack_bytes': 264,
        'points_address': hra.RAM + table_at, 'points_sha256': sha256(points),
        'native_weights_preserved': True, 'donor_weights_sha256': sha256(donor),
        'added_categories': [19, 20, 21, 22], 'added_points': list(values[19:23]),
        'patches': patches, 'relocation_destinations_checked': 3,
        'saved_format_changed': False, 'saved_profile_changed': False,
        'additional_on_demand_bytes': len(image) - len(data),
        'additional_permanent_ram': 0, 'native_test': 'pending',
        'reward_acquisition_installed': False, 'new_item_ids_enabled': False}


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if sha256(base) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed complete aloha-corrected source')
    prior = json.loads(raw)
    if prior['runtime_abi'] != 62:
        raise ValueError('Changed source ABI')
    files = by_vrom(base)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    data, relocation, detail = extend(files[hra.NEW_VROM].extract(base),
        files[hra.NEW_RELOC].extract(base), prior['hra'], rel, symbols)
    code = bytearray(files[CODE_VROM].extract(base))
    scheduler = copy.deepcopy(prior['hra']['scheduler'])
    for row in scheduler:
        at = row['address'] - CODE_RAM
        before = row['after']
        if u32(code, at) != before:
            raise ValueError('Changed actual HRA scheduler')
        if row['address'] in (0x8009CED8, 0x8009CF10):
            target = hra.RAM + len(data)
            after = before & 0xFFFF0000 | target & 65535
        elif row['address'] == 0x8009CF18:
            after = before & 0xFFFF0000 | len(data)
        else:
            after = before
        struct.pack_into('>I', code, at, after)
        row['before'], row['after'] = before, after
    if (hra.RAM + len(data) + 0x8000) >> 16 != 0x8093:
        raise ValueError('Expanded scheduler end needs a changed high half')
    blob = bytearray(files[BLOB].extract(base))
    old_size = len(blob)
    moves = []
    for vrom, payload in ((hra.NEW_VROM, data), (hra.NEW_RELOC, relocation)):
        blob.extend(bytes(-len(blob) % 16))
        at = len(blob)
        blob.extend(payload)
        moves.append({'vrom': vrom, 'bytes': len(payload), 'blob_offset': at,
                      'physical': files[BLOB].pstart + at, 'sha256': sha256(payload)})
    if (len(blob) > 0x200000 or files[BLOB].pstart + len(blob) > len(base)
            or len(base) != 0x4000000
            or any(base[files[BLOB].pstart + old_size:files[BLOB].pstart + len(blob)])
            or any(e.vstart < BLOB + len(blob) and BLOB + old_size < e.vend
                   for v, e in files.items() if v != BLOB)):
        raise ValueError('Extended scoring resources exceed verified cartridge storage')
    struct.pack_into('>I', blob, 4, ABI)
    module = bytearray(files[MODULE].extract(base))
    output.mkdir(parents=True)
    startup, compiled = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', 'AF_V3_ACCESSORY_BYTES=61440'))
    old_startup = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old_startup['bytes']]) != old_startup['sha256']
            or any(module[STARTUP + old_startup['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed startup or code reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    image = bytearray(base)
    for vrom, payload in ((CODE_VROM, code), (MODULE, module), (BLOB, blob)):
        entry = files[vrom]
        if entry.pend or vrom != BLOB and len(payload) != entry.size:
            raise ValueError('Unexpected scoring integration allocation')
        image[entry.pstart:entry.pstart + len(payload)] = payload
    struct.pack_into('>I', image, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moves:
        struct.pack_into('>4I', image, DMA_START + files[row['vrom']].index * 16,
                         row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(image)
    image = bytes(image)
    patch = make_ups(original, image)
    if apply_ups(original, patch) != image:
        raise ValueError('Acquisition scoring patch reconstruction failed')
    report = {**prior, 'build': 'v3-hra-birth', 'runtime_abi': ABI, 'input_build_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'blob_bytes': len(blob),
        'blob_file_bytes': len(blob), 'blob_sha256': sha256(blob), 'startup': compiled,
        'hra': {**prior['hra'], 'bytes': len(data), 'output_sha256': sha256(data),
            'relocation_bytes': len(relocation), 'relocation_sha256': sha256(relocation),
            'on_demand_growth': len(data) - prior['hra']['source_resident_bytes'],
            'scheduler': scheduler, 'birth_extension': detail},
        'hra_birth': {**detail, 'resource_moves': moves, 'not_a_playtest_handoff': True,
            'compatibility': 'Same saved format and profile as ABI 62; ordinary cross-build reload is unverified. Keep backups.'},
        'native_test': 'pending current expanded acquisition-counter check',
        'sources': {**prior['sources'], **{p: sha256((ROOT / p).read_bytes()) for p in SOURCES}}}
    write_new(output / 'animal-forest-v3-asset-loader.z64', image)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({k: report[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
