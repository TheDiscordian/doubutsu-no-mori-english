"""Verified entry-only replacement of the ordinary native birthday preparer."""

from functools import lru_cache
import struct

from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from code_sections import code_segments
from npc_mail_show import OVERLAYS
from runtime_layout import MODULE_RAM, LINKED_LIMIT
from textbanks import banks
from textcodec import command_info, tokenize

SPEC = OVERLAYS['ordinary']
START, END = 0x80921324, 0x80921464
BODY_SHA256 = '770b3dbb0270671fe82acf1804887c667dd60e4c1ebd6f07c95b95be35a05440'
REQUEST = bytes.fromhex('7F0C090004')


@lru_cache(maxsize=1)
def message_ids(rom):
    """The verified cartridge request, not candidate metadata, owns this dependency."""
    rom = verified_rom(rom)
    info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
    entries = next(bank for bank in banks(rom) if bank.name == 'message').entries()
    return frozenset(f'message:{index:04X}' for index, data in enumerate(entries)
                     if any(t.kind == 'cmd' and t.data == REQUEST for t in tokenize(data, info)))


def verify_source(data, reloc):
    if sha256(data[START-SPEC.ram:END-SPEC.ram]) != BODY_SHA256:
        raise ValueError('Native birthday preparer changed')
    if data[0x80921D58-SPEC.ram:0x80921D70-SPEC.ram] != bytes.fromhex('0113021203140413051406150716081609160A170B150C15'):
        raise ValueError('Native birthday constellation boundaries changed')
    if struct.unpack_from('>I',data,0x80921D78+3*4-SPEC.ram)[0] != START:
        raise ValueError('Native birthday dispatcher target changed')
    count = struct.unpack_from('>I',reloc,16)[0]
    if any(START-SPEC.ram <= value&0xFFFFFF < START+8-SPEC.ram
           for value in struct.unpack_from('>'+str(count)+'I',reloc,20)):
        raise ValueError('Birthday entry unexpectedly has a native relocation')


def changes(module):
    target = int(module['symbols'].get('af_birthday_fields','0'),16)
    used = module.get('linked_bytes',0)
    if type(used) is not int or not 0x300 < used <= LINKED_LIMIT or target&3 or not MODULE_RAM+0x300 <= target < MODULE_RAM+used:
        raise ValueError('Birthday preparer lies outside the bounded resident module')
    return [(START,0x27BDFFC8,0x08000000 | ((target&0x0FFFFFFF)>>2)),
            (START+4,0xAFBF0034,0)]


@lru_cache(maxsize=1)
def audit_references(rom):
    """Cache only the identical immutable verified input, never a modified image."""
    rom = verified_rom(rom)
    segments,definitions = code_segments()
    if SPEC.vrom not in segments or len(segments) < 100:
        raise ValueError('Incomplete native birthday executable inventory')
    interior, entries = [], []
    for vrom,file in by_vrom(rom).items():
        if file.pstart == 0xFFFFFFFF:
            continue
        data = file.extract(rom); segment = segments.get(vrom)
        for offset in range(0,len(data)-3,4):
            pc = segment.ram+offset if segment else None
            if vrom == SPEC.vrom and START <= pc < END:
                continue
            word = struct.unpack_from('>I',data,offset)[0]
            targets = [word] if word&3 == 0 else []
            if segment and segment.is_text(offset):
                op = word>>26
                if op in (2,3): targets.append(((pc+4)&0xF0000000) | ((word&0x3FFFFFF)<<2))
                if op in (1,4,5,6,7,20,21,22,23) or op == 17 and (word>>21)&31 == 8:
                    immediate = (word&0xFFFF)-(0x10000 if word&0x8000 else 0)
                    targets.append(pc+4+immediate*4)
            if any(START < t < END for t in targets): interior.append((vrom,offset))
            if START in targets: entries.append((vrom,offset))
    if interior:
        raise ValueError(f'External native birthday interior references: {interior}')
    expected = ((SPEC.vrom,0x80921D78+3*4-SPEC.ram),)
    if tuple(entries) != expected:
        raise ValueError(f'Unexpected native birthday entry references: {entries}')
    return {'source_sha256':sha256(rom),'body_sha256':BODY_SHA256,
            'entry_references':[[f'{v:08X}',f'{o:06X}'] for v,o in entries],
            'external_interior_references':[], 'definition_sha256':definitions,
            'scope':'Aligned literal pointers and direct native jumps/branches in pinned text; original table dispatch retained'}
