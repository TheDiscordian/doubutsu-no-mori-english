#!/usr/bin/env python3
"""Verify native NPC reply creation boundaries and immutable-source requirements.

This records inspected contracts, not installed hooks or approved translations.
Selection helpers consume already selected integer offsets and never call RNG.
"""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import CLASSIC,COMPOSITE,template_fields
from gc_names import symbol_data
from mail_catalog import parse,verify_registered

FUNCTIONS = {
    'composite_wrapper': (0x800A8B84,0x800A8C48,'4327cbe0e7544bf7a6808f44c38890948421c9a4cc1d6e6df2e10590baba3f05'),
    'capture_sources': (0x800A8C48,0x800A8DB4,'d238f2f3d926b0b31e1123db86849401619d6eddf837c7d94ce6ad7671dcb399'),
    'good_reply': (0x800A8DB4,0x800A8F30,'97919d8a755e399b85a058203f2b48bbac5efbfdd2ba6f3dff17f24b4784bdc3'),
    'bad_reply': (0x800A8F30,0x800A9028,'18d888a012891e18dbcd5c3ade9fbf1092802d1734ae3b127855eae6be95cd15'),
    'metadata': (0x800A9028,0x800A9110,'6aa1c763eb149a048b697013f7ade30d20c6e63a45d7120aa0b9fed1f225c87e'),
    'delivery': (0x800A9110,0x800A918C,'5243140a312966f89e82d73d04b2be43fc9dbd67dcd91647c97cbf3ac2a64260'),
    'reply_loop': (0x800A91DC,0x800A9364,'cfcf63a801ca27f46a25ed1c1af93b35033afa4a99e5146fe76d17cd59501ce8'),
}
GROUPS = ((32,64,0,96,128,160),(224,256,192,288,320,352))
BAD_BASES = (197,216)
WORD_BASES = (0x314,0x334,0x2F4,0x219,0x1E5,0x354,0x374,0x394,0x3D4,0x3F4,0x3B4)
REFERENCE_BASES = WORD_BASES[:3]+(0x6A1,0x679)+WORD_BASES[5:]
REFERENCE_COUNTS = (32,32,32,40,40,32,32,32,32,32,32)
TABLES = {
    'word_bases': (0x8010B824,WORD_BASES),
    'local_groups': (0x8010B850,GROUPS[0]),
    'visitor_groups': (0x8010B868,GROUPS[1]),
    'group_pointers': (0x8010B880,(0x8010B850,0x8010B868)),
    'bad_bases': (0x8010B888,BAD_BASES),
    'dispatch': (0x8010B890,(0x800A8F30,0x800A8DB4)),
}
REFERENCE_FUNCTIONS = {
    'mNpc_SetRemailFreeString':'508a294a6d0a064e7f0155aac2c3bf4c42f1145f165c57357824a4f394b0f6f2',
    'mNpc_GetRemailGoodData':'fb5732b2888b1c65ad8054918936c63de5cccd5fceebb37fdcd7f1f296924086',
    'mNpc_GetRemailWrongData':'d6dba6d6259b14e88dd4672e88cd52beb59ac807fb2a6e3f386904e9652cb870',
    'mNpc_GetRemailData':'0dfa2e7af67e913f566931eba9ab017aced8704bc7abcd9740cbbb5a6e37e3e2',
    'mNpc_SendRemailPostOffice':'ab9d217cef22243da746518172beaef47077ed822eeeecc1de951649a30fd1eb',
}
REFERENCE_TABLES = {
    'base_str_no$1281': ('I',REFERENCE_BASES),
    'rand_max_table$1282': ('f',REFERENCE_COUNTS),
    'this_start_no$1300': ('I',GROUPS[0]),
    'ohter_start_no$1301': ('I',GROUPS[1]),
    'mail_no$1320': ('I',BAD_BASES),
}


def native_evidence(code):
    functions,tables = {},{}
    for name,(start,end,expected) in FUNCTIONS.items():
        data = code[start-CODE_RAM:end-CODE_RAM]
        if sha256(data) != expected: raise ValueError('Changed native reply function: '+name)
        functions[name] = {'start':f'{start:08X}','end':f'{end:08X}','sha256':expected}
    for name,(address,expected) in TABLES.items():
        data = code[address-CODE_RAM:address-CODE_RAM+len(expected)*4]
        if data != struct.pack('>'+str(len(expected))+'I',*expected):
            raise ValueError('Changed native reply table: '+name)
        tables[name] = {'address':f'{address:08X}','values':list(expected),'sha256':sha256(data)}
    return {'code_sha256':sha256(code),'functions':functions,'tables':tables,
            'native_capture_bytes':10,'received_status':0,'letter_type':0,
            'staging_mail_ram':'80142F80','post_office_capacity':5,
            'assembler_failure_propagated':False,
            'reply_pending_cleared_only_after_delivery_success':True}


