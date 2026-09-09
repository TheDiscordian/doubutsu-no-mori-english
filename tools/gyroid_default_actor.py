"""Append a read-only default selector to the owned Haniwa actor."""

from dataclasses import dataclass
import json
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256, verified_rom
from gyroid_default import (ROOT, DEFAULT, ORIGINAL, SLOT, INITIALIZERS, SOURCE_SHA256,
                            INTRO_SHA256, VARIANT_SHA256, native_sources as text_sources,
                            reference_payloads)
from npc_mail_show import relocate_verified_data
from runtime_module import module_command_info, verify_test_module
from runtime_layout import MODULE_RAM, MODULE_VROM, RESERVATION
from textbanks import Bank, banks

VROM, RELOCATION, RAM = 0x0085F7D0, 0x00861260, 0x8096AB90
PREFIX_BYTES, SIZE = 0x1A90, 0x1B40
SECTIONS = (6272, 496, 32, 0, 105)
NEW_VROM, NEW_RELOCATION = 0x03930000, 0x03938000
METADATA = 0x80100DD0
METADATA_BYTES = bytes.fromhex('0085f7d0008612608096ab908096c620000000008096c4100000000000000000')
HOOK = 0x8096B380
SYMBOLS = {'af_gyroid_default_select': 0x1A90, 'af_gyroid_default_demo': 0x1ADC,
           'af_gyroid_native_default': 0x1B00}
KINDS = {'26': 4, 'HI16': 5, 'LO16': 6}


def source_hashes():
    paths = ['overlays/gyroid_default/'+name for name in ('default.c', 'default.s', 'actor.s', 'actor.ld')]
    return {p: sha256((ROOT/p).read_bytes()) for p in paths}


