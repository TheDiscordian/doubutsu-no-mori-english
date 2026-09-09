"""Owned proportional gyroid editor, window bridge, and shared allocation checks."""

from dataclasses import dataclass
import json
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256
from hboard_editor import (ROOT, EDITOR, EDITOR_RELOC, EDITOR_RAM as RAM, HBOARD,
                           HBOARD_RELOC, HBOARD_RAM, OWNER, OWNER_RELOC, METADATA,
                           native_sources, audit)
from keyboard import english_editor
from npc_mail_show import relocate_verified_data

PREFIX, ORIGINAL_RESIDENT, CODE_START = 0x39B0, 0x39E0, 0x39F0
NEW_VROM, NEW_RELOCATION = 0x03940000, 0x03948000
POOL_EXTRA = 0x2000
WINDOW_BRIDGE = 0x80882D08
IMPORTS = {'af_hboard_original_init': 0x8088587C, 'af_hboard_original_cursor': 0x80885AEC,
           'af_hboard_original_done': 0x808860A0, 'af_hboard_original_destruct': 0x808884E4,
           'af_hboard_code_width': 0x8009028C, 'af_hboard_font_line': 0x80090E98}
HOOKS = {0x80888484: ('af_hboard_editor_init', 0x8088587C, 4),
         0x808869A4: ('af_hboard_editor_cursor', 0x80885AEC, 4),
         0x80888828: ('af_hboard_editor_command', 0x808862EC, 2)}
KINDS = {'32': 2, '26': 4, 'HI16': 5, 'LO16': 6}
# Independent compiler output is pinned before the image can be installed.
APPROVED = {
    'bytes': 20416, 'code_end': 19360, 'bss_start': 19936,
    'suffix_sha256': '2057042c1ffa3b96ff063496d10a1e38c2408685dd0c1ac5353c5b752379470d',
    'relocation_bytes': 1440,
    'relocation_sha256': 'a7b8a96e5b090f95be9cf85c6258117de29fc8f0edcc28186a0666b72150c3ab',
    'symbols': {
        'af_hboard_begin': 15788, 'af_hboard_command': 16044, 'af_hboard_commit': 17028,
        'af_hboard_context': 19936, 'af_hboard_editor_command': 18672,
        'af_hboard_editor_cursor': 19108, 'af_hboard_editor_destruct': 19288,
        'af_hboard_editor_draw': 17432, 'af_hboard_editor_init': 18248,
        'af_hboard_english_default': 19424, 'af_hboard_layout': 14960,
        'af_hboard_native_default': 19360, 'af_hboard_pack': 16752,
    },
}


def source_hashes():
    paths = ['overlays/hboard/'+name for name in ('editor.c', 'editor.h', 'editor.s', 'editor.ld', 'window.s')]
    paths += ['runtime/hboard_editor.c', 'runtime/hboard_editor.h', 'tools/hboard_editor.py']
    return {name: sha256((ROOT/name).read_bytes()) for name in paths}


def window_bytes():
    return struct.pack('>13I', 0x8C88002C, 0x3C090001, 0x01094021, 0x8D0806E0,
                       0x11000006, 0, 0x8D190030, 0x13200003, 0, 0x03200008, 0, 0x03E00008, 0)


def patch_window(native):
    sources = native_sources(native)
    result = bytearray(sources[HBOARD]); at = WINDOW_BRIDGE-HBOARD_RAM
    reloc = sources[HBOARD_RELOC]; sections = struct.unpack_from('>5I', reloc)
    for row in struct.unpack_from('>'+str(sections[4])+'I', reloc, 20):
        section, offset = row >> 30, row & 0xFFFFFF
        offset += (0, sections[0], sections[0]+sections[1])[section-1]
        if at <= offset < at+len(window_bytes()): raise ValueError('Window bridge overlaps a native relocation')
    result[at:at+len(window_bytes())] = window_bytes()
    return bytes(result)


