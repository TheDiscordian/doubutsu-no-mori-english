"""Translate native Controller Pak label images without changing Pak operations."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,pixels,pack_pixels
from keyboard import label_pixels
from textcodec import encode

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='179c658a70383d278b2b78aa9f2d339c8582ae2cb714e7b95b120163c0104d5d'
ASSET,OWNER=0xB1A000,0x7A10E0
ASSET_SHA='b8c26e67da2581f021d4bc24c91d7870e87bb628f1f4cd89e5c395e0dd31b1bc'
OWNER_SHA='f9a10c58f1e989df18a9f0b5ab6622792e0f01b50a56336711f54ca5950bf22f'
FONT_SHA='dbb3590b722a4cc463f40288d93c2978a12156ec697439e0d3b0d1f985ae43f4'
# Japanese transcription, English replacement, native image, width, load, quad.
ROWS=(('オワリ','Done',0x7560,32,0x6BA8,0x5D70),
      ('のこり','Free',0xBAE0,48,0x7270,0x60B0),
      ('ページ','Pages',0xB960,48,0x72C0,0x60F0),
      ('ノート','Notes',0x76E0,48,0x7370,0x61F0))


def patch_asset(native):
    verified_rom(native);files=by_vrom(native)
    old=files[ASSET].extract(native);owner=files[OWNER].extract(native)
    font=files[FONT_VROM].extract(native)
    if (sha256(old)!=ASSET_SHA or sha256(owner)!=OWNER_SHA or sha256(font)!=FONT_SHA
            or owner[0x1730:0x1738]!=struct.pack('>2I',ASSET,ASSET+len(old))):
        raise ValueError('Changed native Controller Pak asset, owner, or label font')
    atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE]);data=bytearray(old);labels=[]
    for japanese,text,offset,width,load,quad in ROWS:
        pointer=struct.pack('>I',0x0C000000+offset)
        if ([at for at in range(len(old)-3) if old[at:at+4]==pointer]!=[load+4]
                or old[load:load+8]!=struct.pack('>2I',0xFD900000,0x0C000000+offset)
                or old[load+48:load+64]!=struct.pack('>4I',0xF2000000,
                    ((width-1)*4<<12)+60,0x01004008,0x0C000000+quad)):
            raise ValueError('Changed native Controller Pak label reader')
        tile=struct.unpack_from('>I',old,load+40)[0]
        if (tile>>21&7,tile>>19&3)!=(4,0):raise ValueError('Pak label is not native I4')
        texture=pack_pixels(label_pixels(atlas,text,width))
        data[offset:offset+width*8]=texture
        labels.append({'japanese':japanese,'text':text,'texture_vrom':f'{ASSET+offset:08X}',
            'width':width,'height':16,'source_sha256':sha256(old[offset:offset+width*8]),
            'texture_sha256':sha256(texture),'load_offset':load,'quad_offset':quad})
    if len(data)!=len(old):raise ValueError('Controller Pak asset size changed')
    return bytes(data),{'version':1,'native_asset_sha256':ASSET_SHA,'owner_sha256':OWNER_SHA,
        'source_font_sha256':FONT_SHA,'asset_sha256':sha256(data),'labels':labels,
        'font_transform':'Unscaled native Latin glyphs; remove only empty outer columns and centre',
        'cpu_code_changed':False,'allocation_changed':False,'saved_format_changed':False,
        'status':'Four English label images installed; ordinary Controller Pak acceptance pending'}


def build(native,base,report):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Controller Pak artwork requires the complete birthday baseline')
    files=by_vrom(base)
    if sha256(files[ASSET].extract(base))!=ASSET_SHA or sha256(files[OWNER].extract(base))!=OWNER_SHA:
        raise ValueError('Controller Pak baseline contains unrelated changes')
    data,profile=patch_asset(native)
    image,patch,result=rebuild(native,base,report,{ASSET:data})
    result['controller_pak_artwork']=profile
    result['release_status']='English Controller Pak labels and all preceding fixes; ordinary acceptance pending'
    return image,patch,result


def measure_text(ledger,native,built,report):
    expected,profile=patch_asset(native);files=by_vrom(built)
    installed=bool(report.get('controller_pak_artwork'))
    if installed and (report['controller_pak_artwork']!=profile
            or files[ASSET].extract(built)!=expected
            or sha256(files[OWNER].extract(built))!=OWNER_SHA):
        raise ValueError('Changed installed Controller Pak labels or reader')
    for i,((japanese,text,*_),label) in enumerate(zip(ROWS,profile['labels'])):
        identity=f'ui_controller_pak_label:{i:04X}'
        ledger.add(identity,encode(japanese,ledger.info))
        ledger.rows[identity]['source_sha256']=label['source_sha256']
        if installed:
            ledger.rows[identity]['replacements'].append(
                {'route':'controller_pak_artwork','sha256':label['texture_sha256']})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/controller-pak-artwork-01')
    args=parser.parse_args();base=ROOT/'build/birthday-screen-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
