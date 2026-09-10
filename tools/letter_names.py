"""Owned full-name letter header and cursor with unchanged saved mail fields."""
import json
from functools import lru_cache
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from catalogue_names import Image, elf_inventory as inventory
from mail_view_patch import CALLS, SNAPSHOT_CALLS, remove_call_relocations
from mail_viewer import evidence as native_evidence
from shop_item_names import jump
from runtime_module import MODULE_VROM, verify_test_module

ROOT = Path(__file__).resolve().parents[1]
STEM, EXPORT_PREFIX = 'letter_names', 'af_letter_'
VROM, RELOC, RAM = 0x007908A0, 0x00792610, 0x80888E90
PREFIX, START, SECTIONS = 7536, 7728, (0x1910, 0x430, 0x30, 0xC0, 52)
NEW_VROM, NEW_RELOC = 0x03B60000, 0x03B70000
OWNER, OWNER_RELOC, OWNER_AT = 0x007749C0, 0x007778B0, 0x2B90
OWNER_ROW = bytes.fromhex('007908a00079261080888e908088acc08088a6e88088a77c8088a2a000000000')
HEADER, CURSOR_CALL = 0x80889CD8, 0x8088A114
POOL_PATCH, POOL_EXTRA, POOL_WORD = 0x800C4B10, 4096, 0x25CE0B20
READ_HOOKS = {'af_mail_body_hook': 0x80194C60, 'af_mail_footer_hook': 0x80194C84,
              'af_mail_header_hook': 0x80194CB4, 'af_mail_copy_hook': 0x80194CD8,
              'af_mail_reader_trigger': 0x8019887C}
IMPORTS = {'af_load_display_name': 0x80196044, 'af_letter_code_width': 0x8009028C,
           'af_mail_draw': 0x8019923C,
           'af_letter_native_cursor': 0x80889878, 'af_letter_native_point': 0x8088973C}
APPROVED = {
    'bytes': 9232,
    'symbols': {'af_letter_cursor': 8692, 'af_letter_header': 7828, 'af_letter_prefix_width': 7728},
    'suffix_sha256': 'cd5dea7d176245e0ed4f89c3f841dc4d8889f1505732a079209615fa333846e1',
    'relocation_sha256': 'dea6b26c39d41bf5fd04a9530f5613e995823978a97deee85d1b05364252835b',
    'elf_relocations': [
        [7808, 4, 2148074124, 'af_letter_code_width'], [8096, 4, 2149159484, 'af_mail_draw'],
        [8236, 4, 2149146692, 'af_load_display_name'], [8300, 4, 2149159484, 'af_mail_draw'],
        [8312, 4, 2156440768, 'af_letter_prefix_width'],
        [8336, 5, 2156433040, '.text'], [8340, 6, 2156433040, '.text'],
        [8360, 5, 2156433040, '.text'], [8364, 6, 2156433040, '.text'],
        [8392, 4, 2149159484, 'af_mail_draw'], [8416, 5, 2156433040, '.text'],
        [8420, 6, 2156433040, '.text'], [8584, 4, 2149159484, 'af_mail_draw'],
        [8820, 4, 2156435576, 'af_letter_native_cursor'],
        [8868, 4, 2156440768, 'af_letter_prefix_width'], [8888, 5, 2156433040, '.text'],
        [8892, 6, 2156433040, '.text'], [8976, 4, 2156435260, 'af_letter_native_point'],
        [9000, 4, 2156440768, 'af_letter_prefix_width'], [9020, 5, 2156433040, '.text'],
        [9024, 6, 2156433040, '.text'], [9032, 5, 2156433040, '.text'],
        [9036, 6, 2156433040, '.text'], [9072, 5, 2156433040, '.text'],
        [9076, 6, 2156433040, '.text'], [9088, 5, 2156433040, '.text'], [9092, 6, 2156433040, '.text'],
    ],
}


def source_hashes():
    return {name: sha256((ROOT/name).read_bytes()) for name in
            ('overlays/letter_names/names.c', 'overlays/letter_names/image.s', 'overlays/letter_names/image.ld')}