def native_sources(native):
    native = verified_rom(native); files = by_vrom(native)
    data, reloc = files[VROM].extract(native), files[RELOCATION].extract(native)
    if (sha256(data) != 'bdd7e9093fe20ea5daf78953c3bb29f046c59e182d89ccc43871866c04d1c14d'
            or sha256(reloc) != '2c29895cb0e08f6dc4fb3464f53aae06a4b44b6a5c70b55611128ed9149ed03d'
            or struct.unpack_from('>5I', reloc) != SECTIONS or len(data) != PREFIX_BYTES
            or files[RELOCATION].index != files[VROM].index+1
            or files[CODE_VROM].extract(native)[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES
            or struct.unpack_from('>2I', data, HOOK-RAM) != (0x0C01ED70, 0x8C84C458)):
        raise ValueError('Changed original gyroid actor, ownership, call, or adjacent relocation')
    return data, reloc


def expected_helper():
    target = RAM+SYMBOLS['af_gyroid_native_default']
    selector = [0x24030928, 0x1483000F, 0x00801025, 0x10A0000D, 0x00001825,
                0x3C070000 | ((target+32768) >> 16), 0x24E70000 | (target & 65535),
                0x24060040, 0x00A34021, 0x00E32021, 0x91080000, 0x90840000,
                0x15040004, 0x24630001, 0x1466FFFA, 0x00A34021, 0x24022AE7,
                0x03E00008, 0]
    adapter = [0x8FA50020, 0x27BDFFE8, 0xAFBF0014,
               0x0C000000 | (((RAM+SYMBOLS['af_gyroid_default_select']) >> 2) & 0x3FFFFFF),
               0x24A50018, 0x8FBF0014, 0x00402025, 0x0801ED70, 0x27BD0018]
    return struct.pack('>28I', *(selector+adapter))


def patch_prefix(native):
    data, _ = native_sources(native); result = bytearray(data)
    struct.pack_into('>I', result, HOOK-RAM,
                     0x0C000000 | (((RAM+SYMBOLS['af_gyroid_default_demo']) >> 2) & 0x3FFFFFF))
    return bytes(result)


def elf_inventory(text):
    rows = []
    for line in text.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported gyroid ELF relocation')
        rows.append([int(match[1], 16)-RAM, KINDS[match[2]], int(match[3], 16), match[4]])
    return rows


def expected_inventory():
    return [[PREFIX_BYTES+0x14, 5, RAM+0x1B00, 'af_gyroid_native_default'],
            [PREFIX_BYTES+0x18, 6, RAM+0x1B00, 'af_gyroid_native_default'],
            [0x1AE8, 4, RAM+0x1A90, 'af_gyroid_default_select']]


def relocation_bytes(original):
    rows = []
    for row in struct.unpack_from('>105I', original, 20):
        section, kind, offset = row >> 30, (row >> 24) & 63, row & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6):
            raise ValueError('Unsupported original gyroid relocation')
        offset += (0, SECTIONS[0], SECTIONS[0]+SECTIONS[1])[section-1]
        if offset == HOOK-RAM: raise ValueError('Native external call must not have an overlay relocation')
        rows.append(0x40000000 | (kind << 24) | offset)
    # Preserve original order and paired/reused high semantics. The external
    # tail call at adapter+1C remains fixed in main code and has no new row.
    rows.append(0x44000000 | (HOOK-RAM))
    rows.extend(0x40000000 | (kind << 24) | at for at, kind, _, _ in expected_inventory())
    if len({r & 0xFFFFFF for r in rows}) != len(rows): raise ValueError('Duplicate gyroid relocation')
    length = (24+len(rows)*4+15) & ~15
    return (struct.pack('>5I', SIZE, 0, 0, 0, len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
            +bytes(length-24-len(rows)*4)+struct.pack('>I', length))


@dataclass(frozen=True)
class ActorImage:
    ram: int
    resident_bytes: int
    sections: tuple


def validate(native, data, reloc, report):
    original, original_reloc = native_sources(native)
    saved = text_sources(native)['string'][DEFAULT]
    if (report.get('version') != 1 or report.get('ram') != RAM or report.get('bytes') != SIZE
            or report.get('overlay_sha256') != sha256(data) or report.get('relocation_bytes') != len(reloc)
            or report.get('relocation_sha256') != sha256(reloc) or report.get('sources') != source_hashes()
            or report.get('symbols') != SYMBOLS or report.get('elf_relocations') != expected_inventory()
            or data != patch_prefix(native)+expected_helper()+saved
            or reloc != relocation_bytes(original_reloc)):
        raise ValueError('Changed gyroid code, saved-default comparison, source, or relocation')
    spec = ActorImage(RAM, SIZE, struct.unpack_from('>5I', reloc))
    old_spec = ActorImage(RAM, PREFIX_BYTES, SECTIONS)
    for base in (MODULE_RAM+RESERVATION, 0x802F8010, (0x80400000-SIZE) & ~15):
        moved = relocate_verified_data(spec, data, reloc, base)
        old = relocate_verified_data(old_spec, original, original_reloc, base)
        if moved[:HOOK-RAM] != old[:HOOK-RAM] or moved[HOOK-RAM+4:PREFIX_BYTES] != old[HOOK-RAM+4:]:
            raise ValueError('Gyroid growth changes unrelated native relocations')
        for at, offset in ((HOOK-RAM, SYMBOLS['af_gyroid_default_demo']), (0x1AE8, PREFIX_BYTES)):
            if struct.unpack_from('>I', moved, at)[0] != 0x0C000000 | (((base+offset) >> 2) & 0x3FFFFFF):
                raise ValueError('Gyroid internal call did not relocate')
        high, low = struct.unpack_from('>2I', moved, PREFIX_BYTES+0x14)
        actual = ((high & 65535) << 16)+(low & 65535)-(65536 if low & 32768 else 0)
        if actual != base+0x1B00 or moved[0x1AF8:0x1AFC] != bytes.fromhex('0801ED70'):
            raise ValueError('Gyroid default address or native tail target changed during relocation')
    return spec


def metadata():
    value = bytearray(METADATA_BYTES)
    struct.pack_into('>4I', value, 0, NEW_VROM, NEW_VROM+SIZE, RAM, RAM+SIZE)
    return bytes(value)


def verify_installation(built, native, module, report):
    verify_test_module(built, module)
    files, originals = by_vrom(built), by_vrom(native)
    if (NEW_VROM not in files or NEW_RELOCATION not in files or VROM in files or RELOCATION in files
            or files[NEW_VROM].index != originals[VROM].index
            or files[NEW_RELOCATION].index != files[NEW_VROM].index+1
            or report.get('vrom') != f'{NEW_VROM:08X}' or report.get('relocation_vrom') != f'{NEW_RELOCATION:08X}'):
        raise ValueError('Missing gyroid actor or adjacent relocation installation')
    spec = validate(native, files[NEW_VROM].extract(built), files[NEW_RELOCATION].extract(built), report['overlay'])
    code = files[CODE_VROM].extract(built)
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != metadata():
        raise ValueError('Gyroid actor allocation metadata is not installed')
    for start, end, digest in INITIALIZERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Gyroid saved initialisation changed')
    # Keep the existing complete custom formatter and fixed demo-message setter.
    target = int(module['symbols']['af_set_gyroid_message'], 16)
    if code[0x8009DA94-CODE_RAM:0x8009DA9C-CODE_RAM] != struct.pack('>2I', 0x08000000 | ((target >> 2) & 0x3FFFFFF), 0):
        raise ValueError('Complete custom gyroid formatter is not installed')
    native_code = originals[CODE_VROM].extract(native)
    if code[0x8007B5C0-CODE_RAM:0x8007B5F4-CODE_RAM] != native_code[0x8007B5C0-CODE_RAM:0x8007B5F4-CODE_RAM]:
        raise ValueError('Changed native demo-message setter')
    message = Bank('message', 0x02000000, 0x00CF9000, files[0x02000000].extract(built),
                   files[0x00CF9000].extract(built)).entries()
    full, intro, variant = reference_payloads(native, module_command_info(native))
    if message[ORIGINAL] != intro or message[SLOT] != variant:
        raise ValueError('Missing complete gyroid default or changed custom-message introduction')
    strings = next(b for b in banks(native) if b.name == 'string')
    vrom = 0x02600000 if 0x02600000 in files else strings.data_vrom
    saved = Bank('string', vrom, strings.table_vrom, files[vrom].extract(built),
                 files[strings.table_vrom].extract(built)).entries()[DEFAULT]
    if sha256(saved) != SOURCE_SHA256: raise ValueError('Gyroid saved-default representation changed')
    return spec, full


def install(native, replacements, additions, relocations, module, directory):
    if not module or MODULE_VROM not in additions: raise ValueError('Gyroid default requires its resident formatter')
    original, original_reloc = native_sources(native); files = by_vrom(native)
    if (replacements.get(VROM, original), replacements.get(RELOCATION, original_reloc)) != (original, original_reloc):
        raise ValueError('Overlapping gyroid actor edits')
    if (any(v in files or any(v in m for m in (replacements, additions, relocations))
            or v in relocations.values() for v in (NEW_VROM, NEW_RELOCATION))
            or any(v in relocations for v in (VROM, RELOCATION))):
        raise ValueError('Overlapping gyroid DMA range')
    data = (directory/'overlay.bin').read_bytes(); reloc = (directory/'relocation.bin').read_bytes()
    actor = json.loads((directory/'overlay.json').read_text())
    validate(native, data, reloc, actor)
    code = bytearray(replacements.get(CODE_VROM, files[CODE_VROM].extract(native)))
    if code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] != METADATA_BYTES:
        raise ValueError('Overlapping gyroid actor ownership metadata')
    code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata()
    report = {'overlay': actor, 'vrom': f'{NEW_VROM:08X}', 'relocation_vrom': f'{NEW_RELOCATION:08X}',
              'default_source_id': 'string:055C', 'variant_id': 'message:2AE7',
              'default_sha256': SOURCE_SHA256, 'variant_sha256': VARIANT_SHA256,
              'additional_actor_bytes': SIZE-PREFIX_BYTES, 'new_resident_bytes': 0, 'new_saved_bytes': 0,
              'status': 'Complete other-owner default installed; editor, native, and save acceptance remain'}
    changes = {VROM: data, RELOCATION: reloc, CODE_VROM: bytes(code)}
    moves = {VROM: NEW_VROM, RELOCATION: NEW_RELOCATION}
    prospective = replace_dma(native, {**replacements, **changes}, {**relocations, **moves}, additions)
    verify_installation(prospective, native, module, report)
    replacements.update(changes); relocations.update(moves)
    return report
