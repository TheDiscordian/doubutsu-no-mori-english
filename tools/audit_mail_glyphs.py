#!/usr/bin/env python3
"""Inventory every unsupported glyph, not only the first error in each letter.

This is source-bound preparation only. It changes no catalogue, font, or ROM,
and does not credit text application or approve native/GameCube identities.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from aflib import sha256
from extended_glyphs import ENCODINGS
from gc_text import decoder_tables
from mail_catalog import BANKS,parse,verify_registered
from mail_format import field_index
from mail_reference import BANK_HASHES,DECODER_SHA256,load_reference
from textbanks import Bank
from textcodec import ENCODE


def missing_glyphs(data,tables):
    rows,pos = [],0
    while pos < len(data):
        code = data[pos]
        if code == 0x7F:
            if pos+1 == len(data): raise ValueError('Truncated reference mail command')
            opcode = data[pos+1]
            if opcode not in (0x74,0x75): field_index(opcode)
            if tables['CONT_SIZES'][opcode] != 2: raise ValueError('Changed mail command width')
            pos += 2;continue
        glyph = tables['CHAR_MAP'][code]
        if glyph not in ENCODE:
            extension = ENCODINGS.get(glyph)
            rows.append({'offset':pos,'source_code':f'{code:02X}','character':glyph,
                         'existing_separate_font_encoding':extension.hex() if extension else None})
        pos += 1
    return rows


def audit(directory,decomp,rel_path,catalog):
    registered = verify_registered(catalog)
    if registered['catalog'] != 2: raise ValueError('Audit requires frozen catalogue two')
    _,installed = parse(catalog)
    converted,source_report = load_reference(directory,decomp,rel_path)
    decoder = decomp/'tools/msg_tool.py';tables = decoder_tables(decoder)
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed reference decoder')
    rows = []
    for name in BANKS:
        data = (directory/(name+'_data.bin')).read_bytes();offsets = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(offsets)) != BANK_HASHES[name]: raise ValueError('Changed source mail bank')
        for i,part in enumerate(Bank(name,0,0,data,offsets).entries()):
            glyphs = missing_glyphs(part,tables)
            if bool(glyphs) != (converted[name][i] is None): raise ValueError('Glyph scan differs from reference conversion')
            if converted[name][i] != installed[name][i]: raise ValueError('Frozen catalogue differs from source conversion')
            if glyphs:
                rows.append({'id':f'{name}:{i:04X}','reference_sha256':sha256(part),'source_bytes':len(part),
                             'glyphs':glyphs,'only_existing_separate_font_glyphs':all(g['existing_separate_font_encoding'] for g in glyphs)})
    totals = Counter(g['source_code'] for row in rows for g in row['glyphs'])
    codes = {g['source_code']:g for row in rows for g in row['glyphs']}
    return {'schema':1,'catalog_sha256':registered['sha256'],'reference_banks':BANK_HASHES,
            'reference_functions':source_report['semantic_functions'],'decoder_sha256':DECODER_SHA256,
            'unavailable_parts':len(rows),'unsupported_occurrences':sum(totals.values()),
            'glyphs':[{'source_code':code,'character':codes[code]['character'],'occurrences':totals[code],
                       'existing_separate_font_encoding':codes[code]['existing_separate_font_encoding']} for code in sorted(totals)],
            'parts_using_only_existing_separate_font':[row['id'] for row in rows if row['only_existing_separate_font_glyphs']],
            'parts':rows,'installed':False,
            'scope':'Source glyph inventory only; native identities, mail tokens, pagination, new immutable catalogue, and generation remain required'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--catalog',type=Path,default=Path('build/mail-catalog/catalog.bin'))
    parser.add_argument('--output',type=Path,default=Path('build/mail-glyph-audit'))
    args = parser.parse_args();report = audit(args.gc_data,args.decomp,args.rel,args.catalog.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:report[k] for k in ('unavailable_parts','unsupported_occurrences','glyphs','parts_using_only_existing_separate_font','installed')},ensure_ascii=False,indent=2))


if __name__ == '__main__': main()
