"""Save-preserving complete name preparation in the opening guide actor."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from actor_display_names import IMPORTS, NAMES_SHA, NAMES_VROM
from catalogue_names import Image
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import MODULE_SHA, jump

VROM, RELOC, RAM = 0x008AB7E0, 0x008ADBA0, 0x809C7FF0
PREFIX, SIZE = 9152, 9264
SECTIONS = (7920, 1184, 48, 0, 225)
NEW_VROM, NEW_RELOC = 0x03B20000, 0x03B30000
METADATA = 0x80101970
METADATA_BYTES = bytes.fromhex('008ab7e0008adba0809c7ff0809ca3b000000000809c9ee00000000000000000')
CALL, LENGTH = 0x809C8318, 0x809C8338
SOURCE_SHA = 'eadc78a87d188e9824801915bcc1840c73cf912638796604fcec2ecf31f924dd'
RELOC_SHA = 'b29a4a66f9e2dc8c7de381a799743ecaa94e8a2f72906268c23651e67a9a602a'


def body():
    # Only the verified eight-byte display temporary calls this adapter. Saved
    # identity APIs keep their native six-byte contract and fallback behaviour.
    return struct.pack('>28I', 0x27BDFFE0, 0xAFBF001C, 0xAFB00018, 0xAFB10014,
        0x00A08825, jump(0x800ACD18, link=True), 0x00808025, 0x24080020,
        0xA2080006, 0xA2080007, 0x12200009, 0,
        0x96260000, 0x24C82000, 0x3108FFFF, 0x2D0800D8, 0x11000003, 0x02002025,
        jump(IMPORTS['af_load_display_name'], link=True), 0x24050008,
        0x8FBF001C, 0x8FB10014, 0x8FB00018, 0x03E00008, 0x27BD0020, 0, 0, 0)


def source(native):
    files = by_vrom(verified_rom(native))
    data, reloc = [files[v].extract(native) for v in (VROM, RELOC)]
    code = files[CODE_VROM].extract(native)
    if (len(data) != PREFIX or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or files[RELOC].index != files[VROM].index+1
            or struct.unpack_from('>I', data, CALL-RAM)[0] != jump(0x800ACD18, link=True)
            or struct.unpack_from('>I', data, LENGTH-RAM)[0] != 0x24070006):
        raise ValueError('Changed native opening-guide actor or ownership')
    return data, reloc


def patched(native):
    original, reloc = source(native)
    data = bytearray(original+body())
    struct.pack_into('>I', data, CALL-RAM, jump(RAM+PREFIX, link=True))
    struct.pack_into('>I', data, LENGTH-RAM, 0x24070008)
    rows = []
    for (word,) in struct.iter_unpack('>I', reloc[20:20+SECTIONS[4]*4]):
        section, kind, at = word >> 30, (word >> 24) & 63, word & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Unknown opening-guide relocation')
        at += (0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1]
        if at in (CALL-RAM, LENGTH-RAM): raise ValueError('Unexpected name-call relocation')
        rows.append(0x40000000 | kind << 24 | at)
    rows.append(0x44000000 | (CALL-RAM))
    count = len(rows); length = (24+4*count+15) & ~15
    relocation = (struct.pack('>5I', SIZE, 0, 0, 0, count)+struct.pack('>'+str(count)+'I', *rows)
                  +bytes(length-24-4*count)+struct.pack('>I', length))
    if len(data) != SIZE: raise ValueError('Opening-guide helper exceeds allocation')
    return bytes(data), relocation


def metadata():
    row = bytearray(METADATA_BYTES)
    struct.pack_into('>4I', row, 0, NEW_VROM, NEW_VROM+SIZE, RAM, RAM+SIZE)
    return bytes(row)


def install(native, replacements, additions, relocations, module):
    original, original_reloc = source(native); files = by_vrom(native)
    code = bytearray(replacements.get(CODE_VROM, files[CODE_VROM].extract(native)))
    module_data = additions.get(MODULE_VROM, b''); normalised = bytearray(module_data)
    normalised[56:0x88] = bytes(0x88-56)
    native_code = files[CODE_VROM].extract(native)
    if (len(module_data) != 32768 or sha256(normalised) != MODULE_SHA
            or module.get('module_sha256') != MODULE_SHA
            or int(module['symbols'].get('af_load_display_name', '0'), 16) != IMPORTS['af_load_display_name']
            or struct.unpack_from('>I', module_data, 60)[0] != NAMES_VROM
            or sha256(additions.get(NAMES_VROM, b'')) != NAMES_SHA
            or code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM] != native_code[0x800ACD18-CODE_RAM:0x800ACD74-CODE_RAM]):
        raise ValueError('Opening-guide names require the approved resource and native identity fallback')
    if ((replacements.get(VROM, original), replacements.get(RELOC, original_reloc)) != (original, original_reloc)
            or VROM in relocations or RELOC in relocations
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or any(v in files or v in replacements or v in additions or v in relocations.values()
                   for v in (NEW_VROM, NEW_RELOC))):
        raise ValueError('Overlapping opening-guide installation')
    data, reloc = patched(native)
    code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata()
    replacements.update({VROM: data, RELOC: reloc, CODE_VROM: bytes(code)})
    relocations.update({VROM: NEW_VROM, RELOC: NEW_RELOC})
    return {'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOC:08X}',
            'actor_sha256': sha256(data), 'relocation_sha256': sha256(reloc),
            'helper_sha256': sha256(body()), 'actor_bytes': SIZE, 'extra_actor_bytes': SIZE-PREFIX,
            'name_bytes': 8, 'field_slot': 5, 'colour': 1, 'saved_layout_changes': False}


def verify_installation(built, native, report):
    if not report.get('text_extension'): raise ValueError('Opening-guide names require complete dialogue fields')
    module = report['runtime_module']; verify_test_module(built, module)
    files, originals = by_vrom(built), by_vrom(native)
    if (VROM in files or RELOC in files or NEW_VROM not in files or NEW_RELOC not in files
            or files[NEW_VROM].index != originals[VROM].index or files[NEW_RELOC].index != originals[RELOC].index):
        raise ValueError('Missing complete opening-guide actor and relocation')
    code = files[CODE_VROM].extract(built)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata():
        raise ValueError('Incomplete opening-guide allocation')
    normalised = bytearray(code); normalised[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = METADATA_BYTES
    changes = {CODE_VROM: bytes(normalised)}
    evidence = install(native, changes, {v: files[v].extract(built) for v in (MODULE_VROM, NAMES_VROM)}, {}, module)
    if (changes[CODE_VROM] != code or changes[VROM] != files[NEW_VROM].extract(built)
            or changes[RELOC] != files[NEW_RELOC].extract(built) or report.get('guide_name') != evidence):
        raise ValueError('Incomplete opening-guide name application')
    for old, new in ((VROM, NEW_VROM), (RELOC, NEW_RELOC)):
        if report.get('vrom_relocations', {}).get(f'{old:08X}') != f'{new:08X}':
            raise ValueError('Missing opening-guide DMA movement evidence')
    return evidence


def relocated_spec():
    return Image(RAM, SIZE, (SIZE, 0, 0, 0, SECTIONS[4]+1))
