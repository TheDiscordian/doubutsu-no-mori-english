"""Give imported houses separate temporary markers without moving native IDs."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_npc_draw import relocation_offsets
from v3_registry import villager_actor, villager_house_marker

ABI = 60
BASE = ROOT/'build/v3-house-exterior-01'
BASE_SHA = 'ba188ffb7579a92418de4861f1b6daa92e6140f276ae4b17deaeb027cebed8df'
HOUSE, HOUSE_RELOC, HOUSE_RAM = 0x8D2440, 0x8D3B80, 0x80A03770
HOUSE_SHA = '0b99957c05e9cae76ce6f916425ff2d30c21e844dcebf8d13cff60f129030ce7'
NPC, NPC_RELOC, NPC_RAM = 0x8681F0, 0x878550, 0x809735B0
NPC_SHA = '8344c68daad3d5e51488046871ead7b4ccce62867632eff61306cdc4f5a89443'
# Native growth flags occupy 1E80..1F5F; town modes occupy 1F60..1F73.
# This separate 128-byte gap ends at the complete NPC drawing table. Startup's
# guard is BFF0, not the obsolete ABI-1 guard at 1FF0.
MARKER_OFFSET, MARKER_END = 0x1F80, 0x2000


def build(output):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Ignored build/ output required')
    base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    prior = json.loads((BASE/'build.json').read_text())
    if sha256(base) != BASE_SHA or prior['output_sha256'] != BASE_SHA or prior['runtime_abi'] != 59:
        raise ValueError('Changed exterior-fix parent')
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    house, npc = bytearray(files[HOUSE].extract(base)), bytearray(files[NPC].extract(base))
    if sha256(house) != HOUSE_SHA or sha256(npc) != NPC_SHA:
        raise ValueError('Changed house/NPC owners')
    if any(blob[MARKER_OFFSET:MARKER_END]):
        raise ValueError('Occupied marker-code reservation')
    if len(blob) != 0x131690 or prior['house_exterior']['save_profile_changed']:
        raise ValueError('Changed physical/storage profile parent')
    output.mkdir(parents=True, exist_ok=False)
    helper, compiled = compile_part('house_markers', output/'house_markers',
                                    primary_source='overlays/v3/house_markers.S')
    if not helper or len(helper) > MARKER_END-MARKER_OFFSET:
        raise ValueError('Marker helper overlaps NPC drawing records')
    blob[MARKER_OFFSET:MARKER_OFFSET+len(helper)] = helper
    symbols = compiled['symbols']
    hooks = []

    def hook(data, vrom, ram, offset, before, words):
        after = struct.pack('>'+str(len(words))+'I', *words)
        if data[offset:offset+len(after)].hex() != before:
            raise ValueError('Changed native marker expression')
        data[offset:offset+len(after)] = after
        hooks.append({'vrom': f'{vrom:08X}', 'address': f'{ram+offset:08X}',
                      'offset': offset, 'before': before, 'after': after.hex()})

    jal = lambda label: 0x0C000000 | ((symbols[label]>>2)&0x3FFFFFF)
    hook(house, HOUSE, HOUSE_RAM, 0x97C, '3401a00500611821',
         (jal('af_v3_house_marker_v1'), 0))
    hook(house, HOUSE, HOUSE_RAM, 0x10C4, '008120213084ffff',
         (jal('af_v3_house_marker_a0'), 0))
    # Return only the predicate through at. The following native actual-house
    # range path stays intact, including its separate native branch delay slot.
    hook(npc, NPC, NPC_RAM, 0x3B84, '0071082a142000020072082a14200008',
         (jal('af_v3_is_house_marker_v1'), 0, 0x14200009, 0))
    for vrom, reloc, data in ((HOUSE, HOUSE_RELOC, house), (NPC, NPC_RELOC, npc)):
        offsets = relocation_offsets(files[reloc].extract(base), len(data))
        for row in hooks:
            if int(row['vrom'], 16) == vrom and set(range(row['offset'], row['offset']+len(bytes.fromhex(row['after'])), 4)) & offsets:
                raise ValueError('Marker window overlaps an original relocation')
    if files[HOUSE].pend == 0 or files[NPC].pend:
        raise ValueError('Changed expected house/NPC physical storage')
    old_end = files[BLOB].pstart+len(blob)
    blob.extend(bytes((-len(blob))&15))
    house_offset = len(blob)
    blob.extend(house)
    new_end = files[BLOB].pstart+len(blob)
    if len(blob) > 0x200000 or new_end > 0x4000000 or any(base[old_end:]):
        raise ValueError('Marker storage exceeds verified padding or 64-MiB limit')
    if any(e.vstart < BLOB+len(blob) and BLOB+files[BLOB].size < e.vend
           for vrom, e in files.items() if vrom != BLOB):
        raise ValueError('Appended house owner overlaps another virtual resource')
    struct.pack_into('>I', blob, 4, ABI)
    startup, startup_report = compile_part('startup', output/'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', 'AF_V3_ACCESSORY_BYTES=61440'))
    module = bytearray(files[MODULE].extract(base))
    old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup) > CONFIG-STARTUP):
        raise ValueError('Changed startup contract')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    size = max(len(base), 1 << (new_end-1).bit_length())
    image = bytearray(base)+bytes(size-len(base))
    for vrom, data in ((BLOB, blob), (NPC, npc), (MODULE, module)):
        entry = files[vrom]
        if entry.pend or vrom != BLOB and len(data) != entry.size:
            raise ValueError('Unexpected owner resize')
        image[entry.pstart:entry.pstart+len(data)] = data
    struct.pack_into('>I', image, DMA_START+files[BLOB].index*16+4, BLOB+len(blob))
    struct.pack_into('>2I', image, DMA_START+files[HOUSE].index*16+8,
                     files[BLOB].pstart+house_offset, 0)
    fix_checksum(image)
    image = bytes(image)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('House marker patch reconstruction failed')
    sources = ('tools/v3_house_markers.py', 'tools/v3_registry.py', 'tools/v3_asset_loader.py',
               'overlays/v3/house_markers.S', 'overlays/v3/house_markers.ld',
               'overlays/v3/startup.c', 'overlays/v3/startup.ld')
    rows = [{'actor_id': f'{villager_actor(i):04X}', 'house_id': f'{villager_actor(i)-0x9000:04X}',
             'marker_id': f'{villager_house_marker(i):04X}'} for i in range(216, 236)]
    report = {**prior, 'build': 'v3-house-markers', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_bytes': len(blob), 'blob_sha256': sha256(blob), 'startup': startup_report,
        'house_markers': {'code': compiled, 'hooks': hooks, 'imports': rows,
            'house_blob_offset': house_offset, 'house_sha256': sha256(house), 'npc_sha256': sha256(npc),
            'original_markers_unchanged': True, 'additional_ram_allocation': 0, 'rom_bytes': len(image),
            'save_format_changed': False, 'save_profile_changed': False,
            'native_test': 'pending', 'ordinary_save_reload_tested': False, 'not_a_playtest_handoff': True},
        'native_test': 'pending complete house-marker integration',
        'sources': {**prior['sources'], **{p: sha256((ROOT/p).read_bytes()) for p in sources}}}
    write_new(output/'animal-forest-v3-asset-loader.z64', image)
    write_new(output/'asset-loader.ups', patch)
    write_new(output/'build.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({k: report[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
