"""Complete source-bound inventory labels and the ordinary full-name consumer."""
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256, verified_rom
from gc_names import symbol_data
import mail_menu as native_tag
from npc_mail_show import relocate_verified_data

ROOT = Path(__file__).resolve().parents[1]
VROM, RELOC, RAM = native_tag.VROM, native_tag.RELOC, native_tag.RAM
PREFIX, BSS = native_tag.SIZE, native_tag.BSS
START = PREFIX+BSS
NEW_VROM, NEW_RELOC = 0x03950000, 0x03960000
OWNER, OWNER_RELOC, OWNER_AT = 0x7749C0, 0x7778B0, 0x2CB0
OWNER_ROW = bytes.fromhex('00777ae000781d608086f310808796b0808787a0808789048087890400000000')
LABEL_FIRST = 0x80878AE0
LABEL_NAMES = tuple(('akeru ageru itadaku dump_mail sell okuru kakinaosu kabeniharu korewoireru '
    'zimenniueru zimennioku suteru tada tukamu tegamiwokaku nedanwotukeru present miserudake '
    'yameru heyanioku yukanisiku yomu watasu 100 1000 10000 30000 okane beru osameru '
    'zenbutukamu 1maitukamu order zimenniumeru nigasu akeru2 kesu hai iie').split())
REFERENCE_SHA = '3087c98cadfd93035732100538ab8b4c3d11d0c4f944fb0d8f4d6afe4c7b73f6'
APPROVED = {'bytes': 42800, 'loader': 0x801969C8,
            'symbols': {'af_tag_cells': 41888, 'af_tag_load_item': 42004, 'af_tag_labels': 42016},
            'helpers_sha256': '3fd37ece129440caa938dfdc2b0483c5e4a5a068017770abba77bc2d089089f0'}
HOOKS = {0x8086FAC4: ('af_tag_cells', 0x0C027070),
         0x808701EC: ('af_tag_load_item', 0x0C0259D0),
         0x808701FC: ('af_tag_cells', 0x0C027070)}
WORDS = {0x8086FAC0: (0x24050008, 0x24050010),
         0x808701F8: (0x2405000A, 0x24050010),
         0x80876D04: (0x8DF90008, 0x8DF90010),
         0x808779F0: (0x24060008, 0x24060010),
         0x80877F78: (0x24060008, 0x24060010),
         0x808783AC: (0x2406000A, 0x24060010)}


def source_hashes():
    return {p: sha256((ROOT/p).read_bytes()) for p in
            ('overlays/tag/labels.c', 'overlays/tag/image.s', 'overlays/tag/image.ld')}


