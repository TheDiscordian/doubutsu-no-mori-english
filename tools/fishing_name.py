"""Exact, save-preserving fishing winner-name display integration."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from actor_display_names import NAMES_SHA, NAMES_VROM
from catalogue_names import Image, elf_inventory as inventory
from npc_mail_names import prepare, unpack_aliases, lookup
from runtime_module import MODULE_VROM, verify_test_module
from shop_item_names import MODULE_SHA, jump

ROOT = Path(__file__).resolve().parents[1]
VROM, RELOC, RAM = 0x0094FF70, 0x00950C50, 0x80A8FCF0
PREFIX, START = 3296, 3312
SECTIONS = (2832, 288, 176, 16, 92)
NEW_VROM, NEW_RELOC = 0x03B40000, 0x03B50000
METADATA, CALL = 0x80102050, 0x80A9031C
METADATA_BYTES = bytes.fromhex('0094ff7000950c5080a8fcf080a909e00000000080a908000000000000000000')
SOURCE_SHA = '74a443389fb91af5df3de75bfe2aa43a0be56b09d0383dc25debefe7fd5c68b3'
RELOC_SHA = '12bbd61e96a0c178777f0fd381ec5d0a9a89f57608ff5c27abe4b4a74b9c517b'
ALIASES_SHA = 'a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6'
IMPORTS = {'af_fishing_native_set': 0x8009D6D0}
APPROVED = {
    'bytes': 10048,
    'symbols': {'af_fishing_aliases': 3680, 'af_fishing_name': 3572, 'af_fishing_resolve': 3312},
    'suffix_sha256': 'b30f520c06d8b32529b16378845ca8d0d4a0d903bd475b3367f9ddac872d80e4',
    'relocation_sha256': '91e9826db52f2e6d7b8b970ecd4be0ed56adb57ed7bf8e692e5c6b0c3435fffe',
    'elf_relocations': [[3600, 5, RAM+3680, 'af_fishing_aliases'],
                        [3604, 6, RAM+3680, 'af_fishing_aliases'],
                        [3612, 4, RAM+3312, 'af_fishing_resolve'],
                        [3656, 4, 0x8009D6D0, 'af_fishing_native_set']],
}


def source_hashes():
    return {p: sha256((ROOT/p).read_bytes()) for p in
            ('overlays/fishing/name.c', 'overlays/fishing/image.s', 'overlays/fishing/image.ld')}


def source(native):
    files = by_vrom(verified_rom(native))
    data, reloc = [files[v].extract(native) for v in (VROM, RELOC)]
    code = files[CODE_VROM].extract(native)
    if (len(data) != PREFIX or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or files[RELOC].index != files[VROM].index+1):
        raise ValueError('Changed native fishing actor or ownership')
    return data, reloc


def aliases(native, directory):
    data, report = prepare(native, (directory/'names.bin').read_bytes(),
                           json.loads((directory/'names.json').read_text()))
    unpack_aliases(data, ALIASES_SHA)
    if len(data) != 6368 or report['aliases'] != 394:
        raise ValueError('Changed fishing name alias resource')
    return data


def original_relocations(reloc):
    rows = []
    for (word,) in struct.iter_unpack('>I', reloc[20:20+SECTIONS[4]*4]):
        section, kind, at = word >> 30, (word >> 24) & 63, word & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid native fishing relocation')
        rows.append((at+(0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1], kind))
    return rows


def patch_prefix(native, symbols):
    original, reloc = source(native); data = bytearray(original)
    if (struct.unpack_from('>I', data, CALL-RAM)[0] != jump(IMPORTS['af_fishing_native_set'], link=True)
            or CALL-RAM in dict(original_relocations(reloc))):
        raise ValueError('Changed fishing name call or relocation')
    struct.pack_into('>I', data, CALL-RAM, jump(RAM+symbols['af_fishing_name'], link=True))
    return bytes(data)


def relocation_data(native, elf, size):
    rows = original_relocations(source(native)[1])+[(CALL-RAM, 4)]
    seen = set()
    for at, kind, target, name in elf:
        if at in seen or at & 3 or not START <= at <= size-4 or kind not in (2, 4, 5, 6):
            raise ValueError('Invalid appended fishing relocation')
        seen.add(at)
        if RAM <= target < RAM+size: rows.append((at, kind))
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound fishing external target')
    if len({at for at, _ in rows}) != len(rows): raise ValueError('Duplicate fishing relocation')
    values = [0x40000000 | kind << 24 | at for at, kind in rows]
    length = (24+len(values)*4+15) & ~15
    return (struct.pack('>5I', size, 0, 0, 0, len(values))+struct.pack('>'+str(len(values))+'I', *values)
            +bytes(length-24-len(values)*4)+struct.pack('>I', length))


def validate(native, data, reloc, report):
    if not APPROVED: raise ValueError('Fishing image needs independent approval')
    if (any(report.get(k) != v for k, v in APPROVED.items())
            or len(data) != APPROVED['bytes'] or report.get('sources') != source_hashes()
            or report.get('imports') != IMPORTS or report.get('overlay_sha256') != sha256(data)
            or data[:PREFIX] != patch_prefix(native, APPROVED['symbols']) or any(data[PREFIX:START])
            or sha256(data[START:]) != APPROVED['suffix_sha256']
            or sha256(reloc) != APPROVED['relocation_sha256']
            or reloc != relocation_data(native, report['elf_relocations'], len(data))):
        raise ValueError('Changed fishing image, imports, or relocation')
    at = APPROVED['symbols']['af_fishing_aliases']
    unpack_aliases(data[at:at+6368], ALIASES_SHA)
    return Image(RAM, len(data), struct.unpack_from('>5I', reloc))


def metadata():
    row = bytearray(METADATA_BYTES)
    struct.pack_into('>4I', row, 0, NEW_VROM, NEW_VROM+APPROVED['bytes'], RAM, RAM+APPROVED['bytes'])
    return bytes(row)


def dependencies(native, code, module_data, names):
    original = by_vrom(native)[CODE_VROM].extract(native)
    normalised = bytearray(module_data); normalised[56:0x88] = bytes(0x88-56)
    if (len(module_data) != 32768 or sha256(normalised) != MODULE_SHA or sha256(names) != NAMES_SHA
            or struct.unpack_from('>I', module_data, 60)[0] != NAMES_VROM
            or code[0x80094EE0-CODE_RAM:0x80094F04-CODE_RAM] != original[0x80094EE0-CODE_RAM:0x80094F04-CODE_RAM]
            or code[0x800ACC38-CODE_RAM:0x800ACEE8-CODE_RAM] != original[0x800ACC38-CODE_RAM:0x800ACEE8-CODE_RAM]):
        raise ValueError('Fishing names require approved names, runtime, and native identity writers')


def evidence(report):
    return {'overlay': report, 'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOC:08X}',
            'extra_actor_bytes': APPROVED['bytes']-START, 'alias_count': 394,
            'name_bytes': 8, 'player_name_bytes': 6, 'field_slot': 0, 'saved_layout_changes': False}


def install(native, replacements, additions, relocations, directory):
    original, original_reloc = source(native); files = by_vrom(native)
    code = bytearray(replacements.get(CODE_VROM, files[CODE_VROM].extract(native)))
    dependencies(native, code, additions.get(MODULE_VROM, b''), additions.get(NAMES_VROM, b''))
    if ((replacements.get(VROM, original), replacements.get(RELOC, original_reloc)) != (original, original_reloc)
            or VROM in relocations or RELOC in relocations
            or code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or any(v in files or v in replacements or v in additions or v in relocations.values()
                   for v in (NEW_VROM, NEW_RELOC))):
        raise ValueError('Overlapping fishing name installation')
    data, reloc = (directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes()
    report = json.loads((directory/'overlay.json').read_text()); validate(native, data, reloc, report)
    verify_native_keys(data, replacements.get(0xE04000, files[0xE04000].extract(native)))
    code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata()
    replacements.update({VROM: data, RELOC: reloc, CODE_VROM: bytes(code)})
    relocations.update({VROM: NEW_VROM, RELOC: NEW_RELOC})
    return evidence(report)


def verify_native_keys(data, bank):
    at = APPROVED['symbols']['af_fishing_aliases']
    rows = unpack_aliases(data[at:at+6368], ALIASES_SHA)
    for i in range(216):
        found = lookup(rows, bytes(bank[8+i*6:14+i*6]))
        if found is None or found[0] != i: raise ValueError('Unresolved installed fishing NPC identity')


def verify_installation(built, native, report):
    if not report.get('text_extension'): raise ValueError('Fishing names require complete dialogue fields')
    verify_test_module(built, report['runtime_module'])
    files, originals = by_vrom(built), by_vrom(native)
    if (VROM in files or RELOC in files or NEW_VROM not in files or NEW_RELOC not in files
            or files[NEW_VROM].index != originals[VROM].index or files[NEW_RELOC].index != originals[RELOC].index):
        raise ValueError('Missing complete fishing actor and relocation')
    entry = report['fishing_name']; data, reloc = [files[v].extract(built) for v in (NEW_VROM, NEW_RELOC)]
    validate(native, data, reloc, entry['overlay']); verify_native_keys(data, files[0xE04000].extract(built))
    code = files[CODE_VROM].extract(built)
    dependencies(native, code, files[MODULE_VROM].extract(built), files[NAMES_VROM].extract(built))
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata() or entry != evidence(entry['overlay']):
        raise ValueError('Incomplete fishing actor ownership')
    for old, new in ((VROM, NEW_VROM), (RELOC, NEW_RELOC)):
        if report.get('vrom_relocations', {}).get(f'{old:08X}') != f'{new:08X}':
            raise ValueError('Missing fishing DMA movement evidence')
    return entry
