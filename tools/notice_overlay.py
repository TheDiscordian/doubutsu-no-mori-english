"""Guarded native notice creation, reader ownership, and relocation installation."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256, verified_rom
from audit_noticeboard import audit, INITIAL_IDS, OVERLAY_HASH, INIT_HASH
from english_runtime import GuardedCode, SOURCE_HASHES
from mail_record import Record
from notice_record import pack
from npc_mail_show import relocate_verified_data

ROOT = Path(__file__).resolve().parents[1]
RAM, VROM, RELOCATION = 0x80894250, 0x797A50, 0x799450
PREFIX, RESIDENT, GROWTH = 0x1A00, 0x1A80, 0x4000
NEW_VROM, NEW_RELOCATION = 0x03920000, 0x03928000
OWNER_RAM, OWNER_VROM, OWNER_RELOCATION = 0x8085BAC0, 0x7749C0, 0x7778B0
METADATA = 0x2AD0
METADATA_BYTES = bytes.fromhex('00797a50007994508089425080895cd080895b0480895b9c80895a3000000000')
INIT_START, INIT_END, INIT_TABLE = 0x800A5BC4, 0x800A5CB0, 0x8010B4A0
POOL_START, POOL_END, POOL_PATCH = 0x800C49D4, 0x800C4C60, 0x800C4B10
MODULE_HASH = '493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
# Independently pinned compiled code/data, loader records, and creator encoding.
SUFFIX_HASH = '135b72f54e35ee7b29b673a8e41d92987c5902fcebc0ce69ccc415a7a87fe098'
RELOC_HASH = 'dabe4c9ad7f3ac3ef7649e513e70958acd66b41597f1fc530c13e1931d96c59c'
INITIAL_HASH = '59816fc8421e5332a082ed94c7adc09c7c7cc0cc171c9d89b14ecbec6e478940'
EXPECTED_SYMBOLS = {
    'af_notice_cache': 11392, 'af_notice_construct': 9196, 'af_notice_draw_body': 9588,
    'af_notice_draw_date': 10740, 'af_notice_draw_entry': 10572, 'af_notice_initial_pack': 7284,
    'af_notice_initial_restore': 7384, 'af_notice_page': 8008, 'af_notice_read_control': 9252,
    'af_notice_record_expand': 7036, 'af_notice_record_pack': 6848, 'af_notice_record_tagged': 6784,
}
KINDS = {'32': 2, '26': 4, 'HI16': 5, 'LO16': 6}
NATIVE_IMPORTS = {'af_notice_original_construct': 0x80895B04,
                  'af_notice_original_read': 0x80894560, 'af_notice_original_body': 0x8089542C}
MODULE_IMPORTS = {'af_crc32': 0x80195938, 'af_format_month': 0x80195CC0,
                  'af_mail_draw': 0x8019923C, 'af_mail_next_line': 0x801992A8,
                  'af_mail_record_pack': 0x80198DD4, 'af_mail_record_unpack': 0x80198FDC,
                  'af_mail_restore': 0x80196C28}
CALLS = {0x80895750: ('af_notice_draw_entry', 0x80895298),
         0x80895768: ('af_notice_draw_date', 0x80895328),
         0x808957C0: ('af_notice_draw_body', 0x8089542C)}


def source_hashes():
    paths = ['overlays/notice/'+name for name in ('reader.c', 'reader.h', 'reader.s', 'reader.ld', 'initial.s')]
    paths += ['runtime/notice/'+name+suffix for name in ('record', 'initial', 'page') for suffix in ('.c', '.h')]
    paths += ['runtime/mail/'+name+'.h' for name in ('record', 'format', 'catalog', 'glyph', 'view')]
    paths += ['runtime/dateformat.h', 'runtime/crc32.h', 'tools/audit_noticeboard.py', 'tools/notice_record.py']
    return {name: sha256((ROOT/name).read_bytes()) for name in paths}


def imports(module):
    if (module['module_sha256'] != MODULE_HASH
            or any(int(module['symbols'][name], 16) != address for name, address in MODULE_IMPORTS.items())):
        raise ValueError('Notice reader requires its verified resident imports')
    return {**NATIVE_IMPORTS, **MODULE_IMPORTS}


def native_sources(native):
    native = verified_rom(native)
    files = by_vrom(native)
    data, reloc, owner, owner_reloc = (files[vrom].extract(native)
                                      for vrom in (VROM, RELOCATION, OWNER_VROM, OWNER_RELOCATION))
    code = files[CODE_VROM].extract(native)
    if (sha256(data) != OVERLAY_HASH or len(data) != PREFIX
            or sha256(reloc) != 'ee227ce7f6a375c0f3e5bb77aa93ffd76ee33e0d846ea44d70b47620a557169c'
            or struct.unpack_from('>5I', reloc) != (6512, 112, 32, 128, 69)
            or sha256(owner) != 'ff0c90d15d6e17baa1eee5acdf86cf1fe8af9ce5479acc8f6e55d731fc837a20'
            or sha256(owner_reloc) != '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
            or owner[METADATA:METADATA+32] != METADATA_BYTES
            or sha256(code[INIT_START-CODE_RAM:INIT_END-CODE_RAM]) != INIT_HASH
            or sha256(code[POOL_START-CODE_RAM:POOL_END-CODE_RAM]) != '1eb33510e5438cb377c1a7408321b5b60558325b14e006105bd435dc8a73e6c4'
            or struct.unpack_from('>4I', code, INIT_TABLE-CODE_RAM) != INITIAL_IDS
            or files[RELOCATION].index != files[VROM].index+1):
        raise ValueError('Changed native notice code, ownership, or allocation')
    sections = struct.unpack_from('>5I', owner_reloc)
    for row in struct.unpack_from('>'+str(sections[4])+'I', owner_reloc, 20):
        section, at = row >> 30, row & 0xFFFFFF
        at += (0, 0, sections[0], sections[0]+sections[1])[section]
        if METADATA <= at < METADATA+32: raise ValueError('Unexpected external notice metadata relocation')
    return data, reloc, owner, owner_reloc


def audit_editor(native, current=None):
    from keyboard import EDITOR_VROM, SOURCE_HASHES as KEYBOARD_HASHES, english_editor
    data = by_vrom(native)[EDITOR_VROM].extract(native)
    ram = 0x80885140
    if sha256(data) != KEYBOARD_HASHES[EDITOR_VROM]: raise ValueError('Changed native notice editor')
    if current is not None and current != english_editor(data): raise ValueError('Changed English notice editor')
    pointers = struct.unpack_from('>5I', data, 0x808885C8-ram)
    counts = struct.unpack_from('>5I', data, 0x808885DC-ram)
    table = data[0x80888710-ram:0x80888810-ram]
    if (counts != (50, 30, 50, 30, 10)
            or sha256(data[:0x98]) != 'b78bc58667eb44c261fe37dcd051de581dd13edec25f9274f7b1f9e4a9ae5d40'
            or sha256(table) != 'b362d398e9b519b0e336eb53a2490a5af1ca78ddd426de3c3034153a38bf1e5e'
            or sha256(data[0x80886168-ram:0x808861E0-ram]) != '241984b49882796d3293dcc1e8029432b5991c7172649842309c02b255d6859a'):
        raise ValueError('Changed native palette selector or case/ornament conversion')
    # Native insertion copies the selected palette byte unchanged. The only
    # replacement operation indexes this 256-byte table with the previous byte.
    # Deletion shifts existing bytes and writes space; down-at-end adds newline.
    reachable = {32, 205}
    for pointer, count in zip(pointers, counts):
        if not ram <= pointer <= ram+len(data)-count: raise ValueError('Invalid native palette pointer')
        reachable.update(data[pointer-ram:pointer-ram+count])
    for _ in range(256):
        added = {table[code] for code in reachable}-reachable
        if not added: break
        reachable.update(added)
    else: raise ValueError('Notice editor conversion closure did not converge')
    if reachable & {0x7F, 0x80}: raise ValueError('Native manual text collides with reserved snapshot/glyph prefixes')
    return {'reachable_bytes': len(reachable), 'reserved_prefixes_excluded': [0x7F, 0x80],
            'conversion_sha256': sha256(table), 'scope': 'Original and English-first palettes plus repeated native conversion'}


def patch_prefix(native, symbols):
    original, reloc, _, _ = native_sources(native)
    data = bytearray(original)
    required = set(name for name, _ in CALLS.values()) | {'af_notice_read_control', 'af_notice_construct'}
    if any(type(symbols.get(name)) is not int or symbols[name] & 3
           or not RESIDENT <= symbols[name] < RESIDENT+GROWTH for name in required):
        raise ValueError('Missing or unowned notice reader entry point')
    expected_rows = {0x80895BC0-RAM: 2}
    for at, (name, before) in CALLS.items():
        if struct.unpack_from('>I', original, at-RAM)[0] != 0x0C000000 | ((before >> 2) & 0x3FFFFFF):
            raise ValueError('Changed native notice draw call')
        struct.pack_into('>I', data, at-RAM, 0x0C000000 | (((RAM+symbols[name]) >> 2) & 0x3FFFFFF))
        expected_rows[at-RAM] = 4
    if struct.unpack_from('>I', original, 0x80895BC0-RAM)[0] != NATIVE_IMPORTS['af_notice_original_read']:
        raise ValueError('Changed native read dispatch')
    struct.pack_into('>I', data, 0x80895BC0-RAM, RAM+symbols['af_notice_read_control'])
    actual = {}
    for row in struct.unpack_from('>69I', reloc, 20):
        section, at = row >> 30, row & 0xFFFFFF
        at += (0, 0, 6512, 6624)[section]
        if at in expected_rows: actual[at] = (row >> 24) & 63
    if actual != expected_rows: raise ValueError('Native reader hooks lack their expected relocations')
    return bytes(data)


def elf_inventory(text):
    result = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported notice ELF relocation')
        result.append([int(match[1], 16)-RAM, KINDS[match[2]], int(match[3], 16), match[4]])
    return result


def relocation_bytes(native_reloc, inventory, size, module):
    allowed = imports(module)
    rows = []
    for row in struct.unpack_from('>69I', native_reloc, 20):
        section, kind, at = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3): raise ValueError('Invalid original notice relocation')
        at += (0, 6512, 6624)[section-1]
        rows.append(0x40000000 | kind << 24 | at)
    seen = set()
    for at, kind, target, name in inventory:
        if at in seen or at & 3 or not RESIDENT <= at <= size-4 or kind not in KINDS.values():
            raise ValueError('Invalid appended notice relocation')
        seen.add(at)
        if RAM <= target < RAM+size:
            rows.append(0x40000000 | kind << 24 | at)
        elif name not in allowed or target != allowed[name] or kind != 4:
            raise ValueError('Unapproved external notice ELF target')
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate notice relocation')
    length = (24+4*len(rows)+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
            +bytes(length-24-4*len(rows))+struct.pack('>I', length))


def initial_table():
    records = [pack(Record(4, 0, (number,), ())) for number in INITIAL_IDS]
    if any(wire[:12] != bytes.fromhex('7f424e01af200c0004000000') or any(wire[16:]) for wire in records):
        raise ValueError('Initial assembly no longer matches canonical compact envelopes')
    return b''.join(wire[12:16] for wire in records)


def pool_sizes():
    # All endpoints below are immediate constants in the source-hashed native
    # allocation function. The patch grows only the editor term in the maximum
    # submenu sum, reserving room for notice growth wherever the board is loaded.
    align = lambda value: (value+63) & ~63
    pair_a = align(0x8088CA90-0x8088ADB0)+align(0x80897870-0x80896B20)
    pair_b = align(0x808A2E00-0x8089AD40)+align(0x808A45E0-0x808A2EA0)
    parent = align(0x8086F0E0-0x8085BAC0)
    inventory = align(0x808796B0-0x8086F310)
    tag = align(0x8087CA30-0x8087A330)
    hand = align(0x80881C20-0x8087D480)
    primary = (parent+hand+inventory+tag+align(0x8088ACC0-0x80888E90)
               +align(0x80888B20-0x80885140)+align(0x80896A70-0x80895E00)+max(pair_a, pair_b))
    alternative = parent+inventory+tag+align(0x808B2B30-0x808A6100)+0x4000
    player = 0x808E04D0-0x808B2D50
    if primary <= max(alternative, player): raise ValueError('Native allocation maximum changed')
    return {'native': primary, 'expanded': primary+GROWTH, 'alternative': alternative,
            'player': player, 'additional_bytes': GROWTH}


def main_changes(init):
    if len(init) != INIT_END-INIT_START or sha256(init) != INITIAL_HASH:
        raise ValueError('Unapproved in-place notice creator')
    pool_sizes()
    return {INIT_START: init, INIT_TABLE: initial_table(), POOL_PATCH: struct.pack('>I', 0x25CECB20)}


@dataclass(frozen=True)
class OverlayImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native, data, reloc, init, report, module, catalog):
    original, native_reloc, _, _ = native_sources(native)
    imports(module)
    audit_editor(native)
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != len(data)
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_bytes') != len(reloc)
            or report.get('relocation_sha256') != sha256(reloc) or report.get('sources') != source_hashes()
            or report.get('module_sha256') != MODULE_HASH or report.get('imports') != imports(module)
            or report.get('approval') != audit(native, catalog)):
        raise ValueError('Stale or changed notice reader build')
    symbols, end, bss = report.get('symbols', {}), report.get('code_end'), report.get('bss_start')
    if (symbols != EXPECTED_SYMBOLS or end != 11232 or bss != 11392
            or len(data) & 15 or not RESIDENT < len(data) <= RESIDENT+GROWTH
            or type(end) is not int or type(bss) is not int or end & 15 or bss & 15
            or not RESIDENT < end <= bss < len(data) or any(data[bss:])
            or data[:PREFIX] != patch_prefix(native, symbols) or any(data[PREFIX:RESIDENT])
            or sha256(data[RESIDENT:]) != SUFFIX_HASH or report.get('suffix_sha256') != SUFFIX_HASH
            or sha256(reloc) != RELOC_HASH or sha256(init) != INITIAL_HASH
            or report.get('init_sha256') != INITIAL_HASH):
        raise ValueError('Unapproved notice code, initialization, or relocation image')
    if reloc != relocation_bytes(native_reloc, report.get('elf_relocations', []), len(data), module):
        raise ValueError('Changed notice relocation inventory')
    spec = OverlayImage(RAM, len(data), struct.unpack_from('>5I', reloc))
    prior = OverlayImage(RAM, RESIDENT, struct.unpack_from('>5I', native_reloc))
    changed = set(CALLS) | {0x80895BC0}
    for base in (0x801A0000, 0x802F8010, (0x80400000-len(data)) & ~15):
        moved = relocate_verified_data(spec, data, reloc, base)
        old = relocate_verified_data(prior, original, native_reloc, base)
        for at in range(0, RESIDENT, 4):
            if at+RAM not in changed and moved[at:at+4] != old[at:at+4]:
                raise ValueError('Notice growth changes retained code, data, or original BSS')
    main_changes(init)
    return spec


def metadata(size, symbols):
    if size & 15 or not RESIDENT < size <= RESIDENT+GROWTH: raise ValueError('Notice allocation exceeded')
    return struct.pack('>8I', NEW_VROM, NEW_VROM+size, RAM, RAM+size,
                       RAM+symbols['af_notice_construct'], 0x80895B9C, 0x80895A30, 0)


def verify_installation(built, native, module, report):
    from snowman_actor import verify_resources
    catalog = verify_resources(built, native, module)[0]
    files = by_vrom(built)
    audit_editor(native, files[0x78CB80].extract(built))
    if (NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files
            or files[NEW_VROM].index != by_vrom(native)[VROM].index
            or files[NEW_RELOCATION].index != files[NEW_VROM].index+1
            or report.get('catalog') != 4 or report.get('complete_templates') != list(INITIAL_IDS)
            or report.get('pool') != pool_sizes()):
        raise ValueError('Missing installed notice reader, source IDs, or native DMA positions')
    data, reloc = files[NEW_VROM].extract(built), files[NEW_RELOCATION].extract(built)
    code = files[CODE_VROM].extract(built)
    init = code[INIT_START-CODE_RAM:INIT_END-CODE_RAM]
    spec = validate(native, data, reloc, init, report['overlay'], module, catalog)
    owner, owner_reloc = files[OWNER_VROM].extract(built), files[OWNER_RELOCATION].extract(built)
    _, _, old_owner, old_owner_reloc = native_sources(native)
    expected = bytearray(old_owner)
    expected[METADATA:METADATA+32] = metadata(len(data), report['overlay']['symbols'])
    if owner != expected or owner_reloc != old_owner_reloc: raise ValueError('Changed notice owner or loader')
    for at, value in main_changes(init).items():
        if code[at-CODE_RAM:at-CODE_RAM+len(value)] != value: raise ValueError('Missing notice creator or pool patch')
    original_code = by_vrom(native)[CODE_VROM].extract(native)
    for start, end in ((0x800A5B50, INIT_START), (INIT_END, 0x800A5DF4), (POOL_START, POOL_PATCH), (POOL_PATCH+4, POOL_END)):
        if code[start-CODE_RAM:end-CODE_RAM] != original_code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed saved-post layout, insertion, or allocation policy')
    return spec


def install(native, replacements, additions, relocations, module, directory):
    native_sources(native)
    for address in (VROM, RELOCATION, NEW_VROM, NEW_RELOCATION, OWNER_VROM, OWNER_RELOCATION):
        if any(address in mapping for mapping in (replacements, additions, relocations)):
            raise ValueError('Overlapping native notice overlay/owner replacement')
    data, reloc, init = ((directory/name).read_bytes() for name in ('overlay.bin', 'relocation.bin', 'init.bin'))
    overlay = json.loads((directory/'overlay.json').read_text())
    files = by_vrom(native)
    original = files[CODE_VROM].extract(native)
    code = GuardedCode(original, replacements.get(CODE_VROM, original), CODE_RAM, SOURCE_HASHES[CODE_VROM])
    for at, value in main_changes(init).items(): code.write(at, value)
    owner = bytearray(files[OWNER_VROM].extract(native))
    owner[METADATA:METADATA+32] = metadata(len(data), overlay['symbols'])
    report = {'overlay': overlay, 'catalog': 4, 'complete_templates': list(INITIAL_IDS), 'pool': pool_sizes(),
              'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOCATION:08X}',
              'new_saved_bytes': 0, 'new_resident_module_bytes': 0,
              'status': 'Initial notice creation/full-body reader installed; native and persistence acceptance remain'}
    changes = {VROM: data, RELOCATION: reloc, OWNER_VROM: bytes(owner), CODE_VROM: bytes(code.data)}
    moves = {VROM: NEW_VROM, RELOCATION: NEW_RELOCATION}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_installation(prospective, native, module, report)
    replacements.update(changes)
    relocations.update(moves)
    return report