def native_sources(native):
    verified_rom(native); native_evidence(native); files = by_vrom(native)
    data, reloc, owner, owner_reloc = [files[v].extract(native) for v in (VROM, RELOC, OWNER, OWNER_RELOC)]
    if (len(data) != PREFIX or struct.unpack_from('>5I', reloc) != SECTIONS
            or sha256(owner) != 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'
            or sha256(owner_reloc) != '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
            or owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed native letter editor or allocation owner')
    remove_call_relocations(reloc, snapshots=True)
    return data, reloc, owner, owner_reloc


@lru_cache(maxsize=1)
def audit_entry(native):
    from code_sections import code_segments
    verified_rom(native); segments, definitions = code_segments()
    if VROM not in segments or len(segments) < 100:
        raise ValueError('Incomplete letter header executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            if word == HEADER+4: raise ValueError('Literal reference into the replaced header entry')
            if not segment or not segment.is_text(offset): continue
            pc, op, targets = segment.ram+offset, word >> 26, []
            if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
            if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                displacement = (word & 65535)-(65536 if word & 32768 else 0)
                targets.append(pc+4+4*displacement)
            if HEADER+4 in targets: raise ValueError('Native branch into the replaced header entry')
    return {'external_interior_references': [], 'definition_sha256': definitions}


def preceding(native):
    data, reloc, _, _ = native_sources(native); result = bytearray(data)
    for address, old, symbol in CALLS+SNAPSHOT_CALLS:
        if struct.unpack_from('>I', result, address-RAM)[0] != jump(old, link=True):
            raise ValueError('Changed preceding letter reader call')
        struct.pack_into('>I', result, address-RAM, jump(READ_HOOKS[symbol], link=True))
    return bytes(result), remove_call_relocations(reloc, snapshots=True)


def patch_prefix(native, symbols):
    data = bytearray(preceding(native)[0])
    if (struct.unpack_from('>2I', data, HEADER-RAM) != (0x27BDFF80, 0xF7B40040)
            or struct.unpack_from('>I', data, CURSOR_CALL-RAM)[0] != jump(IMPORTS['af_letter_native_cursor'], link=True)):
        raise ValueError('Changed letter editor entry or cursor call')
    struct.pack_into('>2I', data, HEADER-RAM, jump(RAM+symbols['af_letter_header']), 0)
    struct.pack_into('>I', data, CURSOR_CALL-RAM, jump(RAM+symbols['af_letter_cursor'], link=True))
    return bytes(data)


def elf_inventory(text):
    return inventory(text, RAM)


def relocation_data(native, entries, size):
    reloc = preceding(native)[1]; count = struct.unpack_from('>I', reloc, 16)[0]; rows = []
    for (row,) in struct.iter_unpack('>I', reloc[20:20+4*count]):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6): raise ValueError('Unknown letter relocation')
        at += (0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1]
        if HEADER-RAM <= at < HEADER-RAM+8: raise ValueError('Unexpected letter header entry relocation')
        rows.append((at, kind))
    if rows.count((CURSOR_CALL-RAM, 4)) != 1: raise ValueError('Missing native cursor call relocation')
    rows.append((HEADER-RAM, 4)); seen = set()
    for at, kind, target, symbol in entries:
        if at in seen or at & 3 or not START <= at <= size-4 or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid appended letter relocation')
        seen.add(at)
        if RAM <= target < RAM+size: rows.append((at, kind))
        elif IMPORTS.get(symbol) != target or kind != 4: raise ValueError('Unbound letter import')
    if len({at for at, _ in rows}) != len(rows): raise ValueError('Duplicate letter relocation')
    values = [0x40000000 | kind << 24 | at for at, kind in rows]; length = (24+len(values)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(values))+struct.pack('>'+str(len(values))+'I', *values)
            +bytes(length-24-len(values)*4)+struct.pack('>I', length))


def validate(native, data, reloc, report, module):
    if not APPROVED: raise ValueError('Letter-name image requires independent compiled approval')
    audit_entry(native)
    if (len(data) != APPROVED['bytes'] or report.get('bytes') != len(data)
            or report.get('symbols') != APPROVED['symbols'] or report.get('sources') != source_hashes()
            or report.get('imports') != IMPORTS or report.get('overlay_sha256') != sha256(data)
            or report.get('suffix_sha256') != APPROVED['suffix_sha256']
            or sha256(data[START:]) != APPROVED['suffix_sha256']
            or data[:PREFIX] != patch_prefix(native, APPROVED['symbols']) or any(data[PREFIX:START])
            or sha256(reloc) != APPROVED['relocation_sha256']
            or report.get('relocation_sha256') != sha256(reloc)
            or report.get('elf_relocations') != APPROVED['elf_relocations']
            or reloc != relocation_data(native, report['elf_relocations'], len(data))):
        raise ValueError('Changed complete letter name image or relocation')
    for symbol, address in {**READ_HOOKS, **IMPORTS}.items():
        if 0x801948E0 <= address < 0x8019C8E0 and int(module['symbols'].get(symbol, '0'), 16) != address:
            raise ValueError('Changed resident letter-name import')
    return Image(RAM, len(data), struct.unpack_from('>5I', reloc))


def metadata():
    value = bytearray(OWNER_ROW)
    struct.pack_into('>4I', value, 0, NEW_VROM, NEW_VROM+APPROVED['bytes'], RAM, RAM+APPROVED['bytes'])
    return bytes(value)


def allocation(tag_size):
    from inventory_english import allocation as inventory_allocation
    from notice_overlay import pool_sizes
    current = inventory_allocation(tag_size); align = lambda n: (n+63) & ~63
    growth = align(APPROVED['bytes'])-align(START)
    used = current['shared_growth_used']+growth
    if growth < 0 or used > current['shared_growth_reserved']+POOL_EXTRA:
        raise ValueError('Letter names exceed the complete shared submenu reservation')
    return {'letter_growth': growth, 'combined_growth_used': used, 'extra_pool_bytes': POOL_EXTRA,
            'combined_pool_bytes': current['combined_pool']+POOL_EXTRA,
            'conservative_required': pool_sizes(True)['expanded']+used}