def patch_editor(native, symbols):
    sources = native_sources(native); result = bytearray(english_editor(sources[EDITOR]))
    rows = {}
    original = sources[EDITOR_RELOC]; sections = struct.unpack_from('>5I', original)
    for row in struct.unpack_from('>'+str(sections[4])+'I', original, 20):
        section, offset = row >> 30, row & 0xFFFFFF
        offset += (0, sections[0], sections[0]+sections[1])[section-1]
        rows[RAM+offset] = (row >> 24) & 63
    for address, (name, before, kind) in HOOKS.items():
        offset = symbols.get(name)
        if type(offset) is not int or offset & 3 or not CODE_START <= offset < ORIGINAL_RESIDENT+POOL_EXTRA:
            raise ValueError('Missing owned editor hook')
        expected = before if kind == 2 else 0x0C000000 | ((before >> 2) & 0x3FFFFFF)
        if struct.unpack_from('>I', result, address-RAM)[0] != expected or rows.get(address) != kind:
            raise ValueError('Changed native editor hook or relocation')
        after = RAM+offset if kind == 2 else 0x0C000000 | (((RAM+offset) >> 2) & 0x3FFFFFF)
        struct.pack_into('>I', result, address-RAM, after)
    return bytes(result)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported owner-editor ELF relocation')
        result.append([int(match[1], 16)-RAM, KINDS[match[2]], int(match[3], 16), match[4]])
    return result


def relocation_bytes(original, inventory, size):
    sections = struct.unpack_from('>5I', original); rows = []
    for row in struct.unpack_from('>'+str(sections[4])+'I', original, 20):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in KINDS.values(): raise ValueError('Invalid native editor relocation')
        at += (0, sections[0], sections[0]+sections[1])[section-1]
        rows.append(0x40000000 | kind << 24 | at)
    seen = set()
    for at, kind, target, name in inventory:
        if at in seen or at & 3 or not CODE_START <= at <= size-4 or kind not in KINDS.values():
            raise ValueError('Invalid appended owner-editor relocation')
        seen.add(at)
        if RAM <= target < RAM+size:
            rows.append(0x40000000 | kind << 24 | at)
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound owner-editor external target')
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate owner-editor relocation')
    length = (24+len(rows)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I', length))


@dataclass(frozen=True)
class Image:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native, data, reloc, report=None):
    sources = native_sources(native)
    if not APPROVED: raise ValueError('Owner-editor compiler image is not independently approved yet')
    size, symbols = APPROVED['bytes'], APPROVED['symbols']
    if (len(data) != size or size & 15 or not CODE_START < size <= ORIGINAL_RESIDENT+POOL_EXTRA
            or data[:PREFIX] != patch_editor(native, symbols) or any(data[PREFIX:CODE_START])
            or sha256(data[CODE_START:]) != APPROVED['suffix_sha256']
            or len(reloc) != APPROVED['relocation_bytes']
            or sha256(reloc) != APPROVED['relocation_sha256']
            or any(data[APPROVED['bss_start']:])):
        raise ValueError('Changed complete owner-editor code, state, or relocation')
    if report is not None:
        for key, value in APPROVED.items():
            if report.get(key) != value: raise ValueError('Changed owner-editor build field: '+key)
        if (report.get('version') != 1 or report.get('ram') != RAM or report.get('sources') != source_hashes()
                or report.get('overlay_sha256') != sha256(data) or report.get('imports') != IMPORTS
                or report.get('approval') != audit(native)
                or reloc != relocation_bytes(sources[EDITOR_RELOC], report.get('elf_relocations', []), size)):
            raise ValueError('Stale owner-editor build, references, or imports')
    spec = Image(RAM, size, struct.unpack_from('>5I', reloc))
    old_spec = Image(RAM, ORIGINAL_RESIDENT, struct.unpack_from('>5I', sources[EDITOR_RELOC]))
    for base in (0x801A0000, 0x802F8010, (0x80400000-size) & ~15):
        moved = relocate_verified_data(spec, data, reloc, base)
        old = relocate_verified_data(old_spec, english_editor(sources[EDITOR]), sources[EDITOR_RELOC], base)
        for at in range(0, ORIGINAL_RESIDENT, 4):
            if RAM+at not in HOOKS and moved[at:at+4] != old[at:at+4]:
                raise ValueError('Owner-editor growth changes unrelated native code or state')
    return spec


def metadata():
    value = bytearray(METADATA[EDITOR][1])
    struct.pack_into('>4I', value, 0, NEW_VROM, NEW_VROM+APPROVED['bytes'], RAM, RAM+APPROVED['bytes'])
    struct.pack_into('>I', value, 20, RAM+APPROVED['symbols']['af_hboard_editor_destruct'])
    return bytes(value)