def reference_evidence(rel,symbols):
    functions,tables = {},{}
    for name,expected in REFERENCE_FUNCTIONS.items():
        if sha256(symbol_data(rel,symbols,name)) != expected:
            raise ValueError('Changed English reply function: '+name)
        functions[name] = expected
    for name,(format_char,expected) in REFERENCE_TABLES.items():
        data = symbol_data(rel,symbols,name)
        if data != struct.pack('>'+str(len(expected))+format_char,*expected):
            raise ValueError('Changed English reply table: '+name)
        tables[name] = {'values':list(expected),'sha256':sha256(data)}
    return {'functions':functions,'tables':tables,'reference_capture_bytes':16,
            'word_family_id_mapping_approved':False}


def indices(foreign,looks):
    if type(foreign) is not int or not 0 <= foreign < 2 or type(looks) is not int or not 0 <= looks < 6:
        raise ValueError('Invalid reply origin or personality')


def composite_selection(foreign,looks,gift_gate,offsets):
    """Retain five native-selected offsets. Gate zero selects a gift, not one."""
    indices(foreign,looks)
    if (type(gift_gate) is not int or gift_gate not in (0,1)
            or not isinstance(offsets,(tuple,list)) or len(offsets) != 5):
        raise ValueError('Invalid composite reply selection')
    if any(type(value) is not int or not 0 <= value < (16 if i == 2 else 32)
           for i,value in enumerate(offsets)):
        raise ValueError('Composite reply offset exceeds native RNG range')
    start = GROUPS[foreign][looks]
    return tuple(start+value+(gift_gate*16 if i == 2 else 0) for i,value in enumerate(offsets))


def classic_selection(foreign,looks,offset):
    indices(foreign,looks)
    if type(offset) is not int or not 0 <= offset < 3:
        raise ValueError('Classic reply offset exceeds native RNG range')
    return BAD_BASES[foreign]+looks*3+offset


def field_coverage(banks):
    """Check all selectable parts, not every wording combination or semantics."""
    if set(banks) != set(CLASSIC+COMPOSITE) or any(len(banks[name]) != (982 if name in CLASSIC else 384)
                                                for name in CLASSIC+COMPOSITE):
        raise ValueError('Unexpected reply reference bank dimensions')
    groups,classic = [],[]
    def inspect(parts,foreign):
        provided = set(range(16 if foreign else 14))
        required,missing,unavailable = set(),[],[]
        for name,index in parts:
            data = banks[name][index]
            if data is None:
                unavailable.append({'bank':name,'id':index})
                continue
            used = template_fields(data)
            required.update(used)
            if used-provided: missing.append({'bank':name,'id':index,'fields':sorted(used-provided)})
        return {'provided_fields':sorted(provided),'required_fields':sorted(required),
                'missing_fields':missing,'unavailable_parts':unavailable}
    for foreign in range(2):
        for looks in range(6):
            for gate in range(2):
                low = composite_selection(foreign,looks,gate,(0,0,0,0,0))
                parts = [(name,i) for part,(name,start) in enumerate(zip(COMPOSITE,low))
                         for i in range(start,start+(16 if part == 2 else 32))]
                groups.append({'foreign':foreign,'looks':looks,'gift_gate':gate,**inspect(parts,foreign)})
            for offset in range(3):
                index = classic_selection(foreign,looks,offset)
                classic.append({'foreign':foreign,'looks':looks,'id':index,
                                **inspect(((name,index) for name in CLASSIC),foreign)})
    unavailable = sorted({(part['bank'],part['id']) for row in groups+classic for part in row['unavailable_parts']})
    return {'composite_groups':groups,'classic_selections':classic,
            'summary':{'composite_groups':len(groups),'classic_selections':len(classic),
                       'missing_field_parts':sum(len(row['missing_fields']) for row in groups+classic),
                       'unavailable_parts':[{'bank':name,'id':index} for name,index in unavailable]},
            'status':'Source-slot availability only; full values, articles, template meaning, and delivery remain unapproved'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--catalog',type=Path,default=Path('build/mail-catalog/catalog.bin'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--symbols',type=Path,default=Path('local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'))
    parser.add_argument('--output',type=Path,default=Path('build/audits/npc-mail-generation.json'))
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    data = args.catalog.read_bytes();verify_registered(data)
    report = {'source_sha256':sha256(rom),'native':native_evidence(by_vrom(rom)[CODE_VROM].extract(rom)),
              'reference':reference_evidence(args.rel.read_bytes(),args.symbols.read_text()),
              'catalog_sha256':sha256(data),'coverage':field_coverage(parse(data)[1]),
              'production_generation_enabled':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['coverage']['summary'],indent=2))


if __name__ == '__main__': main()