def verify_owned_parts(built, native, module, report=None):
    # This half has no recursive inventory dependency: the inventory verifier
    # uses it to bind the only approved extension to its original pool word.
    from inventory_english import NEW_VROM as TAG_VROM
    from actor_display_names import NAMES_SHA, NAMES_VROM
    verify_test_module(built, module); files, originals = by_vrom(built), by_vrom(native)
    if (VROM in files or RELOC in files or NEW_VROM not in files or NEW_RELOC not in files
            or files[NEW_VROM].index != originals[VROM].index or files[NEW_RELOC].index != originals[RELOC].index
            or sha256(files[NAMES_VROM].extract(built)) != NAMES_SHA
            or struct.unpack_from('>I', files[MODULE_VROM].extract(built), 60)[0] != NAMES_VROM):
        raise ValueError('Missing complete letter-editor names and native DMA positions')
    data, reloc = files[NEW_VROM].extract(built), files[NEW_RELOC].extract(built)
    overlay = {**APPROVED, 'sources': source_hashes(), 'imports': IMPORTS,
               'overlay_sha256': sha256(data)} if report is None else report['overlay']
    validate(native, data, reloc, overlay, module)
    needed = allocation(len(files[TAG_VROM].extract(built))); code = files[CODE_VROM].extract(built)
    pool_word = POOL_WORD
    from hboard_overlay import NEW_VROM as EDITOR_VROM, APPROVED as EDITOR
    if len(files[EDITOR_VROM].extract(built)) != EDITOR['bytes']:
        from apology_overlay import verify_owned_parts as verify_apology, POOL_WORD as APOLOGY_POOL
        pool_word = verify_apology(built, native).get('pool_word', APOLOGY_POOL)
    if (files[OWNER].extract(built)[OWNER_AT:OWNER_AT+32] != metadata()
            or struct.unpack_from('>I', code, POOL_PATCH-CODE_RAM)[0] != pool_word
            or struct.unpack_from('>I', code, 0x800C4AFC-CODE_RAM)[0] != 0x3C0E8089
            or report is not None and report.get('allocation') != needed):
        raise ValueError('Missing complete letter-editor allocation')
    return {'owner_offset': OWNER_AT, 'owner_bytes': metadata(), 'pool_patch': struct.pack('>I', pool_word),
            'allocation': needed}


def verify_shared_parts(built, native, module, report=None):
    from inventory_english import verify_shared_parts as verify_inventory
    result = verify_owned_parts(built, native, module, report)
    verify_inventory(built, native, module)
    return result


def install(native, replacements, additions, relocations, module, directory):
    files = by_vrom(native); original, reloc = preceding(native)
    if (replacements.get(VROM) != original or replacements.get(RELOC) != reloc
            or VROM in relocations or RELOC in relocations
            or any(v in files or v in replacements or v in additions or v in relocations.values() for v in (NEW_VROM, NEW_RELOC))):
        raise ValueError('Letter editor requires the unchanged complete preceding reader')
    data, new_reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    overlay = json.loads((directory/'overlay.json').read_text()); validate(native, data, new_reloc, overlay, module)
    owner, code = bytearray(replacements[OWNER]), bytearray(replacements[CODE_VROM])
    if (owner[OWNER_AT:OWNER_AT+32] != OWNER_ROW
            or struct.unpack_from('>I', code, POOL_PATCH-CODE_RAM)[0] != 0x25CEFB20
            or struct.unpack_from('>I', code, 0x800C4AFC-CODE_RAM)[0] != 0x3C0E8089):
        raise ValueError('Overlapping letter ownership or submenu pool')
    from inventory_english import VROM as TAG_VROM
    needed = allocation(len(replacements[TAG_VROM]))
    owner[OWNER_AT:OWNER_AT+32] = metadata(); struct.pack_into('>I', code, POOL_PATCH-CODE_RAM, POOL_WORD)
    replacements.update({VROM: data, RELOC: new_reloc, OWNER: bytes(owner), CODE_VROM: bytes(code)})
    relocations.update({VROM: NEW_VROM, RELOC: NEW_RELOC})
    return {'overlay': overlay, 'allocation': needed, 'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOC:08X}',
            'name_bytes': 8, 'name_gap_pixels': 80, 'new_saved_bytes': 0, 'new_resident_module_bytes': 0}


def verify_installation(built, native, report):
    entry = report['letter_editor_names']; verify_shared_parts(built, native, report['runtime_module'], entry)
    if (entry.get('vrom') != f'{NEW_VROM:08X}' or entry.get('relocation_vrom') != f'{NEW_RELOC:08X}'
            or entry.get('name_bytes') != 8 or entry.get('name_gap_pixels') != 80
            or entry.get('new_saved_bytes') != 0 or entry.get('new_resident_module_bytes') != 0):
        raise ValueError('Incomplete letter-editor name evidence')
    for old, new in ((VROM, NEW_VROM), (RELOC, NEW_RELOC)):
        if report.get('vrom_relocations', {}).get(f'{old:08X}') != f'{new:08X}':
            raise ValueError('Missing letter-editor DMA evidence')
    return entry
