"""Complete house-sign names in existing stack storage; saved APIs stay six bytes."""
from functools import lru_cache
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from catalogue_names import Image
from code_sections import code_segments
from shop_item_names import jump
from text_names import BRIDGE, bridge_profile, verify_installed_bridge
from text_extension import VROM as TEXT_VROM, SETTER

VROM, RELOC, RAM = 0x00956630, 0x00956830, 0x80A963C0
SIZE, SECTIONS = 512, (464, 48, 0, 0, 8)
SOURCE_SHA = '179c1646dd78784770f12a3d926dc137f6e732eeb3efee851e5f0655b45e2328'
RELOC_SHA = '7d185e9b992f99a24ea80cbd0e2d5083904ca3594bcc05674e40c68c327edb8c'
START, END, CALL, LENGTH = 0x80A963E8, 0x80A96414, 0x80A9640C, 0x80A9642C
HELPER, HELPER_END, IDENTITY_CALL = 0x800ACF84, 0x800AD084, 0x800AD050
HELPER_SHA = '039a62c521c2abad15419351a4f17f566e5f0870473128cd6c060399f06abebc'
METADATA = 0x80102130
METADATA_BYTES = bytes.fromhex('009566300095683080a963c080a965c00000000080a965900000000000000000')


def preparation():
    # The callee stores its own argument homes. Reuse redundant caller stores
    # to initialize both name words before the unchanged position lookup.
    return struct.pack('>11I', 0x00807025, 0x3C082020, 0x35082020,
        0xAFA8001C, 0xAFA80020, 0x8DC50028, 0x8DC6002C, 0x8DC70030,
        0x27A4001C, jump(HELPER, link=True), 0)


def source(native):
    files = by_vrom(verified_rom(native))
    data, reloc, code = (files[v].extract(native) for v in (VROM, RELOC, CODE_VROM))
    if (len(data) != SIZE or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or files[RELOC].index != files[VROM].index+1
            or sha256(code[HELPER-CODE_RAM:HELPER_END-CODE_RAM]) != HELPER_SHA
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES):
        raise ValueError('Changed house-sign actor, lookup, or ownership')
    for (word,) in struct.iter_unpack('>I', reloc[20:20+4*SECTIONS[4]]):
        section = word >> 30
        if section not in (1, 2, 3): raise ValueError('Unknown house-sign relocation')
        at = (word & 0xFFFFFF)+(0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1]+RAM
        if START <= at < END or at == LENGTH:
            raise ValueError('Unexpected house-sign preparation relocation')
    return data, reloc, code


@lru_cache(maxsize=1)
def audit_references(native):
    """The widened position lookup is exclusive to this eight-byte display."""
    verified_rom(native); segments, definitions = code_segments(); callers = []
    if len(segments) < 100 or VROM not in segments:
        raise ValueError('Incomplete house-sign executable inventory')
    for vrom, file in by_vrom(native).items():
        if file.pstart == 0xFFFFFFFF: continue
        data, segment = file.extract(native), segments.get(vrom)
        for offset in range(0, len(data)-3, 4):
            word = struct.unpack_from('>I', data, offset)[0]
            if HELPER <= word < HELPER_END or START <= word < END:
                raise ValueError('Native literal reference to widened house-sign code')
            if not segment or not segment.is_text(offset): continue
            pc, op, targets = segment.ram+offset, word >> 26, []
            if op in (2, 3): targets.append(((pc+4) & 0xF0000000) | ((word & 0x3FFFFFF) << 2))
            if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or op == 17 and (word >> 21) & 31 == 8:
                displacement = (word & 65535)-(65536 if word & 32768 else 0)
                targets.append(pc+4+4*displacement)
            for target in targets:
                if START <= target < END:
                    raise ValueError('Native branch into replaced house-sign preparation')
                if HELPER <= target < HELPER_END and not (vrom == CODE_VROM and HELPER <= pc < HELPER_END):
                    if (vrom, pc, target, op) != (VROM, CALL, HELPER, 3):
                        raise ValueError('House-name lookup has an unsupported caller')
                    callers.append(f'{pc:08X}')
    if callers != [f'{CALL:08X}']: raise ValueError('Missing exclusive house-name caller')
    return {'callers': callers, 'external_interior_references': [], 'literal_pointers': [],
            'definition_sha256': definitions,
            'scope': 'Aligned literals and direct jumps/relative branches in pinned executable ranges'}


def patch_actor(native):
    data, _, _ = source(native); result = bytearray(data)
    result[START-RAM:END-RAM] = preparation()
    if struct.unpack_from('>I', result, LENGTH-RAM)[0] != 0x24070006:
        raise ValueError('Changed house-sign field length')
    struct.pack_into('>I', result, LENGTH-RAM, 0x24070008)
    return bytes(result)


def patch_code(code, *, reverse=False):
    before, after = jump(0x800ACD18, link=True), jump(BRIDGE, link=True)
    if reverse: before, after = after, before
    result = bytearray(code)
    if struct.unpack_from('>I', result, IDENTITY_CALL-CODE_RAM)[0] != before:
        raise ValueError('Changed house-sign identity call')
    struct.pack_into('>I', result, IDENTITY_CALL-CODE_RAM, after)
    return bytes(result)


def install(native, replacements, additions, report):
    original, reloc, native_code = source(native); reference = audit_references(native)
    code = replacements.get(CODE_VROM, native_code)
    profile = bridge_profile(additions.get(TEXT_VROM, b''))
    if (not report.get('text_extension', {}).get('identities')
            or profile is None
            or sha256(code[SETTER-CODE_RAM:SETTER-CODE_RAM+profile['loader_bytes']]) != profile['loader_sha256']
            or code[HELPER-CODE_RAM:HELPER_END-CODE_RAM] != native_code[HELPER-CODE_RAM:HELPER_END-CODE_RAM]
            or code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM] != native_code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM]
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or replacements.get(VROM, original) != original or replacements.get(RELOC, reloc) != reloc):
        raise ValueError('House signs require the complete identity bridge and original reader')
    data, changed_code = patch_actor(native), patch_code(code)
    replacements.update({VROM: data, CODE_VROM: changed_code})
    return {'vrom': f'{VROM:08X}', 'actor_sha256': sha256(data), 'relocation_sha256': sha256(reloc),
            'lookup_sha256': sha256(changed_code[HELPER-CODE_RAM:HELPER_END-CODE_RAM]),
            'bridge': f'{BRIDGE:08X}', 'field_slot': 0, 'name_bytes': 8,
            'blank_on_no_match': True, 'extra_allocation_bytes': 0,
            'saved_layout_changes': False, 'reference_audit': reference}


def verify_installation(built, native, report):
    verify_installed_bridge(built)
    files, originals = by_vrom(built), by_vrom(native)
    if any(v not in files or files[v].index != originals[v].index or
           report.get('vrom_relocations', {}).get(f'{v:08X}') not in (None, f'{v:08X}') for v in (VROM, RELOC)):
        raise ValueError('Changed house-sign DMA ownership')
    code = files[CODE_VROM].extract(built)
    changes = {CODE_VROM: patch_code(code, reverse=True)}
    evidence = install(native, changes, {TEXT_VROM: files[TEXT_VROM].extract(built)}, report)
    if (changes[CODE_VROM] != code or changes[VROM] != files[VROM].extract(built)
            or files[RELOC].extract(built) != originals[RELOC].extract(native)
            or report.get('house_name') != evidence):
        raise ValueError('Incomplete house-sign English reader')
    return evidence


def image_spec():
    return Image(RAM, SIZE, SECTIONS)
