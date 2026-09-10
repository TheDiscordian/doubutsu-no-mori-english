#!/usr/bin/env python3
"""Source-bound complete accented item candidates; installation stays gated."""
import argparse
import json
from pathlib import Path
from aflib import sha256,verified_rom
from extended_items import COUNTS,HEADER,WIDTH,resource as previous_resource
from extended_glyphs import REL_SHA256,SYMBOLS_SHA256
from gc_names import symbol_data
from item_aliases import ordinary_item
from textbanks import banks

ROOT=Path(__file__).resolve().parents[1]
ROWS={
    'item_24:00A8':('café shirt','itemName_cloth',0xA8,
        'ff22d2d56c969228765eededd07601702a80ea864f3db4c5221719ca9063dd7b',
        'a1032ff93cf67d4c04fb99e1d9f953831632dd0e5da564a6c2a1b2a72e8a4601'),
    'item_25:0005':('Pokémon Pikachu','itemName_etc',5,
        '1140ce043fafd5b03379b3a40d80138fc8709539ca4b13cfe0edd993f9a79e84',
        '931286ecdeac671f25a122762a08f3b6e1bf4b69b1a480ca61bfadbd7a86e5ef'),
    'item_2A:0031':('Café K.K.','itemName_minidisk',0x31,
        'e6c4492972d6078e171f7c9d0bd45bf540d0d85a6e19e6a22ea2890dc8399c9a',
        '26031acef3a2f8f881ef732b153935aced02f8d6a0f7babe69e3c5e3d27a999b'),
    'item_2A:0033':('Señor K.K.','itemName_minidisk',0x33,
        '6b973d95f0a7344d919c6bf38524d21ea7e3542394755ca4f5d257dd51dc7f95',
        'c68f8815d0b804e14da9af2f726dd1bcc4f81eb6c12fb8dfff1e90d1c3a2f68d'),
}
ALIASES={f'item_10:{n:04X}':'item_24:00A8' for n in range(0xA4C,0xA50)}
ACCENTS={'é':0x7C,'ñ':0x87}


def encoded(text,*,reference=False):
    output=bytearray()
    for char in text:
        if char in ACCENTS:
            if not reference:output.append(0x80)
            output.append(ACCENTS[char])
        elif char.isascii() and (char.isalnum() or char in ' .'):
            output.append(ord(char))
        else:raise ValueError('Unapproved accented item spelling or encoding')
    if not output or len(output)>WIDTH:raise ValueError('Complete accented item exceeds sixteen bytes')
    return bytes(output).ljust(WIDTH,b' ')


def candidates(native,rel,symbols):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols.encode())!=SYMBOLS_SHA256:
        raise ValueError('Changed accented item reference executable or symbols')
    sources={b.name:b.entries() for b in banks(native) if b.name.startswith('item_')}
    result=[]
    for id,root in [(id,id) for id in ROWS]+list(ALIASES.items()):
        text,symbol,index,source_hash,reference_hash=ROWS[root]
        bank,n=id.split(':');n=int(n,16);source=sources[bank][n]
        reference=symbol_data(rel,symbols,symbol)[index*16:(index+1)*16]
        if (sha256(source)!=source_hash or sha256(reference)!=reference_hash
                or encoded(text,reference=True)!=reference):
            raise ValueError('Changed exact native/accented English item identity')
        if id in ALIASES:
            item=0x1000+n;converted=ordinary_item(item)
            if root!=f'item_{converted>>8:02X}:{converted&255:04X}':
                raise ValueError('Accented placed name changes native carried conversion')
        value=encoded(text)
        tagged=text.replace('é','{glyph:807C}').replace('ñ','{glyph:8087}')
        result.append({'id':id,'source_sha256':source_hash,'translation':tagged,
            'control_policy':'exact','accent_item_name':root,'status':'source_verified_candidate_not_installed',
            'provenance':{'source':'user-supplied GAFE01 revision 0 disc','reference_id':root,
                'reference_sha256':reference_hash,'encoded_sha256':sha256(value),
                'reference_text':text,'match_basis':'exact_native_identity_and_complete_accented_reference',
                'native_conversion':f'{0x1000+n:04X}->24A8' if id in ALIASES else None}})
    return result


def offset(id):
    bank,index=id.split(':');group=int(bank[5:],16);index=int(index,16)
    order=[*range(0x20,0x30),0x10]
    if group not in order or not 0<=index<COUNTS[order.index(group)]:
        raise ValueError('Accented item resource slot outside its native group')
    return len(HEADER)+(sum(COUNTS[:order.index(group)])+index)*WIDTH


def build(native,rel,symbols,base_data,base_report):
    if (base_report.get('source_sha256')!=sha256(native)
            or base_report.get('data_sha256')!=sha256(base_data)
            or previous_resource(native,base_report['edits'])!=base_data):
        raise ValueError('Changed complete preceding item resource')
    edits=candidates(native,rel,symbols)
    if {r['id'] for r in edits}&{r['id'] for r in base_report['edits']}:
        raise ValueError('Accented candidate overlaps an existing English approval')
    result=bytearray(base_data)
    for row in edits:
        at=offset(row['id']);result[at:at+16]=encoded(ROWS[row['accent_item_name']][0])
    report={'source_sha256':sha256(native),'data_sha256':sha256(result),
            'previous_data_sha256':sha256(base_data),'previous_candidate_slots':len(base_report['edits']),
            'accent_edits':edits,'accent_candidate_slots':len(edits),'installed':False,
            'required_capability':'complete accented font, literal capture, immutable reconstruction, and item readers'}
    return bytes(result),report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=Path('build/design-items-resource'))
    p.add_argument('--output',type=Path,default=Path('build/accent-items-candidate'))
    a=p.parse_args()
    data,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text(),
        (a.base/'names.bin').read_bytes(),json.loads((a.base/'names.json').read_text()))
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'names.bin').write_bytes(data)
    (a.output/'candidates.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'bytes':len(data),'data_sha256':sha256(data),'accent_candidate_slots':8,'installed':False}))


if __name__=='__main__':main()
