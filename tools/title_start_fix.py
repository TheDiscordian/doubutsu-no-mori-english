"""Correct the linear English Press Start source on the complete v1 cartridge."""
import argparse
import json
from pathlib import Path

from aflib import by_vrom, verified_rom, sha256, replace_dma, fix_checksum, make_ups, apply_ups
from title_assets import ROOT, DATA_BASE, REL_SHA256, SYMBOLS_SHA256, scoped_symbols
from title_press_start import ASSETS, TEXTURE_OFFSETS

BASE_SHA = 'a8072a76783317215ae85afbf31cca77422d5b783512194d8269004f31073780'
STORAGE = ((0x5E5020, 'log_win_logo3_tex'), (0x5E5420, 'log_win_logo4_tex'))
BANK_SHA = '3099db1a1d5491130d8754e9946e27b2f9a7d29e5faf39da55e8215f17b2aeb7'


def source_tiles(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed English title source')
    named = scoped_symbols(symbols)
    tiles = []
    for at, name in STORAGE:
        if named[at]['symbol'] != name or named[at]['bytes'] != 1024:
            raise ValueError('Changed linear Press Start storage')
        # The GC actor uses the compatibility gDPLoadTextureTile path, not a
        # Dolphin tiled model command. These are already row-major N64 I:A.
        tiles.append(rel[DATA_BASE+at:DATA_BASE+at+1024])
    return tiles


def reconstruct(native, base, changes):
    """Repack from the original without doubling an already padded cartridge."""
    verified_rom(native)
    originals, files = by_vrom(native), by_vrom(base)
    by_index = {entry.index: entry for entry in files.values()}
    replacements, moved, additions = {}, {}, {}
    original_indices = {entry.index for entry in originals.values()}
    if len(by_index) != len(files) or not original_indices <= set(by_index):
        raise ValueError('Missing or duplicate native DMA identity')
    if not changes or not set(changes) <= set(files):
        raise ValueError('Missing or unknown fix resource')
    for address, data in changes.items():
        if address in (0x1060, 0x19D40) or len(data) != files[address].size:
            raise ValueError('Fix changes boot data or an owned allocation')
    for vrom, old in originals.items():
        entry = by_index[old.index]
        data = changes.get(entry.vstart, entry.extract(base))
        if vrom == 0x19D40:
            if entry.vstart != vrom or entry.size != old.size or data[:16] != old.extract(native)[:16]:
                raise ValueError('Changed DMA table owner prefix')
            continue
        if entry.vstart != vrom or entry.size != old.size:
            moved[vrom] = entry.vstart
        if data != old.extract(native) or vrom in moved:
            replacements[vrom] = data
    for entry in files.values():
        if entry.index not in original_indices:
            additions[entry.vstart] = changes.get(entry.vstart, entry.extract(base))
    image = bytearray(replace_dma(native, replacements, moved, additions))
    # IPL3 executes this physical copy before the DMA table is used.
    boot = originals[0x1060]
    boot_data = files[0x1060].extract(base)
    if base[boot.pstart:boot.pstart+boot.size] != boot_data:
        raise ValueError('Base startup copies disagree')
    image[boot.pstart:boot.pstart+boot.size] = boot_data
    fix_checksum(image)
    image = bytes(image)
    installed = by_vrom(image)
    if len(image) != len(base) or set(installed) != set(files):
        raise ValueError('Fix changes cartridge size or DMA identities')
    for vrom, before in files.items():
        after = installed[vrom]
        actual, expected = after.extract(image), changes.get(vrom, before.extract(base))
        if vrom == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if before.index != after.index or before.size != after.size or actual != expected:
            raise ValueError(f'Fix loses unrelated resource {vrom:08X}')
    if image[boot.pstart:boot.pstart+boot.size] != boot_data:
        raise ValueError('Fix changes physical startup code')
    return image


def build(native, base, rel, symbols):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Press Start fix requires the complete civic v1 baseline')
    bank = by_vrom(base)[ASSETS].extract(base)
    if sha256(bank) != BANK_SHA:
        raise ValueError('Unexpected current title texture bank')
    tiles = source_tiles(rel, symbols)
    changed = bytearray(bank)
    for at, tile in zip(TEXTURE_OFFSETS, tiles+[bytes(1024)]):
        changed[at:at+1024] = tile
    image = reconstruct(native, base, {ASSETS: bytes(changed)})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Press Start fix patch reconstruction failed')
    report = {'version': 1, 'source_sha256': sha256(native), 'baseline_sha256': BASE_SHA,
              'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
              'rom_bytes': len(image), 'changed_files': {f'{ASSETS:08X}': sha256(changed)},
              'source_storage': 'linear N64 IA8 compatibility textures; no untile or nibble swap',
              'source_rel_sha256': REL_SHA256, 'source_symbols_sha256': SYMBOLS_SHA256,
              'tiles': [{'source': f'{source:08X}', 'symbol': name, 'destination': f'{ASSETS+at:08X}',
                         'width': 64, 'height': 16, 'sha256': sha256(tile)}
                        for (source, name), at, tile in zip(STORAGE, TEXTURE_OFFSETS, tiles)],
              'third_tile': 'transparent', 'required_ram_bytes': 0x800000,
              'code_changed': False, 'allocation_changed': False, 'save_format_changed': False,
              'other_resources_retained': True, 'fixed_issues': ['V1-01'],
              'hardware_retest': 'pending',
              'status': 'Corrected source pixels installed; other V1 playtest bugs remain open'}
    return image, patch, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/title-civic-interior-combined-01')
    parser.add_argument('--output', type=Path, default=ROOT/'build/v1-playtest-fixes-01')
    args = parser.parse_args()
    base = (args.base/'animal-forest-title-preview.z64').read_bytes()
    prior = json.loads((args.base/'preview.json').read_text())
    if prior.get('output_sha256') != BASE_SHA:
        raise ValueError('Mismatched title baseline report')
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), base,
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    report['baseline_report_sha256'] = sha256((args.base/'preview.json').read_bytes())
    report['baseline_actor_sha256'] = prior['actor']['overlay_sha256']
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in {'animal-forest-title-preview.z64': image,
                       'animal-forest-title-preview.ups': patch,
                       'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:
            target.write(data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
