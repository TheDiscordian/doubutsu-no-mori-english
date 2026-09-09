"""Guarded complete catalogue name storage and rendering integration."""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256, verified_rom

ROOT = Path(__file__).resolve().parents[1]
VROM, RELOC, RAM = 0x7A28F0, 0x7AC200, 0x808A6100
PREFIX, BSS = 39184, 12576
START = PREFIX+BSS
NEW_VROM, NEW_RELOC = 0x03970000, 0x03980000
OWNER, OWNER_RELOC, OWNER_AT = 0x7749C0, 0x7778B0, 0x2C90
OWNER_ROW = bytes.fromhex('007a28f0007ac200808a6100808b2b30808a96ac808a97c0808a92ec00000000')
SECTIONS = (14048, 25024, 112, 12576, 130)
IMPORTS = {'af_catalog_native_init': 0x808A93A8, 'af_catalog_native_name': 0x80096740,
           'af_catalog_native_draw': 0x80090E98, 'af_load_item_name': 0x801969C8}
HOOKS = {0x808A6C20: ('af_catalog_load_name', 0x80096740),
         0x808A961C: ('af_catalog_load_name', 0x80096740),
         0x808A8A9C: ('af_catalog_draw', 0x80090E98),
         0x808A9798: ('af_catalog_init', 0x808A93A8)}
APPROVED = {
    'bytes': 53584,
    'symbols': {'af_catalog_init': 51760, 'af_catalog_load_name': 51800,
                'af_catalog_name': 52068, 'af_catalog_draw': 52160},
    'suffix_sha256': '6a98c7e8b7dd97a76be8112fe9d16f9a374ab9feb5f8d2b3f7718d60d498cc4b',
    'relocation_sha256': 'e828349a5dd1b46b2df4673af1d9d3f0d1938af332c4ab1783cdcc7179831122',
    'elf_relocations': [
        [51760, 5, RAM, '.text'], [51764, 6, RAM, '.text'],
        [51768, 5, RAM, '.text'], [51772, 6, RAM, '.text'],
        [51792, 4, 0x808A93A8, 'af_catalog_native_init'],
        [51832, 4, 0x80096740, 'af_catalog_native_name'],
        [51840, 5, RAM, '.text'], [51844, 6, RAM, '.text'],
        [51900, 5, RAM, '.text'], [51904, 6, RAM, '.text'],
        [51944, 4, 0x801969C8, 'af_load_item_name'],
        [52068, 5, RAM, '.text'], [52072, 6, RAM, '.text'],
        [52084, 5, RAM, '.text'], [52088, 6, RAM, '.text'],
        [52144, 5, RAM, '.text'], [52148, 6, RAM, '.text'],
        [52176, 4, 0x808B2C64, 'af_catalog_name'],
        [52284, 4, 0x80090E98, 'af_catalog_native_draw'],
    ],
}


def source_hashes():
    return {p: sha256((ROOT/p).read_bytes()) for p in
            ('overlays/catalog/names.c', 'overlays/catalog/image.s', 'overlays/catalog/image.ld')}


def native_sources(native):
    native = verified_rom(native); files = by_vrom(native)
    data, reloc, owner, owner_reloc = [files[v].extract(native) for v in (VROM, RELOC, OWNER, OWNER_RELOC)]
    if (len(data) != PREFIX or sha256(data) != '8fad244f38141aa81de27fe539fabcc6c6d2e4ba4f60eb26fdaa6c5f601a6a6b'
            or sha256(reloc) != '49ca34e8e0a5a5726f99cfd2e9f1537f0c4e12c73f90825b65428270509ce85a'
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or sha256(owner) != 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'
            or sha256(owner_reloc) != '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
            or owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed native catalogue source or ownership')
    return data, reloc, owner, owner_reloc


def original_relocations(reloc):
    rows = []
    for (row,) in struct.iter_unpack('>I', reloc[20:20+SECTIONS[4]*4]):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid native catalogue relocation')
        rows.append((at+(0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1], kind))
    return rows


def patch_prefix(native, symbols):
    original, reloc, _, _ = native_sources(native)
    data = bytearray(original); slots = dict(original_relocations(reloc))
    for at, (name, target) in HOOKS.items():
        expected_kind = 4 if target == IMPORTS['af_catalog_native_init'] else None
        if (struct.unpack_from('>I', data, at-RAM)[0] != 0x0C000000 | (target >> 2) & 0x3FFFFFF
                or slots.get(at-RAM) != expected_kind):
            raise ValueError('Changed catalogue hook instruction or relocation')
        struct.pack_into('>I', data, at-RAM, 0x0C000000 | ((RAM+symbols[name]) >> 2) & 0x3FFFFFF)
    return bytes(data)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported catalogue ELF relocation')
        result.append([int(match[1], 16)-RAM, {'32': 2, '26': 4, 'HI16': 5, 'LO16': 6}[match[2]],
                       int(match[3], 16), match[4]])
    return result


def relocation_data(native, inventory, size):
    rows = original_relocations(native_sources(native)[1])
    rows += [(at-RAM, 4) for at in HOOKS if at != 0x808A9798]
    seen = set()
    for at, kind, target, name in inventory:
        if at in seen or at & 3 or not START <= at <= size-4 or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid appended catalogue relocation')
        seen.add(at)
        if RAM <= target < RAM+size:
            rows.append((at, kind))
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound catalogue external target')
    if len({at for at, _ in rows}) != len(rows): raise ValueError('Duplicate catalogue relocation')
    values = [0x40000000 | kind << 24 | at for at, kind in rows]
    length = (24+len(values)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(values))+struct.pack('>'+str(len(values))+'I', *values)
            +bytes(length-24-len(values)*4)+struct.pack('>I', length))


