#!/usr/bin/env python3
"""Record selected metadata/storage boundaries and the Pelly failure-loss path."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from audit_display_names import audit as references
from code_sections import code_segments
from mail_storage import FUNCTIONS, evidence, pelly_evidence, pocket_send_evidence


def inline_candidates(rom):
    """A reproducible narrow search, not proof about arbitrary pointer aliases."""
    entries = by_vrom(rom)
    segments,definitions = code_segments()
    rows = []
    for vrom,segment in segments.items():
        # Makerom precedes the first DMA entry and contains the entry stub.
        data = rom[:0x1060] if vrom == 0 else entries[vrom].extract(rom)
        digest = sha256(data)
        for offset in range(0,len(data)-3,4):
            word = struct.unpack_from('>I',data,offset)[0]
            if (segment.is_text(offset) and word>>26 in (0x20,0x24,0x28)
                    and (word>>21)&31 != 29 and word&0xFFFF in (0x27,0x2F)):
                rows.append({'vrom':f'{vrom:08X}','address':f'{segment.ram+offset:08X}',
                             'instruction':f'{word:08X}','file_sha256':digest})
    return {'method':'Executable LB/LBU/SB, non-stack base, immediate 27 or 2F hexadecimal',
            'limitation':'Excludes adjusted/computed pointers, other offsets, stack fields, and other load sizes; hits are not necessarily mail',
            'definition_sha256':definitions,'candidates':rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('build/audits/mail-storage.json'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    result = {'rom_sha256':sha256(rom),'storage':evidence(rom),'pelly':pelly_evidence(rom),
              'pocket_send':pocket_send_evidence(rom),
              'references':references(rom,{name:row[0] for name,row in FUNCTIONS.items()},allow_empty=True)}
    result['inline_candidates'] = inline_candidates(rom)
    result['text_helper_references'] = references(rom,{'strlen':0x8009C1C0,'strlen2':0x8009C284,
                                                        'strcpy_back':0x8009C2D8},allow_empty=True)
    for value in result['text_helper_references'].values():
        value['status'] = 'Shared text helper; caller data flow requires review and is not necessarily mail'
    for value in result['references'].values():
        value['status'] = 'Selected native mail predicate/storage references; inline/computed-pointer consumers require independent review'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'references':{name:len(value['callers'])
                      for name,value in result['references'].items()},'pelly':result['pelly']['status']}))


if __name__ == '__main__': main()
