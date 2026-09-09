#!/usr/bin/env python3
"""Approve complete villager secret letters and prepare immutable snapshots."""

import argparse
import json
from pathlib import Path
import struct

from aflib import sha256,verified_rom
from audit_mail_templates import template_fields
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_catalog import parse,templates
from mail_record import Record,pack
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from mail_runtime_test_scenario import output_bytes
from npc_mail_show import OVERLAYS,source
from textbanks import Bank,banks
import mail_creator_catalog as creator_catalog

ROOT = Path(__file__).resolve().parents[1]
START,END,COMPACT = 0x8091E960,0x8091E9FC,0x80921B54
TEMPLATES = tuple(range(0x22,0x31))
NATIVE_HASH = '1f431bce746b485434b90471780e07add04acbbf87e8791a62672c00722a976a'
REFERENCE_HASH = 'f1fa6dc41cdacb0e1fb0c197196ee0c63c30893e18110138bc783211900cb088'


def audit(native,catalog,root=ROOT):
    native = verified_rom(native);spec = OVERLAYS['ordinary'];data,reloc = source(native,'ordinary')
    if sha256(data[START-spec.ram:END-spec.ram])!=NATIVE_HASH:
        raise ValueError('Changed native secret-letter selection or metadata')
    rel = (root/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (root/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
    if sha256(rel)!='29306a927eee861b073c571408393f99cb384048684eee4bff3d219725429837':
        raise ValueError('Changed supplied secret-letter executable')
    reference = symbol_data(rel,symbols,'aQMgr_get_memory_mail_secret')
    if (len(reference),sha256(reference))!=(156,REFERENCE_HASH):
        raise ValueError('Changed supplied secret-letter creator')
    decoder = root/'local/ac-decomp/tools/msg_tool.py'
    if sha256(decoder.read_bytes())!=DECODER_SHA256: raise ValueError('Changed secret-letter decoder')
    tables = decoder_tables(decoder);catalog_id = creator_catalog.identity(catalog)
    if catalog_id!=4: raise ValueError('Complete secret letters require glyph catalogue four')
    installed = parse(catalog)[1];original = {b.name:b.entries() for b in banks(native) if b.name in ('super','mail','ps')}
    directory = root/'build/gamecube/files/forest_1st.arc.unpacked/data';parts = []
    for name in original:
        data,table = ((directory/(name+suffix)).read_bytes() for suffix in ('_data.bin','_data_table.bin'))
        if (sha256(data),sha256(table))!=BANK_HASHES[name]: raise ValueError('Changed secret-letter reference bank')
        reference = Bank(name,0,0,data,table).entries()
        for number in TEMPLATES:
            value = transcode(reference[number],tables,extended_glyphs=catalog_id==4)
            if (value!=installed[name][number] or template_fields(value,extended_glyphs=catalog_id==4)
                    or template_fields(original[name][number])):
                raise ValueError('Incomplete secret-letter wording or unexpected free field')
            parts.append({'id':f'{name}:{number:04X}','source_sha256':sha256(original[name][number]),
                          'reference_sha256':sha256(reference[number]),'encoded_sha256':sha256(value),'bytes':len(value),'fields':[]})
    return {'templates':list(TEMPLATES),'parts':parts,'catalog':catalog_id,'native_generator_sha256':NATIVE_HASH,
            'reference_generator_sha256':REFERENCE_HASH,'native_overlay_sha256':spec.file_sha256,
            'native_relocation_sha256':sha256(reloc),'compact_ram':f'{COMPACT:08X}',
            'installed':False,'status':'Source-approved fixed snapshots; original overlay integration and native execution remain'}


def snapshots(native,catalog):
    approval = audit(native,catalog)
    if approval['catalog']!=4: raise ValueError('Secret snapshots require complete glyph catalogue four')
    rows = bytearray();cases = []
    for number in TEMPLATES:
        for capital in (0,1):
            entry = Record(4,0,(number,),(),bool(capital));wire = pack(entry)
            text = output_bytes(entry,templates(catalog,entry))
            if wire[2]!=12 or any(wire[16:]) or text[14] not in (0,1):
                raise ValueError('Unexpected secret snapshot layout')
            rows.extend(struct.pack('>HBB',number,text[14],0)+wire[:16])
            cases.append({'template':number,'capital':capital,'wire':wire.hex(),'text':text.hex()})
    if len(rows)!=600: raise ValueError('Unexpected secret snapshot table size')
    return bytes(rows),{**approval,'table_sha256':sha256(rows),'row_bytes':20,'table_bytes':600,'cases':cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/secret-letter-snapshots')
    args = parser.parse_args();data,report = snapshots(args.rom.read_bytes(),args.catalog.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True);(args.output/'snapshots.bin').write_bytes(data)
    (args.output/'approval.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'templates':15,'parts':45,'snapshots':30,'bytes':len(data),'installed':False}))


if __name__=='__main__': main()
