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
REDD_BASE_SHA = '7cba9ed279dd90b8fa903cd3ab1745aacf7bd0383c5b43347cadc1bf6fecc39a'
CURSOR_BASE_SHA = '2725492f603d6dda9d1984ae4e3dcced520786a6c43e9180082e288d62cdd419'
TUNE_BASE_SHA = '4fcebd1758f3ca5bed1a9c7dd3659f961f27d51572ea5b4f13c49039e2b8d963'
SERVICE_BASE_SHA = '23f9d9724827d0de3c91bd00a91349b04b0d45371d1930ef71cdbb95910e711e'
BIRTHDAY_BASE_SHA = '179c658a70383d278b2b78aa9f2d339c8582ae2cb714e7b95b120163c0104d5d'
PAK_BASE_SHA = 'e6511dfe0a51b75f8764eeed0159a31ee651f6d650075f42501977b0ea1d8483'
SUBMENU_BASE_SHA = '9f12c83314b048225e87c0c4ba46853caf3dadb21f863a234ca03a879987474d'
GYROID_SERVICE_BASE_SHA = '0173bb83decfda63b299fb40aedd22121b546818081754032e60fc3b96d9a257'
NOOKINGTON_DETAILS_BASE_SHA = '2795a31a259996395dafb5df4e46c00f46a1109eda46e6a15119927d9d01d193'
DUMP_BASE_SHA = '5c5206c9a8ee548900ba264276f5052a4ed8b5a13803ffcf1a6b44c880f17226'
FISHING_BASE_SHA = 'ec2917b38e47e936b69b203ffa99913e7fedad9d4ae29e8c368db5441b64ed13'
FORTUNE_BOOTH_BASE_SHA = '69c695c746959f9c3f5b2bda3d56020ce24fdd7a1ec341285ea9696f0738c7c4'
COUNTDOWN_BASE_SHA = '3d0cc3c0db2b6a200adaecbb07733ea3a2537ed0223947192fc6a9cb677a2c99'
STALL_BASE_SHA = '84852fae59184d6eb97d2ee94cbb44ea913680b22a31156287d5a604c048d3d3'
TITLE_BASES = {CANDIDATE_SHA256, COLLECTION_BASE_SHA, GRID_BASE_SHA, NOOKINGTON_BASE_SHA, POLICE_BASE_SHA, REDD_BASE_SHA, CURSOR_BASE_SHA, TUNE_BASE_SHA, SERVICE_BASE_SHA, BIRTHDAY_BASE_SHA, PAK_BASE_SHA, SUBMENU_BASE_SHA, GYROID_SERVICE_BASE_SHA, NOOKINGTON_DETAILS_BASE_SHA, DUMP_BASE_SHA, FISHING_BASE_SHA, FORTUNE_BOOTH_BASE_SHA, COUNTDOWN_BASE_SHA, STALL_BASE_SHA}
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