def verify_shared_parts(built, native):
    """No recursive notice validation: return the exact permitted shared edits."""
    files, originals = by_vrom(built), by_vrom(native)
    if (NEW_VROM not in files or NEW_RELOCATION not in files or EDITOR in files or EDITOR_RELOC in files
            or files[NEW_VROM].index != originals[EDITOR].index
            or files[NEW_RELOCATION].index != files[NEW_VROM].index+1):
        raise ValueError('Missing complete owner-editor DMA ownership')
    validate(native, files[NEW_VROM].extract(built), files[NEW_RELOCATION].extract(built))
    if (files[HBOARD].extract(built) != patch_window(native)
            or files[HBOARD_RELOC].extract(built) != originals[HBOARD_RELOC].extract(native)):
        raise ValueError('Missing complete owner-message window bridge')
    at = METADATA[EDITOR][0]
    if files[OWNER].extract(built)[at:at+32] != metadata():
        raise ValueError('Missing owner-editor allocation or destructor')
    return {'owner_offset': at, 'owner_bytes': metadata(), 'pool_extra': POOL_EXTRA}


def install(native, replacements, additions, relocations, module, directory, notice_report, default_report):
    from notice_overlay import POOL_PATCH, SEASONAL_GROWTH, pool_sizes, verify_installation as verify_notice
    from gyroid_default_actor import verify_installation as verify_default
    originals = native_sources(native)
    if not notice_report.get('overlay', {}).get('seasonal') or not default_report:
        raise ValueError('Owner editor requires the complete seasonal build and visitor default')
    if (replacements.get(EDITOR) != english_editor(originals[EDITOR])
            or replacements.get(EDITOR_RELOC, originals[EDITOR_RELOC]) != originals[EDITOR_RELOC]
            or replacements.get(HBOARD, originals[HBOARD]) != originals[HBOARD]
            or replacements.get(HBOARD_RELOC, originals[HBOARD_RELOC]) != originals[HBOARD_RELOC]
            or any(v in relocations for v in (EDITOR, EDITOR_RELOC))):
        raise ValueError('Overlapping owner-editor or window edits')
    files = by_vrom(native)
    for v in (NEW_VROM, NEW_RELOCATION):
        if v in files or any(v in m for m in (replacements, additions, relocations)) or v in relocations.values():
            raise ValueError('Occupied owner-editor DMA range')
    data = (directory/'overlay.bin').read_bytes(); reloc = (directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text())
    validate(native, data, reloc, report)
    owner = bytearray(replacements.get(OWNER, originals[OWNER])); at = METADATA[EDITOR][0]
    if owner[at:at+32] != METADATA[EDITOR][1]: raise ValueError('Overlapping owner-editor allocation metadata')
    owner[at:at+32] = metadata()
    code = bytearray(replacements[CODE_VROM])
    if struct.unpack_from('>I', code, POOL_PATCH-CODE_RAM)[0] != 0x25CEDB20:
        raise ValueError('Owner editor requires the verified seasonal submenu allocation')
    struct.pack_into('>I', code, POOL_PATCH-CODE_RAM, 0x25CEFB20)
    changes = {EDITOR: data, EDITOR_RELOC: reloc, HBOARD: patch_window(native), OWNER: bytes(owner), CODE_VROM: bytes(code)}
    moves = {EDITOR: NEW_VROM, EDITOR_RELOC: NEW_RELOCATION}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_shared_parts(prospective, native)
    verify_notice(prospective, native, module, notice_report)
    verify_default(prospective, native, module, default_report)
    pool = pool_sizes(True)
    result = {'overlay': report, 'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOCATION:08X}',
              'additional_editor_bytes': len(data)-ORIGINAL_RESIDENT, 'pool_additional_bytes': POOL_EXTRA,
              'combined_submenu_pool_bytes': pool['expanded']+POOL_EXTRA,
              'combined_submenu_growth': SEASONAL_GROWTH+POOL_EXTRA,
              'new_saved_bytes': 0, 'new_resident_module_bytes': 0,
              'status': 'Complete owner-editor installed; native interaction, save/reload, and hardware remain'}
    replacements.update(changes); relocations.update(moves)
    return result
