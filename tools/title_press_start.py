#!/usr/bin/env python3
"""Build a separate English Press Start preview without changing v0 artifacts."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups
from package_v0 import CANDIDATE_SHA256
from title_assets import extract, ROOT

ACTOR, RELOC, ASSETS = 0x0095FEC0, 0x009625A0, 0x01136000
RAM = 0x80A9FC70
COLLECTION_BASE_SHA = '27f840aaea2693ac96fbbc084981dd978f8e376cbf8d7a1259666160d29f5f7d'
GRID_BASE_SHA = 'e5f2a22f50f89fdf7e0e9743368abf9a2f4d261e303dc0339f5cbbc4a0ad48f7'
NOOKINGTON_BASE_SHA = '28c551708dbbc1d78333abc7ebf81d5001663859775ca9f85427ced8208b0020'
POLICE_BASE_SHA = '7ec5ba6eb5a68e15a3c89ab37111cf758a5b02241a1f51291cebf174b64ef6ad'
TITLE_BASES = {CANDIDATE_SHA256, COLLECTION_BASE_SHA, GRID_BASE_SHA, NOOKINGTON_BASE_SHA, POLICE_BASE_SHA}
SOURCE_HASHES = {
    ACTOR: '2c91de2e6987199c74b092698a3e656bc023ad0fd924b32e4a7aeb4ffc177a01',
    RELOC: '5642d27903df612f39d052b66682acaf2d4a634d878fcd8da05246fa50d1e29b',
    ASSETS: '4769ffc7d832ffbc7b91bcafb708cce34d7455c7a18e29100b9586cd9e83de2a',
}
POSITIONS = 0x80AA2284-RAM
TEXTURE_OFFSETS = (0x1110, 0x1510, 0x1910)


def replacements(native, base, english):
    verified_rom(native)
    if sha256(base) not in TITLE_BASES:
        raise ValueError('Title preview requires a reviewed complete baseline')
    old, current = by_vrom(native), by_vrom(base)
    for vrom, digest in SOURCE_HASHES.items():
        if sha256(old[vrom].extract(native)) != digest or current[vrom].extract(base) != old[vrom].extract(native):
            raise ValueError('Changed native title actor, relocation, or asset bank')
    actor, data = bytearray(old[ACTOR].extract(native)), bytearray(old[ASSETS].extract(native))
    if len(data) != 0x5CD0 or struct.unpack_from('>6I', actor, POSITIONS) != (74, 138, 202, 154, 154, 154):
        raise ValueError('Changed native Press Start allocation or tile positions')
    # The source-hash-bound draw function consumes these three 64x16 IA8 tiles.
    tiles = [english['005E5020.ia8.bin'], english['005E5420.ia8.bin'], bytes(1024)]
    if any(len(tile) != 1024 for tile in tiles):
        raise ValueError('Press Start requires two complete 64x16 English IA8 tiles')
    for offset, tile in zip(TEXTURE_OFFSETS, tiles):
        data[offset:offset+1024] = tile
    struct.pack_into('>6I', actor, POSITIONS, 96, 160, 224, 159, 159, 159)
    return {ACTOR: bytes(actor), ASSETS: bytes(data)}


def assemble(native, base, report, changed):
    if set(changed) != {ACTOR, ASSETS} or report.get('output_sha256') != CANDIDATE_SHA256:
        raise ValueError('Unexpected Press Start preview changes or predecessor')
    files = by_vrom(base)
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements_map = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                        for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    replacements_map.update(changed)
    result = replace_dma(native, replacements_map, moved, additions)
    installed = by_vrom(result)
    if set(installed) != set(files):
        raise ValueError('Press Start preview adds or removes an unrelated DMA file')
    for vrom, entry in installed.items():
        if entry.index != files[vrom].index or entry.size != files[vrom].size:
            raise ValueError('Press Start preview changes an existing DMA identity/size')
        expected = changed.get(vrom, files[vrom].extract(base))
        actual = entry.extract(result)
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if actual != expected:
            raise ValueError(f'Press Start preview loses a previous resource: {vrom:08X}')
    return result


def build(native, base, report, rel, symbols):
    english, assets_report = extract(rel, symbols)
    changed = replacements(native, base, english)
    result = assemble(native, base, report, changed)
    patch = make_ups(native, result)
    if apply_ups(native, patch) != result:
        raise ValueError('Title preview patch reconstruction failed')
    evidence = {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': CANDIDATE_SHA256,
        'output_sha256': sha256(result), 'patch_sha256': sha256(patch),
        'changed_files': {f'{v:08X}': sha256(data) for v, data in changed.items()},
        'reference_sha256': assets_report['source_sha256'],
        'english_tiles': ['005E5020', '005E5420'], 'third_native_tile': 'transparent',
        'visible_positions': [[96, 159], [160, 159]], 'actor_code_changed': False,
        'allocation_changed': False, 'relocation_changed': False, 'v0_candidate_changed': False,
        'status': 'Separate Press Start preview; main logo and native visual validation pending'}
    return result, patch, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/classic-letters-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-press-start-preview')
    args = parser.parse_args()
    result, patch, evidence = build(
        (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (args.base/'animal-forest-halfwidth.z64').read_bytes(), json.loads((args.base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in (('animal-forest-title-preview.z64', result), ('animal-forest-title-preview.ups', patch),
                       ('preview.json', (json.dumps(evidence, indent=2)+'\n').encode())):
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
