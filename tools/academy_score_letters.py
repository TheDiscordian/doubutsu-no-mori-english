#!/usr/bin/env python3
"""Verify complete HRA score references and full native-to-English series names.

Generated data is reference-only, ignored, and never credits installed text.
"""

import argparse
import json
from pathlib import Path
import struct

from academy_letters import ROOT,verify_code
from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse,verify_registered
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks

VROM,RAM,RELOCATION = 0x81D9D0,0x809259E0,0x821740
TEMPLATES = tuple(range(0x34,0x49))
COMPLETE = tuple(n for n in TEMPLATES if n != 0x3D)
GUARDS = (
    (RAM,0x80925A5C,'8f9891be73838ffbb3025910f79b01a78a9dcdf9332714f099ae8cba20eed653'),
    (0x80925BB8,0x80925D1C,'c627eef36f20b1f8e431352b6a475057dcc3ea613f0054361b5edc61a1b52eac'),
    (0x80925D1C,0x80925D54,'b6779f9725c565928fc47fdac1dff9e43736823f71f074c88f0956a0109d6393'),
    (0x80925D54,0x80925E48,'6492787d71b2030ade9b013467022f3c3fa0345757e87ba0bfd7c14866e5241b'),
    (0x80925E48,0x809260A4,'5ed014bba5d2d577b9213bfaf92ee201ed1c7db43d23cd25bd305036a0904a32'),
    (0x809281B8,0x809283B0,'fae7d5c60fdc55ffe3caaf7b13e522f2bf54d6818f80809510c95c832319ac98'),
)
REFERENCE = {
    'mMkRm_GetSeriesName':(64,'e1d90548b542081d0790a3170b10a66e94e3f981319eb16ba5da1dfa84606a15'),
    'mMkRm_DecideLetterNo':(440,'0b60a0b8a45eb48a7cea4711c87b8da5e4b90d42f3a9a23b18c10653cfd0f175'),
    'mMkRm_SendMarkLetter':(584,'eb740977694f3215648e06b8e25859c803c5def2bfcc1fbd774b9c034b22ff29'),
    'mMkRm_MarkRoomOvl':(300,'f42f15a1ae5308230ada28a0795924be72e9a66f481ae68a08461a5e00ee7cb4'),
    'mMkRm_letter_no_table':(256,'6c24141a1678f32f19dd7b669f25b2d1b322502117f2d684b241aa1ae59964c8'),
    'mMkRm_series_name':(960,'9d5b0d3d4faa60cc780462ef1ed8320bd14b3f01e22f09303ce513e4e41c6e42'),
}


def fields(name,number):
    if number not in TEMPLATES or name not in ('super','mail','ps'):
        raise ValueError('Unknown academy score part')
    if name != 'mail': return set()
    return {0,3,4,5}|({1} if number==0x37 else {2} if number in (0x3A,0x3B) else set())


def verify_overlay(data,relocation):
    if (len(data),sha256(data)) != (15728,'9e42076944c8684c0220f442cb03c60d4ae485c15658a7fa761091f34fcb196b'):
        raise ValueError('Changed native academy score overlay')
    if (len(relocation),sha256(relocation)) != (1024,'1696efd5639209dc45a2531679a04422aeb44c839644613c97c8397d15a6dc7b'):
        raise ValueError('Changed native academy score relocation')
    if struct.unpack_from('>5I',relocation) != (10704,5024,0,1248,248):
        raise ValueError('Changed academy score sections')
    for start,end,digest in GUARDS:
        if sha256(data[start-RAM:end-RAM]) != digest: raise ValueError('Changed academy score function')
    table = data[0x80929630-RAM:0x80929730-RAM]
    if sha256(table) != '7a8502445448d6bb722fe9267181044242b21f09ce00c138d47d227bbaf44867':
        raise ValueError('Changed native score selection table')
    return struct.unpack('>64i',table)


def references(native,catalog,root=ROOT):
    native = verified_rom(native);files = by_vrom(native);verify_code(files[CODE_VROM].extract(native))
    data,relocation = (files[v].extract(native) for v in (VROM,RELOCATION))
    table = verify_overlay(data,relocation)
    if verify_registered(catalog)['catalog'] != 2: raise ValueError('Score references require catalogue two')
    installed = parse(catalog)[1]
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel) != '29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied score executable')
    for name,expected in REFERENCE.items():
        value = symbol_data(rel,symbols,name)
        if (len(value),sha256(value)) != expected: raise ValueError('Changed supplied score function/table')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed English decoder')
    tables = decoder_tables(decoder)
    source = data[0x80928458-RAM:0x80928458-RAM+550]
    if sha256(source) != '031e34c0ab75464a46e69154f04a4214658297cc30211c9014a951197d51d3e7':
        raise ValueError('Changed native furniture-series names')
    target = symbol_data(rel,symbols,'mMkRm_series_name');series = []
    for i in range(55):
        original,reference = source[i*10:i*10+10],target[i*16:i*16+16]
        value = transcode(reference,tables)
        if len(value) != 16 or not value.rstrip(b' ') or any(b<32 or b>=127 for b in value):
            raise ValueError('Invalid complete series-name reference')
        series.append({'id':i,'native':original.hex(),'english':value.hex(),
                       'source_sha256':sha256(original),'reference_sha256':sha256(reference)})
    original_banks = {b.name:b.entries() for b in banks(native) if b.name in ('super','mail','ps')}
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data';rows = []
    for name in ('super','mail','ps'):
        payload = (directory/(name+'_data.bin')).read_bytes();offsets = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(payload),sha256(offsets)) != BANK_HASHES[name]: raise ValueError('Changed supplied score text bank')
        reference = Bank(name,0,0,payload,offsets).entries()
        for number in TEMPLATES:
            original = original_banks[name][number]
            if template_fields(original) != fields(name,number): raise ValueError('Changed native score field set')
            row = {'id':f'{name}:{number:04X}','source_sha256':sha256(original),'reference_sha256':sha256(reference[number]),
                   'fields':sorted(fields(name,number))}
            try: value = transcode(reference[number],tables)
            except ValueError as error:
                if name!='mail' or number!=0x3D or 'GC D0' not in str(error): raise
                if installed[name][number] is not None: raise ValueError('Unavailable semicolon must remain missing')
                row['unavailable'] = str(error)
            else:
                if value != installed[name][number] or template_fields(value) != fields(name,number):
                    raise ValueError('Changed complete score text or fields')
                row.update(encoded_sha256=sha256(value),bytes=len(value))
            rows.append(row)
    return {'classic_templates':list(TEMPLATES),'complete_templates':list(COMPLETE),'unavailable_templates':[0x3D],
            'parts':rows,'series':series,'native_selection_table':table,'installed':False,
            'native_guards':GUARDS,'reference_functions':REFERENCE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-catalog/catalog.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/academy-score-references')
    args = parser.parse_args();report = references(args.rom.read_bytes(),args.catalog.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'references.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'templates':len(TEMPLATES),'complete_references':len(COMPLETE),'parts':len(report['parts']),
                      'full_series_names':len(report['series']),'unavailable':report['unavailable_templates'],'installed':False}))


if __name__ == '__main__': main()
