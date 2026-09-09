#!/usr/bin/env python3
"""Prepare complete NPC reply-word mappings from verified local source banks.

The resource is not installed in a ROM. Original native-selected IDs retain
their corresponding full English words; no new RNG draw or truncation occurs.
"""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import CODE_VROM,by_vrom,sha256,verified_rom
from gc_names import symbol_data
from gc_text import decoder_tables
from mail_record import Field
from mail_reference import BANK_HASHES,DECODER_SHA256,transcode
from npc_mail_generation import WORD_BASES,REFERENCE_BASES,native_evidence,reference_evidence
from textbanks import Bank,banks
from textcodec import LATIN

NATIVE_HASHES = ('b03ec28615257532d4d989cda116064ab928693c20fada0d071ce84cda91883c',
                 '404e038133a7c74622a7cc54c293653c026d090f0f2a74cb9a5b91da5ebcdeed')
LEGACY_HASHES = ('66f7e6e4e13a05814e913e42528d637777464591a110bb0edcdace0849329616',
                 '26af17c905c680b117ffe2ffef2c7011bcd7902ef6ecadc15338449e749f0248')
COUNT,ROW_BYTES,HEADER_BYTES = 352,32,64
RESOURCE_BYTES = HEADER_BYTES+COUNT*ROW_BYTES
HEADER = struct.pack('>8I',0x41464E57,1,COUNT,ROW_BYTES,HEADER_BYTES,11,16,0)
SETTER_SHA256 = '1d6b2bef84d1cd4d296852a60df2951382d796cfa9a99e84233dd4fb41b2d62b'
LOADER_SHA256 = '073c6d7c33f95f476ae33b691b6510a84c23eb6839effac3407effd558d11977'


def field_source_evidence(rel,symbols):
    expected = {'mHandbill_Set_free_str':SETTER_SHA256,'mString_Load_StringFromRom':LOADER_SHA256}
    for name,digest in expected.items():
        if sha256(symbol_data(rel,symbols,name)) != digest:
            raise ValueError('Changed English reply-field source: '+name)
    return expected


@dataclass(frozen=True)
class Word:
    native_id: int
    reference_id: int
    slot: int
    text: bytes
    article: int = 0

    def field(self):
        return Field(self.text,self.article)


def identity(index):
    if type(index) is not int or not 0 <= index < COUNT:
        raise ValueError('Invalid NPC reply-word row index')
    family,offset = divmod(index,32)
    return WORD_BASES[family]+offset,REFERENCE_BASES[family]+offset,family+3


def pack_words(rows):
    if len(rows) != COUNT: raise ValueError('Wrong NPC reply-word count')
    payload = bytearray()
    for i,row in enumerate(rows):
        if (not isinstance(row,Word) or (row.native_id,row.reference_id,row.slot) != identity(i)
                or type(row.article) is not int or row.article != 0
                or type(row.text) is not bytes or not 1 <= len(row.text) <= 16
                or any(byte not in LATIN for byte in row.text)):
            raise ValueError('Invalid, reordered, or incomplete NPC reply word')
        payload.extend(struct.pack('>HHBBBB',row.native_id,row.reference_id,row.slot,len(row.text),row.article,0))
        payload.extend(row.text.ljust(16,b'\0')+bytes(8))
    return HEADER+bytes.fromhex(sha256(payload))+bytes(payload)


def unpack_words(data,expected_sha256=None):
    if (len(data) != RESOURCE_BYTES or data[:32] != HEADER
            or data[32:64] != bytes.fromhex(sha256(data[64:]))
            or (expected_sha256 is not None and sha256(data) != expected_sha256)):
        raise ValueError('Invalid or altered NPC reply-word resource')
    rows = []
    for i in range(COUNT):
        offset = HEADER_BYTES+i*ROW_BYTES
        native,reference,slot,length,article,flags = struct.unpack_from('>HHBBBB',data,offset)
        if not 1 <= length <= 16 or flags or any(data[offset+8+length:offset+32]):
            raise ValueError('Invalid NPC reply-word row or padding')
        rows.append(Word(native,reference,slot,bytes(data[offset+8:offset+8+length]),article))
    if pack_words(rows) != data: raise ValueError('Noncanonical NPC reply-word resource')
    return tuple(rows)


