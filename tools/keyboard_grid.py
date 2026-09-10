"""Map supplied GameCube key layouts to explicit supported native encodings."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from gc_text import decoder_tables
from textcodec import ENCODE
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256

ROOT = Path(__file__).resolve().parents[1]
TABLES = (('letterS_table$440', 0x7F5D8), ('letterS_table2$441', 0x7F600),
          ('letterL_table$442', 0x7F628), ('letterL_table2$443', 0x7F650),
          ('sign_table$444', 0x7F678), ('mark_table$445', 0x7F6A0))
DISABLED = 0xFFFF
GLYPHS_SHA = '027259dafcc1e53f9d65f2039673adf9329f72dd52ee14959ad0f5a613f64d18'


def extract(rel, symbols, glyphs):
    if (sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256 or len(glyphs)!=256
            or sha256(json.dumps(glyphs,ensure_ascii=False,separators=(',',':')).encode())!=GLYPHS_SHA):
        raise ValueError('Unexpected English keyboard reference')
    # Bind the glyph meanings used by this mapping, not an arbitrary decoder.
    if any(glyphs[byte]!=char for byte,char in ((0x20,' '),(0x21,'!'),(0x2A,'~'),(0x90,'ー'),
            (0xD0,';'),(0xD4,'⚷'),(0xCD,'\n'),(0xA7,'☀'),(0xBA,'💀'))):
        raise ValueError('Unexpected GameCube keyboard glyph meanings')
    rows, words = [], []
    for name, address in TABLES:
        if len(re.findall(r'^'+re.escape(name)+r' = \.data:0x'+f'{address:08X}'+r'; // type:object size:0x28 ',
                          symbols.decode(), re.M))!=1:
            raise ValueError('Missing scoped GameCube keyboard table')
        data=rel[DATA_BASE+address:DATA_BASE+address+40]
        entries=[]
        for index, byte in enumerate(data):
            char=glyphs[byte]
            mapped=ENCODE.get(char,DISABLED)
            if char=='~': mapped=ENCODE['～']  # Native fullwidth tilde glyph; same key meaning.
            if char=='☀': mapped=0x80A7
            if char=='💀': mapped=0x80BA
            if mapped in (0x7F,0x80): mapped=DISABLED
            words.append(mapped)
            entries.append({'cell': index, 'gc_byte': f'{byte:02X}', 'native': f'{mapped:04X}',
                            'status': 'disabled' if mapped==DISABLED else 'apology_only' if mapped>255 else 'native'})
        rows.append({'symbol': name, 'data_offset': f'{address:08X}', 'source_sha256': sha256(data), 'keys': entries})
    result=struct.pack('>240H',*words)
    return result, {'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'layout_bytes':len(result),'layout_sha256':sha256(result),'tables':rows,
        'columns':10,'rows':4,'saved_format_changed':False,
        'status':'Mapped layout resource only; not an installed keyboard'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/keyboard-grid-layout')
    args=parser.parse_args()
    data,report=extract((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')['CHAR_MAP'])
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'keys.bin':data,'layout.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target: target.write(value)
    print(json.dumps({'output':str(args.output),'bytes':len(data),'sha256':sha256(data)}))


if __name__=='__main__': main()