def native_sources(native):
    native = verified_rom(native)
    files = by_vrom(native)
    data, reloc = native_tag.source(native)
    owner, owner_reloc = files[OWNER].extract(native), files[OWNER_RELOC].extract(native)
    if (sha256(owner) != 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'
            or sha256(owner_reloc) != '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
            or owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW
            or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed inventory ownership or adjacent relocation')
    return data, reloc, owner, owner_reloc


def reference_labels():
    rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    if (sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837'
            or sha256(symbols) != 'e5267b989d235655c51885bd2a660b3e8c2cbd46d60b2b3c46166d337c7bca87'):
        raise ValueError('Changed supplied inventory-label references')
    values = [symbol_data(rel, symbols.decode(), 'mTG_tag_word_'+name) for name in LABEL_NAMES]
    if any(len(v) != 20 for v in values) or sha256(b''.join(values)) != REFERENCE_SHA:
        raise ValueError('Changed English label identities')
    labels = [v[:16] for v in values]
    # Original translation for a missing reference; native two-line price layout
    # keeps five twelve-pixel numeric positions before the currency suffix.
    # Ten six-pixel English spaces retain that sixty-pixel starting position.
    for name, value in (('kesu', b'Delete'), ('okane', b'Price:'), ('beru', b'          Bells')):
        labels[LABEL_NAMES.index(name)] = value.ljust(16, b' ')
    if any(len(v) != 16 or any(c not in range(32, 127) for c in v) for v in labels):
        raise ValueError('Inventory label is not complete plain Latin text')
    return labels


def label_data(native):
    data = native_sources(native)[0]
    return b''.join(label+data[LABEL_FIRST-RAM+i*12+8:LABEL_FIRST-RAM+i*12+12]
                    for i, label in enumerate(reference_labels()))


def original_relocations(reloc):
    sections = native_tag.SECTIONS
    result = []
    for row in struct.unpack_from('>'+str(sections[4])+'I', reloc, 20):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid native tag relocation')
        result.append(((0, sections[0], sections[0]+sections[1])[section-1]+at, kind))
    return result


def patch_prefix(native, symbols):
    original, reloc, _, _ = native_sources(native)
    result = bytearray(original)
    for at, (before, after) in WORDS.items():
        if struct.unpack_from('>I', result, at-RAM)[0] != before:
            raise ValueError('Changed inventory instruction')
        struct.pack_into('>I', result, at-RAM, after)
    for at, (symbol, before) in HOOKS.items():
        if struct.unpack_from('>I', result, at-RAM)[0] != before:
            raise ValueError('Changed inventory helper call')
        struct.pack_into('>I', result, at-RAM, 0x0C000000 | ((RAM+symbols[symbol]) >> 2) & 0x3FFFFFF)
    mapping = {LABEL_FIRST+i*12: RAM+symbols['af_tag_labels']+i*20 for i in range(len(LABEL_NAMES))}
    slots = {at: kind for at, kind in original_relocations(reloc)}
    found = set()
    for at in range(0, len(original), 4):
        word = struct.unpack_from('>I', original, at)[0]
        if word in mapping:
            if slots.get(at) != 2:
                raise ValueError('Unrelocated inventory label pointer')
            found.add(word)
            struct.pack_into('>I', result, at, mapping[word])
    expected = {r['pointer'] for d in native_tag.definitions(original) for r in d['options']}
    # The unused fourth money option remains in its native pointer array, even
    # though the live definition exposes only the first three choices.
    if found != set(mapping) or found-expected != {0x80878C18}:
        raise ValueError('Unreviewed inventory label reference')
    return bytes(result)


def relocation_data(native, symbols, size):
    original, reloc, _, _ = native_sources(native)
    rows = original_relocations(reloc)
    if any(at+RAM in HOOKS or at+RAM in WORDS for at, _ in rows):
        raise ValueError('Unexpected original relocation at an inventory patch')
    rows += [(at-RAM, 4) for at in HOOKS]
    rows += [(symbols['af_tag_labels']+i*20+16, 2) for i in range(len(LABEL_NAMES))
             if struct.unpack_from('>I', original, LABEL_FIRST-RAM+i*12+8)[0]]
    if len({at for at, _ in rows}) != len(rows): raise ValueError('Duplicate inventory relocation')
    values = [0x40000000 | kind << 24 | at for at, kind in rows]
    length = (24+len(values)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(values))+
            struct.pack('>'+str(len(values))+'I', *values)+bytes(length-24-len(values)*4)+struct.pack('>I', length))


@dataclass(frozen=True)
class Image:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native, data, reloc, report, module):
    if report.get('descriptions'):
        from tag_descriptions import validate as validate_descriptions
        return validate_descriptions(native, data, reloc, report, module)
    if report.get('menu_text'):
        from inventory_menu_text import validate as validate_menu_text
        return validate_menu_text(native, data, reloc, report, module)
    if not APPROVED: raise ValueError('Inventory helper image needs independent approval')
    symbols = APPROVED['symbols']
    size = APPROVED['bytes']
    if (len(data) != size or report.get('symbols') != symbols or report.get('bytes') != size
            or report.get('sources') != source_hashes() or report.get('overlay_sha256') != sha256(data)
            or report.get('relocation_sha256') != sha256(reloc)
            or data[:PREFIX] != patch_prefix(native, symbols) or any(data[PREFIX:START])
            or sha256(data[START:symbols['af_tag_labels']]) != APPROVED['helpers_sha256']
            or data[symbols['af_tag_labels']:symbols['af_tag_labels']+len(LABEL_NAMES)*20] != label_data(native)
            or any(data[symbols['af_tag_labels']+len(LABEL_NAMES)*20:])
            or reloc != relocation_data(native, symbols, size)):
        raise ValueError('Changed complete inventory code, labels, or relocation')
    loader = int(module['symbols']['af_load_item_name'], 16)
    if loader != APPROVED['loader'] or report.get('loader') != loader:
        raise ValueError('Inventory item loader does not match the resident module')
    return Image(RAM, size, struct.unpack_from('>5I', reloc))


def metadata(size=None):
    row = bytearray(OWNER_ROW)
    if size is None: size = APPROVED['bytes']
    struct.pack_into('>4I', row, 0, NEW_VROM, NEW_VROM+size, RAM, RAM+size)
    return bytes(row)


def allocation(size=None):
    from hboard_overlay import APPROVED as editor, ORIGINAL_RESIDENT, POOL_EXTRA
    from notice_overlay import pool_sizes
    align = lambda n: (n+63) & ~63
    if size is None: size = APPROVED['bytes']
    growth = align(size)-align(START)
    editor_growth = align(editor['bytes'])-align(ORIGINAL_RESIDENT)
    pool = pool_sizes(True)
    if (growth < 0 or growth+editor_growth > POOL_EXTRA
            or pool['alternative']+growth > pool['expanded']+POOL_EXTRA):
        raise ValueError('Inventory growth exceeds the installed shared reservation')
    return {'tag_growth': growth, 'editor_growth': editor_growth,
            'shared_growth_used': growth+editor_growth, 'shared_growth_reserved': POOL_EXTRA,
            'combined_pool': pool['expanded']+POOL_EXTRA}


