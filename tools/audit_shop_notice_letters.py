#!/usr/bin/env python3
"""Bind remaining spotlight-item and reopening letters to both native selectors."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks
import mail_creator_catalog as creator_catalog

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = (*range(0x12,0x18),*range(0x1B,0x1E))
RARE_TABLE = (18,18,19,19,21,20,23,22)
REOPENING_TABLE = (29,27,28,29)
GUARDS = (
    (0x800C0E98,0x800C1070,'7c8de407cc329252dfbf6e5299df3092a30c1f10af4864e5518e65efa7309838'),
    (0x800C1070,0x800C1230,'829183c3d0abcf674df06fcdcc9192632194dd3fb3688b081c3171a17c3190b5'),
    (0x800C1230,0x800C1428,'a60688e4f6cfb745812d2b5e56cef9f6e474fd60cb46d420afd02121cbaaddc9'),
)
FUNCTIONS = {
    'mSP_ShopItsumoChirashi':(364,'a1586372f4e7cdeddca90280fcdb5624c9db800ddb603b1428a3638ecb159b6d'),
    'mSP_SetShopRareFurnitureChirashi':(676,'a7464983002b747b1e2c2f7d5404793d024c2e250a4cdefe8f302f7d3bcacc8b'),
    'mSP_SetRenewalChiraswhi_AppoDay':(356,'d9264e3ffa0e30d9d140bf6512b578bc71e14fccef22a6cf6d4e1059e6831464'),
}


def audit(native,catalog,root=ROOT):
    native = verified_rom(native);code = by_vrom(native)[CODE_VROM].extract(native)
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest: raise ValueError('Changed native shop notice owner')
    for at,expected in ((0x8010DC3C,RARE_TABLE),(0x8010DC5C,REOPENING_TABLE)):
        if struct.unpack_from('>'+str(len(expected))+'I',code,at-CODE_RAM)!=expected:
            raise ValueError('Changed native shop notice selection table')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied shop notice executable')
    for name,(size,digest) in FUNCTIONS.items():
        value = symbol_data(rel,symbols,name)
        if (len(value),sha256(value))!=(size,digest): raise ValueError('Changed supplied shop notice owner')
    if (struct.unpack('>8I',symbol_data(rel,symbols,'rare_chirashi_bunmen$981'))!=RARE_TABLE
            or struct.unpack('>4I',symbol_data(rel,symbols,'chirashi_idx_appoday$1048'))!=(27,27,28,29)):
        raise ValueError('Changed supplied shop notice selectors')
    catalog_id = creator_catalog.identity(catalog);installed = parse(catalog)[1]
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA256: raise ValueError('Changed shop notice decoder')
    tables = decoder_tables(decoder);directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    sources = {b.name:b.entries() for b in banks(native) if b.name in ('super','mail','ps')};parts = []
    for name in sources:
        data,table = ((directory/(name+s)).read_bytes() for s in ('_data.bin','_data_table.bin'))
        if (sha256(data),sha256(table))!=BANK_HASHES[name]: raise ValueError('Changed shop notice reference bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            fields = {7} if name=='mail' and 0x14<=number<=0x17 else set()
            if (installed[name][number]!=value or template_fields(value,extended_glyphs=catalog_id==4)!=fields
                    or template_fields(sources[name][number])!=fields):
                raise ValueError('Incomplete shop notice wording or changed item-field contract')
            parts.append({'id':f'{name}:{number:04X}','source_sha256':sha256(sources[name][number]),
                          'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                          'bytes':len(value),'fields':sorted(fields)})
    return {'templates':list(TEMPLATES),'parts':parts,'catalog':catalog_id,'installed':False,
            'native_rare_table':list(RARE_TABLE),'native_reopening_table':list(REOPENING_TABLE),
            'reference_reopening_table':[27,27,28,29],
            'reference_functions':{k:list(v) for k,v in FUNCTIONS.items()},
            'status':'Source approval only; full item capture, complete creation, owner gates, and delivery remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/audits/shop-notice-letters.json')
    args = parser.parse_args();report = audit(args.rom.read_bytes(),args.catalog.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'templates':len(report['templates']),'parts':len(report['parts']),'installed':False}))


if __name__=='__main__': main()