@dataclass(frozen=True)
class Image:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native, data, reloc, report, module):
    if not APPROVED: raise ValueError('Catalogue image needs independent approval')
    if (len(data) != APPROVED['bytes'] or report.get('symbols') != APPROVED['symbols']
            or report.get('bytes') != len(data) or report.get('imports') != IMPORTS
            or report.get('sources') != source_hashes()
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or data[:PREFIX] != patch_prefix(native, APPROVED['symbols']) or any(data[PREFIX:START])
            or sha256(data[START:]) != APPROVED['suffix_sha256']
            or sha256(reloc) != APPROVED['relocation_sha256']
            or report.get('elf_relocations') != APPROVED['elf_relocations']
            or reloc != relocation_data(native, report.get('elf_relocations', []), len(data))
            or int(module['symbols']['af_load_item_name'], 16) != IMPORTS['af_load_item_name']):
        raise ValueError('Changed complete catalogue image, imports, or relocation')
    return Image(RAM, len(data), struct.unpack_from('>5I', reloc))


def metadata():
    value = bytearray(OWNER_ROW)
    struct.pack_into('>4I', value, 0, NEW_VROM, NEW_VROM+APPROVED['bytes'], RAM, RAM+APPROVED['bytes'])
    return bytes(value)


def allocation(tag_size=None):
    from inventory_english import allocation as inventory
    from notice_overlay import pool_sizes
    current = inventory(tag_size); align = lambda n: (n+63) & ~63
    growth = align(APPROVED['bytes'])-align(START)
    alternative = pool_sizes(True)['alternative']+current['tag_growth']+growth
    if growth < 0 or alternative > current['combined_pool']:
        raise ValueError('Catalogue growth exceeds the installed submenu pool')
    return {'catalogue_growth': growth, 'inventory_growth': current['tag_growth'],
            'alternative_required': alternative, 'combined_pool': current['combined_pool']}


def verify_shared_parts(built, native, module, report=None):
    from inventory_english import verify_shared_parts as verify_inventory
    inventory = verify_inventory(built, native, module)
    required = allocation(inventory['resident_bytes'])
    files, originals = by_vrom(built), by_vrom(native)
    if (NEW_VROM not in files or NEW_RELOC not in files or VROM in files or RELOC in files
            or files[NEW_VROM].index != originals[VROM].index
            or files[NEW_RELOC].index != files[NEW_VROM].index+1):
        raise ValueError('Missing complete catalogue DMA pair')
    data, reloc = files[NEW_VROM].extract(built), files[NEW_RELOC].extract(built)
    if report is None:
        report = {'overlay': {**APPROVED, 'sources': source_hashes(), 'imports': IMPORTS,
                             'overlay_sha256': sha256(data)}, 'allocation': required}
    validate(native, data, reloc, report['overlay'], module)
    if files[OWNER].extract(built)[OWNER_AT:OWNER_AT+32] != metadata() or report.get('allocation') != required:
        raise ValueError('Incomplete catalogue allocation or ownership')
    return {'owner_offset': OWNER_AT, 'owner_bytes': metadata()}


def install(native, replacements, additions, relocations, module, directory, notice_report):
    from notice_overlay import verify_installation as verify_notice
    from inventory_english import VROM as TAG
    original, original_reloc, _, _ = native_sources(native); files = by_vrom(native)
    if (replacements.get(VROM, original) != original or replacements.get(RELOC, original_reloc) != original_reloc
            or VROM in relocations or RELOC in relocations
            or any(v in files or v in replacements or v in additions or v in relocations.values()
                   for v in (NEW_VROM, NEW_RELOC))):
        raise ValueError('Overlapping catalogue installation')
    data, reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text())
    validate(native, data, reloc, report, module)
    owner = bytearray(replacements.get(OWNER, files[OWNER].extract(native)))
    if owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW: raise ValueError('Changed catalogue owner row')
    owner[OWNER_AT:OWNER_AT+32] = metadata()
    if TAG not in replacements: raise ValueError('Catalogue requires the complete inventory image')
    result = {'overlay': report, 'allocation': allocation(len(replacements[TAG])), 'vrom': f'{NEW_VROM:08X}',
              'relocation_vrom': f'{NEW_RELOC:08X}', 'complete_name_slots': 63, 'new_saved_bytes': 0,
              'status': 'Complete catalogue names installed; ordinary gameplay acceptance pending'}
    changes = {VROM: data, RELOC: reloc, OWNER: bytes(owner)}; moves = {VROM: NEW_VROM, RELOC: NEW_RELOC}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_shared_parts(prospective, native, module, result)
    verify_notice(prospective, native, module, notice_report, catalogue_report=result)
    replacements.update(changes); relocations.update(moves)
    return result