def verify_shared_parts(built, native, module, report=None):
    from runtime_module import verify_test_module
    files, original = by_vrom(built), by_vrom(native)
    verify_test_module(built, module)
    if (NEW_VROM not in files or NEW_RELOC not in files or VROM in files or RELOC in files
            or files[NEW_VROM].index != original[VROM].index
            or files[NEW_RELOC].index != files[NEW_VROM].index+1):
        raise ValueError('Missing complete inventory DMA pair')
    data, reloc = files[NEW_VROM].extract(built), files[NEW_RELOC].extract(built)
    if report is None:
        if len(data) == APPROVED['bytes']:
            overlay = {**APPROVED, 'sources': source_hashes(),
                       'overlay_sha256': sha256(data), 'relocation_sha256': sha256(reloc)}
        else:
            from inventory_menu_text import make_report, SIZE
            if len(data) == SIZE:
                overlay = make_report(native, data, reloc)
            else:
                import tag_descriptions as desc
                if len(data) != desc.APPROVED['bytes']: raise ValueError('Unknown inventory image profile')
                overlay = desc.make_report(native, data, reloc, desc.APPROVED['symbols'], None)
        report = {'overlay': overlay, 'allocation': allocation(len(data))}
    validate(native, data, reloc, report['overlay'], module)
    from extended_items import HEADER, VROM as ITEMS
    if report['overlay'].get('descriptions'):
        from display_names import VROM as NAMES, HEADER as NAME_HEADER
        from runtime_layout import MODULE_VROM
        if (NAMES not in files or files[NAMES].extract(built)[:32] != NAME_HEADER
                or files[MODULE_VROM].extract(built)[60:64] != struct.pack('>I', NAMES)):
            raise ValueError('Inventory descriptions require the complete display-name resource')
    from font import WIDTH_BRANCH, WIDTH_TABLE, make_halfwidth
    code = files[CODE_VROM].extract(built)
    expected_code = make_halfwidth(native)[0][CODE_VROM]
    pool_patch = bytes.fromhex('25cefb20')
    if 0x03B60000 in files:
        from letter_names import verify_owned_parts
        pool_patch = verify_owned_parts(built, native, module)['pool_patch']
    if (files[OWNER].extract(built)[OWNER_AT:OWNER_AT+32] != metadata(len(data))
            or files[ITEMS].extract(built)[:32] != HEADER
            or code[WIDTH_BRANCH:WIDTH_BRANCH+4] != bytes(4)
            or code[WIDTH_TABLE:WIDTH_TABLE+256] != expected_code[WIDTH_TABLE:WIDTH_TABLE+256]
            or code[0x800C4B10-CODE_RAM:0x800C4B14-CODE_RAM] != pool_patch
            or report.get('allocation') != allocation(len(data))):
        raise ValueError('Incomplete inventory font, item, or allocation dependencies')
    return {'owner_offset': OWNER_AT, 'owner_bytes': metadata(len(data)), 'resident_bytes': len(data)}


def install(native, replacements, additions, relocations, module, directory, notice_report):
    from notice_overlay import verify_installation as verify_notice
    original, original_reloc, _, _ = native_sources(native)
    files = by_vrom(native)
    if (replacements.get(VROM, original) != original or replacements.get(RELOC, original_reloc) != original_reloc
            or any(v in files or v in additions or v in replacements or v in relocations.values()
                   for v in (NEW_VROM, NEW_RELOC)) or VROM in relocations or RELOC in relocations):
        raise ValueError('Overlapping inventory installation')
    data, reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text())
    validate(native, data, reloc, report, module)
    owner = bytearray(replacements.get(OWNER, files[OWNER].extract(native)))
    if owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW: raise ValueError('Changed inventory owner row')
    owner[OWNER_AT:OWNER_AT+32] = metadata(len(data))
    result = {'overlay': report, 'allocation': allocation(len(data)), 'label_records': len(LABEL_NAMES),
              'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOC:08X}',
              'new_saved_bytes': 0, 'new_resident_module_bytes': 0,
              'status': 'Complete labels and ordinary item names installed; normal gameplay acceptance pending'}
    changes = {VROM: data, RELOC: reloc, OWNER: bytes(owner)}
    moves = {VROM: NEW_VROM, RELOC: NEW_RELOC}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_shared_parts(prospective, native, module, result)
    verify_notice(prospective, native, module, notice_report, inventory_report=result)
    replacements.update(changes); relocations.update(moves)
    return result
