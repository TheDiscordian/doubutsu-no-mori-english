"""Bind the eight complete accented names to exact donor articles and checksums."""
import argparse
import json
from pathlib import Path
import struct
import zlib
from aflib import sha256
import accent_items
from gc_names import symbol_data
from item_articles import verify as previous_verify,DESIGN_NAMES_HASH,DESIGN_DATA_HASH

ROOT=Path(__file__).resolve().parents[1]
DONORS={
    'item_24:00A8':('itemArt_Cloth',168,1,'cfb9b14b8f6e8cd2ab2e0874b0a5ddeee5711aba14c0ca2541f4c32a0c67350b'),
    'item_25:0005':('itemArt_Etc',5,1,'af121e89852b8ed34022e1f94f1e645edb37a5fab8977bededfc2382ca8177e1'),
    'item_2A:0031':('itemArt_MiniDisk',49,0,'02779466cdec163811d078815c633f21901413081449002f24aa3e80f0b88ef7'),
    'item_2A:0033':('itemArt_MiniDisk',51,0,'02779466cdec163811d078815c633f21901413081449002f24aa3e80f0b88ef7'),
}


def build(native,rel,symbols,names,previous):
    edits=accent_items.candidates(native,rel,symbols)
    if (previous_verify(previous)!=DESIGN_NAMES_HASH or sha256(previous)!=DESIGN_DATA_HASH
            or sha256(names)!='693ef2c0749822d07062114ffff0b35b4bb8a56d3b2617c932d9220dcc92165b'):
        raise ValueError('Accented articles require exact complete item and preceding article resources')
    output=bytearray(previous);output[16:48]=bytes.fromhex(sha256(names));rows={}
    for edit in edits:
        root=edit['accent_item_name'];symbol,index,article,digest=DONORS[root]
        donor=symbol_data(rel,symbols,symbol)
        if sha256(donor)!=digest or donor[index]!=article:raise ValueError('Changed complete donor article table')
        slot=(accent_items.offset(edit['id'])-32)//16
        name=names[32+slot*16:48+slot*16]
        if name!=accent_items.encoded(accent_items.ROWS[root][0]):raise ValueError('Changed accented article spelling')
        row=slot if slot<756 else 756+(slot-756)//4
        data=bytes((article,))+struct.pack('>I',zlib.crc32(name))
        if row in rows and rows[row]!=data:raise ValueError('Accented placed articles disagree')
        rows[row]=data
        output[48+row*5:53+row*5]=data
    if len(rows)!=5:raise ValueError('Incomplete accented article rows')
    return bytes(output),{'names_sha256':sha256(names),'data_sha256':sha256(output),
        'previous_data_sha256':sha256(previous),'changed_rows':sorted(rows),'bytes':len(output),'installed':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('build/accent-item-articles'))
    a=p.parse_args()
    data,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text(),
        (ROOT/'build/accent-items-candidate/names.bin').read_bytes(),
        (ROOT/'build/design-items-articles/articles.bin').read_bytes())
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/'articles.bin').write_bytes(data)
    (a.output/'articles.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