def lookup(rows,slot,native_id):
    """Return the exact captured field from an already validated row tuple."""
    if type(slot) is not int or not 3 <= slot <= 13 or type(native_id) is not int:
        raise ValueError('Invalid NPC reply-word source slot or ID')
    offset = native_id-WORD_BASES[slot-3]
    if not 0 <= offset < 32 or len(rows) != COUNT:
        raise ValueError('NPC reply word is outside its native selected family')
    row = rows[(slot-3)*32+offset]
    if (row.native_id,row.reference_id,row.slot) != identity((slot-3)*32+offset):
        raise ValueError('NPC reply-word source identity differs')
    return row.field()


def prepare(native,legacy,reference,tables, *, native_species=False):
    for label,bank,hashes in (('native',native,NATIVE_HASHES),('legacy',legacy,LEGACY_HASHES),
                              ('English',reference,BANK_HASHES['string'])):
        if bank.name != 'string' or bank.table is None or (sha256(bank.data),sha256(bank.table)) != hashes:
            raise ValueError('Changed '+label+' NPC reply-word source bank')
    originals,old,english = native.entries(),legacy.entries(),reference.entries()
    rows,manifest = [],[]
    for i in range(COUNT):
        native_id,reference_id,slot = identity(i)
        text = transcode(english[reference_id],tables)
        # Exact complete donor agreement, not a prefix, shortened comparison,
        # shared numeric ID assumption, or whitespace-normalized match.
        if text != old[native_id]:
            raise ValueError(f'NPC reply-word identity is not confirmed at native {native_id:04X}')
        if native_species:
            from native_species import correct_word
            text = correct_word(native_id, originals[native_id], text)
        rows.append(Word(native_id,reference_id,slot,text))
        manifest.append({'slot':slot,'native_id':native_id,'reference_id':reference_id,
                         'native_sha256':sha256(originals[native_id]),
                         'legacy_sha256':sha256(old[native_id]),
                         'reference_sha256':sha256(english[reference_id]),
                         'captured_sha256':sha256(text),'bytes':len(text),
                         'article':0,'match_basis':'verified_caller_family_and_exact_complete_legacy_value'})
        if text != old[native_id]:
            from native_species import SOURCE
            manifest[-1].update(match_basis='reviewed_native_species_correction', translation_source=SOURCE)
    resource = pack_words(rows)
    return resource,{'resource_sha256':sha256(resource),'bytes':len(resource),'rows':manifest,
                     'word_count':len(rows),'words_exceeding_native_ten_bytes':sum(len(row.text)>10 for row in rows),
                     'maximum_word_bytes':max(len(row.text) for row in rows),
                     'status':'Verified local candidate word sources; no ROM resource or native capture hook installed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--legacy',type=Path,default=Path('build/inspect/legacy.z64'))
    parser.add_argument('--gc-data',type=Path,default=Path('build/gamecube/files/forest_1st.arc.unpacked/data'))
    parser.add_argument('--rel',type=Path,default=Path('build/gamecube/files/foresta.rel.szs.decoded'))
    parser.add_argument('--decomp',type=Path,default=Path('local/ac-decomp'))
    parser.add_argument('--output',type=Path,default=Path('build/npc-mail-words'))
    parser.add_argument('--native-species', action='store_true', help='Retain the N64 herabuna instead of the replaced GC species')
    args = parser.parse_args()
    rom = verified_rom(args.rom.read_bytes())
    native = native_evidence(by_vrom(rom)[CODE_VROM].extract(rom))
    rel = args.rel.read_bytes()
    symbols = (args.decomp/'config/GAFE01_00/foresta/symbols.txt').read_text()
    reference = reference_evidence(rel,symbols)
    field_sources = field_source_evidence(rel,symbols)
    decoder = args.decomp/'tools/msg_tool.py'
    if sha256(decoder.read_bytes()) != DECODER_SHA256: raise ValueError('Changed English decoder source')
    sources = [next(bank for bank in banks(data,legacy=old) if bank.name == 'string')
               for data,old in ((rom,False),(args.legacy.read_bytes(),True))]
    sources.append(Bank('string',0,0,(args.gc_data/'string_data.bin').read_bytes(),
                        (args.gc_data/'string_data_table.bin').read_bytes()))
    resource,report = prepare(*sources,decoder_tables(decoder),native_species=args.native_species)
    report.update(native_code=native,reference_code=reference,decoder_sha256=DECODER_SHA256,
                  reference_setter_sha256=SETTER_SHA256,reference_field_sources=field_sources)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'words.bin').write_bytes(resource)
    (args.output/'words.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:value for key,value in report.items() if key not in ('rows','native_code','reference_code')},indent=2))


if __name__ == '__main__': main()
