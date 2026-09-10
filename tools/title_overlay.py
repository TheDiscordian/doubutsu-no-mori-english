#!/usr/bin/env python3
"""Install the source-bound animated English title as a separate v1 preview."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, replace_dma, make_ups, apply_ups, fix_checksum
from package_v0 import CANDIDATE_SHA256
from title_assets import ROOT, extract
from title_press_start import ACTOR, RELOC, ASSETS, RAM, TITLE_BASES, replacements as start_replacements
from title_memory import BOOT, install as install_memory

NEW_ACTOR, NEW_RELOC = 0x03C00000, 0x03C50000
METADATA = 0x801021F0
METADATA_BYTES = bytes.fromhex('0095fec0009625a080a9fc7080aa23500000000080aa1f400000000000000000')
OVERLAY_SHA256 = 'b2ee139e3b57411e3cb6bae925ad2e9303bc205f3e314b5c60b9a547ce2f6e36'
RELOCATION_SHA256 = 'f8b4f4361dd9812f0bd7af8d744199f57a7e6fbfc0fb7507f7cfa983c7b042e9'
SIZE = 292320


def validate(data, reloc, profile):
    if (sha256(data) != OVERLAY_SHA256 or sha256(reloc) != RELOCATION_SHA256
            or len(data) != SIZE or len(reloc) != 720
            or profile.get('overlay_sha256') != OVERLAY_SHA256
            or profile.get('relocation_sha256') != RELOCATION_SHA256
            or profile.get('ram') != RAM or profile.get('bytes') != SIZE
            or profile.get('actor_instance_bytes') != 1968
            or profile.get('state_offset') != 0x330 or profile.get('state_bytes') != 1152):
        raise ValueError('Unapproved complete English title overlay')
    sources = profile.get('sources', {})
    required = {'overlays/title/title.c', 'overlays/title/append.ld', 'tools/title_graphics.py',
                'tools/title_model.py', 'tools/title_assets.py'}
    required.update('upstream/af/lib/ultralib/include/PR/'+name for name in ('mbi.h', 'gbi.h', 'abi.h', 'ultratypes.h'))
    if set(sources) != required or any(sha256((ROOT/p).read_bytes()) != digest for p, digest in sources.items()):
        raise ValueError('Title overlay source inventory changed; rebuild it')
    return True


def build(native, base, report, rel, symbols, data, reloc, profile):
    verified_rom(native); validate(data, reloc, profile)
    baseline_sha = sha256(base)
    if baseline_sha not in TITLE_BASES or report.get('output_sha256') != baseline_sha:
        raise ValueError('English title requires a reviewed complete baseline')
    assets = extract(rel, symbols)[0]
    changed = start_replacements(native, base, assets)
    files = by_vrom(base)
    if NEW_ACTOR in files or NEW_RELOC in files:
        raise ValueError('English title VROM ownership conflicts with existing data')
    moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
    replacements = {int(v, 16): files[moved.get(int(v, 16), int(v, 16))].extract(base)
                    for v in report['replacement_files']}
    additions = {int(v, 16): files[int(v, 16)].extract(base) for v in report['added_files']}
    code = bytearray(files[CODE_VROM].extract(base))
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES or ACTOR in moved or RELOC in moved:
        raise ValueError('English title actor ownership differs from the native profile')
    metadata = bytearray(METADATA_BYTES)
    struct.pack_into('>4I', metadata, 0, NEW_ACTOR, NEW_ACTOR+SIZE, RAM, RAM+SIZE)
    struct.pack_into('>H', metadata, 28, 1)  # Native absolute release clears the pointer without heap-freeing it.
    code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata
    boot, memory = install_memory(native, base, code, SIZE, warning=baseline_sha != CANDIDATE_SHA256)
    replacements.update({ACTOR: data, RELOC: reloc, ASSETS: changed[ASSETS], CODE_VROM: bytes(code), BOOT: boot})
    moved.update({ACTOR: NEW_ACTOR, RELOC: NEW_RELOC})
    image = replace_dma(native, replacements, moved, additions)
    # IPL3 loads the boot image directly before a DMA table exists. Keep the
    # physical startup copy and its later DMA identity consistent.
    physical = by_vrom(native)[BOOT].pstart
    original_boot = files[BOOT].extract(base)
    if base[physical:physical+len(boot)] != original_boot:
        raise ValueError('Physical IPL boot image differs from its v0 DMA identity')
    image = bytearray(image)
    image[physical:physical+len(boot)] = boot
    fix_checksum(image)
    image = bytes(image)
    installed = by_vrom(image)
    if set(installed) != (set(files)-{ACTOR, RELOC}) | {NEW_ACTOR, NEW_RELOC}:
        raise ValueError('English title changes unrelated DMA identities')
    expected_changes = {NEW_ACTOR: data, NEW_RELOC: reloc, CODE_VROM: bytes(code), ASSETS: changed[ASSETS], BOOT: boot}
    for old_vrom, old_entry in files.items():
        vrom = {ACTOR: NEW_ACTOR, RELOC: NEW_RELOC}.get(old_vrom, old_vrom)
        entry = installed[vrom]
        expected = expected_changes.get(vrom, old_entry.extract(base))
        actual = entry.extract(image)
        if old_vrom == 0x19D40:  # Contains the rebuilt DMA table, not main executable code.
            expected, actual = expected[:16], actual[:16]
        if entry.index != old_entry.index or actual != expected:
            raise ValueError(f'English title loses a previous resource: {old_vrom:08X}')
    if installed[NEW_RELOC].index != installed[NEW_ACTOR].index+1:
        raise ValueError('Title loader requires adjacent actor/relocation DMA rows')
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('English title UPS reconstruction failed')
    evidence = {'version': 1, 'baseline_sha256': baseline_sha, 'source_sha256': sha256(native),
                'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'rom_bytes': len(image),
                'actor_vrom': NEW_ACTOR, 'relocation_vrom': NEW_RELOC, 'actor': profile,
                'memory': memory,
                'changed_files': {f'{v:08X}': sha256(contents) for v, contents in expected_changes.items()},
                'resident_runtime_changed': False, 'save_layout_changed': False, 'v0_candidate_changed': False,
                'status': 'Separate animated English title preview; native execution and visual acceptance pending'}
    return image, patch, evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-combined-01')
    parser.add_argument('--base', type=Path, default=ROOT/'build/collection-artwork-01')
    parser.add_argument('--overlay', type=Path, default=ROOT/'build/title-overlay-aligned')
    args = parser.parse_args()
    base, overlay = args.base, args.overlay
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(), json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        (overlay/'overlay.bin').read_bytes(), (overlay/'relocation.bin').read_bytes(),
        json.loads((overlay/'overlay.json').read_text()))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, content in (('animal-forest-title-preview.z64', image), ('animal-forest-title-preview.ups', patch),
                          ('preview.json', (json.dumps(report, indent=2)+'\n').encode())):
        with (args.output/name).open('xb') as target: target.write(content)
    print(json.dumps({k: report[k] for k in ('output_sha256', 'patch_sha256', 'rom_bytes', 'status')}, indent=2))
