#!/usr/bin/env python3
"""Approve Snowman letter inputs without claiming an installed delivery route."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from audit_mail_templates import template_fields
from extended_items import COUNTS,HEADER,WIDTH
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from textbanks import Bank,banks

ROOT = Path(__file__).resolve().parents[1]
VROM,RAM,RELOCATION = 0x862870,0x8096DC30,0x866A80
GIFTS = (*range(0x1EA4,0x1ECC,4),0x2619,0x2719)
GC_GIFTS = (*range(0x1F54,0x1F7C,4),0x2619,0x2719)
GUARDS = (
    (0x8096E1A4,0x8096E274,'873787f99da99b22767b583e7b736c363b8d29f6e52472ae5c6082ddad97be3a'),
    (0x8096E274,0x8096E2EC,'87a6ff3cdd104dd8b8c146a5c5a8159790400491b1416c3cc9b5ab44b651527e'),
    (0x80971C88,0x80971CA0,'6fca03a1137aa135935adeac1b88cd598628f39bbfb51acf04b892a93c236b74'),
)
REFERENCE = {
    'aSMAN_GetSnowmanPresentMail':(276,'f6f56ff710ea2ca9da07e098a200eced6ce7cb00ce0fd4f7c6fab2adc1d2c1af'),
    'aSMAN_SendPresentMail':(116,'9a3251c9faa1045e552b6f6efe460c8782bbfee2ec35a7bc48b7e428d422a5e3'),
    'snow_item_table$536':(24,'c8c0d2cc62581308921c6c225a915bf4f46fd417b722dd50af244ddd8063b66f'),
}


def audit(rom,catalog,items,root=ROOT):
    rom = verified_rom(rom);files = by_vrom(rom)
    actor,reloc = files[VROM].extract(rom),files[RELOCATION].extract(rom)
    if (len(actor)!=16912 or sha256(actor)!='9ddb45f07394e967bf42e121d11ae25fe39814b68c22dc41b238818c48d99d88'
            or len(reloc)!=1104 or sha256(reloc)!='84e8a1a9211ff0f9733b4c46f23389ae65db6a102c66fb601119b1ce1082d75c'
            or struct.unpack_from('>5I',reloc)!=(16400,208,304,0,269)):
        raise ValueError('Changed native Snowman actor or relocation')
    for start,end,digest in GUARDS:
        if sha256(actor[start-RAM:end-RAM])!=digest: raise ValueError('Changed Snowman creator, owner, or gifts')
    if struct.unpack_from('>12H',actor,0x80971C88-RAM)!=GIFTS: raise ValueError('Changed native Snowman gift order')
    if items[:32]!=HEADER or len(items)!=32+sum(COUNTS)*WIDTH: raise ValueError('Invalid Snowman item resource')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied Snowman executable')
    for name,expected in REFERENCE.items():
        data = symbol_data(rel,symbols,name)
        if (len(data),sha256(data))!=expected: raise ValueError('Changed reference Snowman function or gifts')
    if struct.unpack('>12H',symbol_data(rel,symbols,'snow_item_table$536'))!=GC_GIFTS:
        raise ValueError('Changed reference Snowman gift order')
    # Native resource IDs include the furniture orientation bits; GameCube's
    # executable indexes its furniture name table after dividing by four.
    ftr = symbol_data(rel,symbols,'ftrName_table');names = []
    for index,(gift,donor) in enumerate(zip(GIFTS,GC_GIFTS)):
        if gift>>12==1:
            offset = 32+(sum(COUNTS[:-1])+(gift&4095))*16
            at = ((donor//4)&1023)*16;reference = ftr[at:at+16]
        else:
            group = gift>>8;offset = 32+(sum(COUNTS[:group-0x20])+(gift&255))*16
            table = symbol_data(rel,symbols,'itemName_'+('carpet' if group==0x26 else 'wall'))
            reference = table[(donor&255)*16:((donor&255)+1)*16]
        if len(reference)!=16 or items[offset:offset+16]!=reference:
            raise ValueError('Snowman requires the complete matching English item name')
        names.append({'native_gift':gift,'reference_gift':donor,'name_sha256':sha256(reference),'template':0x202+index})
    import mail_creator_catalog as creator_catalog
    catalog_id = creator_catalog.identity(catalog);installed = parse(catalog)[1]
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA256: raise ValueError('Changed English mail decoder')
    tables = decoder_tables(decoder);parts = []
    native = {b.name:b.entries() for b in banks(rom) if b.name in ('super','mail','ps')}
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data'
    for name in ('super','mail','ps'):
        data = (directory/(name+'_data.bin')).read_bytes();table = (directory/(name+'_data_table.bin')).read_bytes()
        if (sha256(data),sha256(table))!=BANK_HASHES[name]: raise ValueError('Changed Snowman reference bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in range(0x202,0x20E):
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            fields = frozenset((0,)) if name=='mail' else frozenset()
            if (value!=installed[name][number] or template_fields(value,extended_glyphs=catalog_id==4)!=fields
                    or template_fields(native[name][number])!=fields):
                raise ValueError('Changed complete Snowman text or item-field contract')
            parts.append({'id':f'{name}:{number:04X}','source_sha256':sha256(native[name][number]),
                          'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),
                          'bytes':len(value),'fields':sorted(fields)})
    return {'native_actor_sha256':sha256(actor),'native_relocation_sha256':sha256(reloc),
            'catalog':catalog_id,'parts':parts,'gifts':names,'reference_functions':REFERENCE,
            'installed':False,'status':'Source and field approval only; creation, receipt, and retry remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    parser.add_argument('--items',type=Path,default=ROOT/'build/interior-items-resource/names.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/audits/snowman-letters.json')
    args = parser.parse_args();report = audit(args.rom.read_bytes(),args.catalog.read_bytes(),args.items.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'templates':len(report['gifts']),'parts':len(report['parts']),'installed':False}))


if __name__=='__main__': main()
