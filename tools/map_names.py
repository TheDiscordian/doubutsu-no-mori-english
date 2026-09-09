"""Complete display-only villager names in the packed native map."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256, verified_rom
from catalogue_names import Image, elf_inventory as catalogue_inventory

ROOT = Path(__file__).resolve().parents[1]
VROM, RELOC, RAM = 0x795350, 0x797870, 0x8088DBD0
PREFIX, BSS = 9504, 16256
START = PREFIX+BSS
NEW_VROM, NEW_RELOC = 0x03B00000, 0x03B10000
OWNER, OWNER_RELOC, OWNER_AT = 0x7749C0, 0x7778B0, 0x2AB0
OWNER_ROW = bytes.fromhex('00795350007978708088dbd0808940708088fbf08088fcbc8088fb4000000000')
SECTIONS = (8464, 992, 48, 16256, 114)
IMPORTS = {'af_map_native_init': 0x8088FB70, 'af_map_native_name': 0x800ACD18,
           'af_map_native_draw': 0x80090E98, 'af_load_display_name': 0x80196044}
HOOKS = {0x8088E030: ('af_map_load_name', 0x800ACD18),
         0x8088F2F0: ('af_map_draw', 0x80090E98),
         0x8088F32C: ('af_map_draw', 0x80090E98),
         0x8088FC98: ('af_map_init', 0x8088FB70)}
APPROVED = {
    'bytes': 26544,
    'symbols': {'af_map_draw': 26196, 'af_map_init': 25760,
                'af_map_load_name': 25800, 'af_map_name': 26108},
    'suffix_sha256': 'a5b2870aa29a5958be5b949b76ee772a490108a41c357dbb63a00a650fd8b15a',
    'relocation_sha256': '70eb5d92ee6f7466f420df56adfc44b2c9a9c1e70286e5380349f19695bcbf8f',
    'elf_sha256': 'f2953c5992efdc32866b69a7000f3d91112c55759eb25ddb94e3ddd8763c1510',
    'elf_relocations': [
        [25760, 5, RAM, '.text'], [25764, 6, RAM, '.text'],
        [25768, 5, RAM, '.text'], [25772, 6, RAM, '.text'],
        [25792, 4, 0x8088FB70, 'af_map_native_init'],
        [25832, 4, 0x800ACD18, 'af_map_native_name'],
        [25840, 5, RAM, '.text'], [25844, 6, RAM, '.text'],
        [25980, 4, 0x80196044, 'af_load_display_name'],
        [26116, 5, RAM, '.text'], [26120, 6, RAM, '.text'],
        [26220, 4, 0x808941CC, 'af_map_name'],
        [26320, 4, 0x80090E98, 'af_map_native_draw'],
    ],
}


def source_hashes():
    return {p: sha256((ROOT/p).read_bytes()) for p in
            ('overlays/map/names.c', 'overlays/map/image.s', 'overlays/map/image.ld')}


def native_sources(native):
    files = by_vrom(verified_rom(native))
    data, reloc, owner, owner_reloc = [files[v].extract(native) for v in (VROM, RELOC, OWNER, OWNER_RELOC)]
    if (len(data) != PREFIX or sha256(data) != 'e10dd3ba1ef1f2f29eeb8481217db927b2302811abc68884109fc9ad67210099'
            or sha256(reloc) != 'e986f18115f0585fbc82c0edd6dbb594f49088a7a2e56ca3ee4e09c9f26c008a'
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or sha256(owner) != 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'
            or sha256(owner_reloc) != '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
            or owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW
            or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed native map source or ownership')
    return data, reloc, owner, owner_reloc


def original_relocations(reloc):
    rows = []
    for (row,) in struct.iter_unpack('>I', reloc[20:20+SECTIONS[4]*4]):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid native map relocation')
        rows.append((at+(0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1], kind))
    return rows


def patch_prefix(native, symbols):
    original, reloc, _, _ = native_sources(native)
    data = bytearray(original); slots = dict(original_relocations(reloc))
    for at, (name, target) in HOOKS.items():
        expected_kind = 4 if target == IMPORTS['af_map_native_init'] else None
        if (struct.unpack_from('>I', data, at-RAM)[0] != 0x0C000000 | (target >> 2) & 0x3FFFFFF
                or slots.get(at-RAM) != expected_kind):
            raise ValueError('Changed map hook instruction or relocation')
        struct.pack_into('>I', data, at-RAM, 0x0C000000 | ((RAM+symbols[name]) >> 2) & 0x3FFFFFF)
    return bytes(data)


def elf_inventory(text):
    return catalogue_inventory(text, ram=RAM)


def relocation_data(native, inventory, size):
    rows = original_relocations(native_sources(native)[1])
    rows += [(at-RAM, 4) for at in HOOKS if at != 0x8088FC98]
    seen = set()
    for at, kind, target, name in inventory:
        if at in seen or at & 3 or not START <= at <= size-4 or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid appended map relocation')
        seen.add(at)
        if RAM <= target < RAM+size:
            rows.append((at, kind))
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound map external target')
    if len({at for at, _ in rows}) != len(rows): raise ValueError('Duplicate map relocation')
    values = [0x40000000 | kind << 24 | at for at, kind in rows]
    length = (24+len(values)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(values))+struct.pack('>'+str(len(values))+'I', *values)
            +bytes(length-24-len(values)*4)+struct.pack('>I', length))


def validate(native, data, reloc, report, module):
    if not APPROVED: raise ValueError('Map image needs independent approval')
    if (len(data) != APPROVED['bytes'] or report.get('symbols') != APPROVED['symbols']
            or report.get('bytes') != len(data) or report.get('imports') != IMPORTS
            or report.get('sources') != source_hashes()
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_sha256') != sha256(reloc)
            or data[:PREFIX] != patch_prefix(native, APPROVED['symbols']) or any(data[PREFIX:START])
            or sha256(data[START:]) != APPROVED['suffix_sha256']
            or sha256(reloc) != APPROVED['relocation_sha256']
            or sha256(json.dumps(report.get('elf_relocations'), separators=(',', ':')).encode()) != APPROVED['elf_sha256']
            or reloc != relocation_data(native, report.get('elf_relocations', []), len(data))
            or int(module['symbols']['af_load_display_name'], 16) != IMPORTS['af_load_display_name']):
        raise ValueError('Changed complete map image, imports, or relocation')
    return Image(RAM, len(data), struct.unpack_from('>5I', reloc))


def metadata():
    value = bytearray(OWNER_ROW)
    struct.pack_into('>4I', value, 0, NEW_VROM, NEW_VROM+APPROVED['bytes'], RAM, RAM+APPROVED['bytes'])
    return bytes(value)


def allocation(tag_size=None):
    from inventory_english import allocation as inventory
    from catalogue_names import START as catalog_size
    from notice_overlay import pool_sizes
    current = inventory(tag_size); align = lambda n: (n+63) & ~63
    # Map's dependency flag is zero: it opens no tag/hand/editor child. Bound it
    # conservatively by the catalogue branch, retaining even its unused tag and
    # inventory allowances and 16-KiB miscellaneous reserve.
    required = (pool_sizes(True)['alternative']+current['tag_growth']
                -align(catalog_size)+align(APPROVED['bytes']))
    if required > current['combined_pool']: raise ValueError('Map exceeds the installed submenu pool')
    return {'map_growth': align(APPROVED['bytes'])-align(START), 'conservative_required': required,
            'combined_pool': current['combined_pool'], 'extra_reservation': 0}


def verify_shared_parts(built, native, module, report=None):
    from inventory_english import verify_shared_parts as verify_inventory
    from actor_display_names import NAMES_SHA
    from display_names import VROM as names_vrom
    from runtime_module import MODULE_VROM
    inventory = verify_inventory(built, native, module)
    required = allocation(inventory['resident_bytes'])
    files, originals = by_vrom(built), by_vrom(native)
    code, native_code = files[CODE_VROM].extract(built), originals[CODE_VROM].extract(native)
    if (NEW_VROM not in files or NEW_RELOC not in files or VROM in files or RELOC in files
            or files[NEW_VROM].index != originals[VROM].index
            or files[NEW_RELOC].index != files[NEW_VROM].index+1
            or sha256(files[names_vrom].extract(built)) != NAMES_SHA
            or struct.unpack_from('>I', files[MODULE_VROM].extract(built), 60)[0] != names_vrom
            or code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM] != native_code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM]):
        raise ValueError('Missing complete map DMA pair or display-name resource')
    data, reloc = files[NEW_VROM].extract(built), files[NEW_RELOC].extract(built)
    if report is None:
        report = {'overlay': {**APPROVED, 'sources': source_hashes(), 'imports': IMPORTS,
                  'overlay_sha256': sha256(data), 'elf_relocations': APPROVED['elf_relocations']}, 'allocation': required}
    elif (report.get('complete_name_slots') != 15 or report.get('new_saved_bytes') != 0
            or report.get('vrom') != f'{NEW_VROM:08X}' or report.get('relocation_vrom') != f'{NEW_RELOC:08X}'):
        raise ValueError('Changed map name application evidence')
    validate(native, data, reloc, report['overlay'], module)
    if files[OWNER].extract(built)[OWNER_AT:OWNER_AT+32] != metadata() or report.get('allocation') != required:
        raise ValueError('Incomplete map allocation or ownership')
    return {'owner_offset': OWNER_AT, 'owner_bytes': metadata()}


def install(native, replacements, additions, relocations, module, directory, notice_report):
    from notice_overlay import verify_installation as verify_notice
    from inventory_english import VROM as TAG
    original, original_reloc, _, _ = native_sources(native); files = by_vrom(native)
    if (replacements.get(VROM, original) != original or replacements.get(RELOC, original_reloc) != original_reloc
            or VROM in relocations or RELOC in relocations
            or any(v in files or v in replacements or v in additions or v in relocations.values()
                   for v in (NEW_VROM, NEW_RELOC))):
        raise ValueError('Overlapping map installation')
    data, reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text())
    validate(native, data, reloc, report, module)
    owner = bytearray(replacements.get(OWNER, files[OWNER].extract(native)))
    if owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW: raise ValueError('Changed map owner row')
    owner[OWNER_AT:OWNER_AT+32] = metadata()
    if TAG not in replacements: raise ValueError('Map requires the complete inventory image')
    result = {'overlay': report, 'allocation': allocation(len(replacements[TAG])), 'vrom': f'{NEW_VROM:08X}',
              'relocation_vrom': f'{NEW_RELOC:08X}', 'complete_name_slots': 15, 'new_saved_bytes': 0,
              'status': 'Complete map villager names installed; ordinary gameplay acceptance pending'}
    changes = {VROM: data, RELOC: reloc, OWNER: bytes(owner)}; moves = {VROM: NEW_VROM, RELOC: NEW_RELOC}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_shared_parts(prospective, native, module, result)
    verify_notice(prospective, native, module, notice_report, map_report=result)
    replacements.update(changes); relocations.update(moves)
    return result
