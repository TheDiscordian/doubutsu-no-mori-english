#!/usr/bin/env python3
"""Recover complete reply-sender display names from exact native identity names.

This prepares local immutable aliases, not a gameplay hook or a save rewrite.
Unknown keys remain unresolved; no English prefix or current-villager guessing.
"""

import argparse
from bisect import bisect_left
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from display_names import resource as display_resource
from mail_record import Field
from textcodec import LATIN

NPC_COUNT,HEADER_BYTES,ROW_BYTES = 216,64,16
DISPLAY_SHA256 = '261078b6c8bec7f974255ddffba8c2a570b4a2a0526ea699a3cc62ffc2b4e974'


@dataclass(frozen=True)
class Alias:
    key: bytes
    npc_index: int
    name: bytes


def aliases(originals,names):
    if len(originals) != NPC_COUNT or len(names) != NPC_COUNT:
        raise ValueError('Incomplete NPC name identity tables')
    selected = {}
    for index,(original,name) in enumerate(zip(originals,names)):
        if (type(original) is not bytes or len(original) != 6 or any(c in (0x7F,0x80) for c in original)
                or type(name) is not bytes or len(name) != 8 or not name.rstrip(b' ')
                or any(c not in LATIN for c in name)):
            raise ValueError('Invalid saved-name key or complete English display name')
        keys = [original]
        short = name.rstrip(b' ')
        if len(short) <= 6:
            keys.append(short.ljust(6,b' '))
        for key in keys:
            alias = Alias(key,index,name)
            if key in selected and selected[key] != alias:
                raise ValueError('Ambiguous exact NPC saved-name identity')
            selected[key] = alias
    return tuple(selected[key] for key in sorted(selected))


def pack_aliases(rows):
    if not NPC_COUNT <= len(rows) <= NPC_COUNT*2:
        raise ValueError('Unexpected NPC saved-name alias count')
    payload = bytearray()
    previous = None
    for row in rows:
        if (not isinstance(row,Alias) or type(row.key) is not bytes or len(row.key) != 6
                or any(c in (0x7F,0x80) for c in row.key)
                or type(row.npc_index) is not int or not 0 <= row.npc_index < NPC_COUNT
                or type(row.name) is not bytes or len(row.name) != 8 or not row.name.rstrip(b' ')
                or any(c not in LATIN for c in row.name)
                or (previous is not None and row.key <= previous)):
            raise ValueError('Invalid or unordered NPC name alias')
        payload.extend(row.key+struct.pack('>H',row.npc_index)+row.name)
        previous = row.key
    if {row.npc_index for row in rows} != set(range(NPC_COUNT)):
        raise ValueError('NPC name aliases do not cover every identity')
    by_id = {}
    for row in rows:
        if by_id.setdefault(row.npc_index,row.name) != row.name:
            raise ValueError('Aliases disagree on the complete NPC display name')
    header = struct.pack('>8I',0x41464E41,1,len(rows),ROW_BYTES,HEADER_BYTES,NPC_COUNT,6,8)
    return header+bytes.fromhex(sha256(payload))+bytes(payload)


def unpack_aliases(data,expected_sha256):
    if (len(data) < HEADER_BYTES or len(data) > HEADER_BYTES+NPC_COUNT*2*ROW_BYTES
            or sha256(data) != expected_sha256 or data[32:64] != bytes.fromhex(sha256(data[64:]))):
        raise ValueError('Altered NPC name alias resource')
    magic,version,count,width,header,npc_count,key_width,name_width = struct.unpack_from('>8I',data)
    if ((magic,version,width,header,npc_count,key_width,name_width) != (0x41464E41,1,16,64,216,6,8)
            or len(data) != HEADER_BYTES+count*ROW_BYTES):
        raise ValueError('Invalid NPC name alias header')
    rows = tuple(Alias(bytes(data[at:at+6]),struct.unpack_from('>H',data,at+6)[0],bytes(data[at+8:at+16]))
                 for at in range(HEADER_BYTES,len(data),ROW_BYTES))
    if pack_aliases(rows) != data: raise ValueError('Noncanonical NPC name aliases')
    return rows


def lookup(rows,key):
    """Resolve an exact six-byte key in a validated tuple; return None if unknown."""
    if type(key) is not bytes or len(key) != 6:
        raise ValueError('NPC saved-name lookup requires exactly six bytes')
    index = bisect_left(rows,key,key=lambda row:row.key)
    if index == len(rows) or rows[index].key != key:
        return None
    row = rows[index]
    return row.npc_index,Field(row.name)


def prepare(rom,names,report):
    rom = verified_rom(rom)
    if (sha256(names) != DISPLAY_SHA256 or report.get('source_sha256') != sha256(rom)
            or report.get('data_sha256') != DISPLAY_SHA256
            or display_resource(rom,report['edits']) != names):
        raise ValueError('NPC alias preparation requires the verified complete display-name resource')
    raw = by_vrom(rom)[0xE04000].extract(rom)
    originals = tuple(raw[8+i*6:14+i*6] for i in range(NPC_COUNT))
    english = tuple(names[32+i*8:40+i*8] for i in range(NPC_COUNT))
    rows = aliases(originals,english)
    data = pack_aliases(rows)
    return data,{'source_sha256':sha256(rom),'native_names_sha256':sha256(raw),
                 'display_names_sha256':sha256(names),'data_sha256':sha256(data),'bytes':len(data),
                 'aliases':len(rows),'villagers':NPC_COUNT,
                 'keys':[{'key_sha256':sha256(row.key),'npc_index':row.npc_index,
                          'full_name_sha256':sha256(row.name)} for row in rows],
                 'unknown_key_policy':'unresolved; no prefix, case folding, or current-world substitution',
                 'status':'Local exact-name source mapping; no native capture or resource installation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--display-names',type=Path,default=Path('build/display-names'))
    parser.add_argument('--output',type=Path,default=Path('build/npc-mail-names'))
    args = parser.parse_args()
    data,report = prepare(args.rom.read_bytes(),(args.display_names/'names.bin').read_bytes(),
                         json.loads((args.display_names/'names.json').read_text()))
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'aliases.bin').write_bytes(data)
    (args.output/'aliases.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key != 'keys'},indent=2))


if __name__ == '__main__': main()
