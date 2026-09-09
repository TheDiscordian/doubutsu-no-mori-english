#!/usr/bin/env python3
"""Bind complete letter-quest replies to native ranks, personalities, and fields."""
import argparse
import json
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks
import mail_creator_catalog as creator_catalog

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = tuple(range(0x75,0xBD))
ITEM_FIELDS = (0x8D,0x8E,0x92,0x94,0xB3,0xB6)
NATIVE_ITEM_FIELDS = (*ITEM_FIELDS,0x98,0xB8)
GUARDS = (
    (0x800BB740,0x800BB86C,'61800a5be236b735b17ebddddd4999190b6cf7c535d8bd122e2262d2f61a1121'),
    (0x800BB86C,0x800BB990,'5be40d5bc076be6e54dc186f529a7bbf24173786aa9c3dbd2f54a02cb52ef7e9'),
    (0x800BB990,0x800BBAB0,'a6bce08209d80d6cfba21ca26d88ca228853bc324c703ec67d0fd346feffa1c8'),
    (0x800BBAB0,0x800BBB30,'7da416d289504d79101acf3e8e431f22670a71212667279a5578ac22a3a9678d'),
    (0x800BBB30,0x800BBBEC,'2b52dbfc483385643ff223d21499f8729eb81eae4cfdd6e562babc7137afbfef'),
)
FUNCTIONS = {
    'mQst_GetPresent':(304,'a27fcba8ce0b582e1b974d958111949608dbdc86896ae74f633438d93e2478aa'),
    'mQst_GetRemailData':(276,'ad71090bee4c40fae8d66aac7637d3e6ea726164c8ce1893b624693d52101a12'),
    'mQst_SendRemail':(216,'c9c3ad264931be619179da466fdd3fd12a8a23126c56080098950bcbaef15acd'),
    'mQst_GetMailRank':(144,'86c1152fa12cf4ddf26fabe4aa907c3f413889f4261bef13cb76ccc2c497dbb8'),
    'mQst_SetReceiveLetter':(176,'f928f592bab8f612a2f9c209d20a82cc2055915d580352d8303cfd3343508055'),
}
CALLER_VROM,CALLER_RAM,CALLER_START,CALLER_END = 0x8108C0,0x80918450,0x8091A9A8,0x8091AA28
CALLER_HASH = '08776a296c7f62300ae44ab432ffeb118c7be24dd875a7f70e68cac968b4b083'


def audit(native,catalog,root=ROOT):
    native = verified_rom(native);files = by_vrom(native);code = files[CODE_VROM].extract(native)
    for start,end,digest in GUARDS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError('Changed native quest reply selection, metadata, or owner')
    caller = files[CALLER_VROM].extract(native)[CALLER_START-CALLER_RAM:CALLER_END-CALLER_RAM]
    if sha256(caller)!=CALLER_HASH: raise ValueError('Changed native quest reply conversation result branch')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied quest reply executable')
    for name,expected in FUNCTIONS.items():
        value = symbol_data(rel,symbols,name)
        if (len(value),sha256(value))!=expected: raise ValueError('Changed supplied quest reply selection or metadata')
    catalog_id = creator_catalog.identity(catalog);installed = parse(catalog)[1]
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA256: raise ValueError('Changed quest reply decoder')
    tables = decoder_tables(decoder);directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    originals = {b.name:b.entries() for b in banks(native) if b.name in ('super','mail','ps')};parts = []
    for name in originals:
        data,table = ((directory/(name+s)).read_bytes() for s in ('_data.bin','_data_table.bin'))
        if (sha256(data),sha256(table))!=BANK_HASHES[name]: raise ValueError('Changed quest reply reference bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            fields = {6} if name=='ps' else {0} if name=='mail' and number in ITEM_FIELDS else set()
            native_fields = {6} if name=='ps' else {0} if name=='mail' and number in NATIVE_ITEM_FIELDS else set()
            if (installed[name][number]!=value or template_fields(value,extended_glyphs=catalog_id==4)!=fields
                    or template_fields(originals[name][number])!=native_fields):
                raise ValueError('Incomplete quest reply wording or changed name/item fields')
            parts.append({'id':f'{name}:{number:04X}','source_sha256':sha256(originals[name][number]),
                          'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                          'bytes':len(value),'fields':sorted(fields),'native_fields':sorted(native_fields)})
    return {'templates':list(TEMPLATES),'parts':parts,'catalog':catalog_id,'installed':False,
            'rank_count':12,'personality_count':6,'item_fields':list(ITEM_FIELDS),
            'native_item_fields':list(NATIVE_ITEM_FIELDS),'paper':22,'caller_sha256':CALLER_HASH,
            'reference_functions':{k:list(v) for k,v in FUNCTIONS.items()},
            'status':'Source-approved complete quest replies; installation and native acceptance remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/audits/quest-reply-letters.json')
    args = parser.parse_args();report = audit(args.rom.read_bytes(),args.catalog.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'templates':len(report['templates']),'parts':len(report['parts']),'installed':False}))


if __name__=='__main__': main()
