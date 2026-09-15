"""Recognise the full imported roster in native outdoor-house consumers."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part

ABI = 59
BASE = ROOT/'build/v3-aloha-display-03'
BASE_SHA = '0f1c532c281ba3dce1bbc32b1085b0207a6617b95090b98d97de2ff1ad2deb0e'
# Only actual house identities expand. Native dummy markers overlap other
# buildings immediately after F0DE and must not be widened in place.
OWNERS = (
    (0x7AC420, 0x808B2D50, '9a9e3262eff9e51a8306fa1ba0455ae8d3c8085d5705b4a6133185b144b20932',
     ((0x83E0, 0x286150DA, 0x286150EE, 'player door-knock classification'),)),
    (0x8681F0, 0x809735B0, '4b277881334bda98b7f91c8a20a4f300e4b006681f4143e9bdd765eb67b1dbdd',
     ((0x3B9C, 0x286150DA, 0x286150EE, 'NPC house proximity'),)),
    (0x8CB690, 0x809E7ED0, '8b630ea1fcd07133d4c4615d0eb0e69f0f23162f81b68347fd5a2796559b93e4',
     ((0xF80, 0x286150DA, 0x286150EE, 'structure actor/profile and artwork selection'),)),
    (0x970920, 0x80AB07C0, '4afba5ece2661e9c8d37e5c96ced009ad5a6f7bdf857b19f04d48c52781d9f4a',
     ((0x1AB8, 0x286150DA, 0x286150EE, 'daily-growth first house cell'),
      (0x1B2C, 0x286150DA, 0x286150EE, 'daily-growth second house cell'),
      (0x2D94, 0x284150DB, 0x284150EE, 'daily-growth protected structure'))),
)


def patch_owner(data, owner):
    vrom, ram, digest, edits = owner
    if sha256(data) != digest:
        raise ValueError(f'Changed complete outdoor-house owner {vrom:08X}')
    output, rows = bytearray(data), []
    for offset, before, after, label in edits:
        if struct.unpack_from('>I', output, offset)[0] != before or before >> 16 != after >> 16:
            raise ValueError('Changed house instruction or register semantics')
        struct.pack_into('>I', output, offset, after)
        rows.append({'offset': offset, 'address': f'{ram+offset:08X}',
                     'before': f'{before:08X}', 'after': f'{after:08X}', 'consumer': label})
    return bytes(output), {'vrom': f'{vrom:08X}', 'ram': f'{ram:08X}',
                           'before_sha256': digest, 'after_sha256': sha256(output), 'edits': rows}


def build(output):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Ignored build/ output required')
    base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    prior = json.loads((BASE/'build.json').read_text())
    if sha256(base) != BASE_SHA or prior['output_sha256'] != BASE_SHA or prior['runtime_abi'] != 58:
        raise ValueError('Changed complete garment/town parent')
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    if (prior['villager_houses']['installed_villagers'] != [f'{n:04X}' for n in range(0xE0DA, 0xE0EE)]
            or blob[0x1E60:0x1E74] != bytes([1])*20 or blob[0x1F60:0x1F74] != bytes([1])*20):
        raise ValueError('Full house/default/town integration is required')
    output.mkdir(parents=True, exist_ok=False)
    changes, rows = {}, []
    for owner in OWNERS:
        vrom = owner[0]
        changes[vrom], row = patch_owner(files[vrom].extract(base), owner)
        rows.append(row)
    # The daily-growth owner is compressed in the parent. Preserve its physical
    # bytes and append a read-only alias in the final blob, without moving audio.
    grow = changes.pop(0x970920)
    if files[0x970920].pend == 0 or len(grow) != files[0x970920].size:
        raise ValueError('Changed daily-growth storage contract')
    old_end = files[BLOB].pstart+len(blob)
    blob.extend(bytes((-len(blob))&15))
    grow_offset = len(blob)
    blob.extend(grow)
    new_end = files[BLOB].pstart+len(blob)
    if new_end > len(base) or len(blob) > 0x200000 or any(base[old_end:new_end]):
        raise ValueError('Outdoor-house append exceeds verified empty cartridge storage')
    struct.pack_into('>I', blob, 4, ABI)
    startup, compiled = compile_part('startup', output/'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', 'AF_V3_ACCESSORY_BYTES=61440'))
    module = bytearray(files[MODULE].extract(base))
    old = prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup) > CONFIG-STARTUP):
        raise ValueError('Changed startup instructions or bounds')
    module[STARTUP:CONFIG] = startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    changes.update({BLOB: blob, MODULE: module})
    image = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or vrom != BLOB and len(data) != entry.size:
            raise ValueError('Unexpected edited-owner resize or compression')
        image[entry.pstart:entry.pstart+len(data)] = data
    struct.pack_into('>I', image, DMA_START+files[BLOB].index*16+4, BLOB+len(blob))
    struct.pack_into('>2I', image, DMA_START+files[0x970920].index*16+8,
                     files[BLOB].pstart+grow_offset, 0)
    fix_checksum(image)
    image = bytes(image)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Outdoor-house patch reconstruction failed')
    sources = ('tools/v3_house_exterior.py', 'overlays/v3/startup.c', 'overlays/v3/startup.ld')
    report = {**prior, 'build': 'v3-house-exterior', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_bytes': len(blob), 'blob_sha256': sha256(blob), 'startup': compiled,
        'house_exterior': {'owners': rows, 'grow_blob_offset': grow_offset,
            'additional_ram_allocation': 0, 'save_format_changed': False, 'save_profile_changed': False,
            'native_test': 'pending', 'dummy_markers': 'separate additive mapping remains required',
            'not_a_playtest_handoff': True},
        'native_test': 'pending outdoor-house crash verification',
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
