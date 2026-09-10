"""Port English catalogue navigation labels without changing native controls."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from building_artwork import donor_texture_pointers
from map_artwork import Donor,compile_commands
from notice_artwork import source_pixels,expected_load
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='4fcebd1758f3ca5bed1a9c7dd3659f961f27d51572ea5b4f13c49039e2b8d963'
VROM=0xB2A000
NATIVE_SHA='73aa49c3e550ca30ea5f09f222f0dac6f05189b2d7e5bbe90410f61a2354038a'
# name, actual donor pointer, width, texture, load, quad, native left edge
ROWS=(('top',Donor(0x3E4E60,0x3E5AD0,8),32,0x9B8,0x768,0x600,18),
      ('bottom',Donor(0x3E5060,0x3E5AB0,8),64,0xDB8,0x718,0x5C0,68))


def commands(directory):
    return compile_commands(directory,ROOT/'overlays/catalogue_artwork/labels.c',
                            tuple((row[0],56) for row in ROWS))


def patch_assets(native,rel,symbols,compiled):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Unexpected English catalogue artwork source')
    files=by_vrom(native);old=files[VROM].extract(native)
    if sha256(old)!=NATIVE_SHA or set(compiled)!={row[0] for row in ROWS}:
        raise ValueError('Unexpected native catalogue asset or command inventory')
    if files[0x7A28F0].extract(native)[0x9890:0x9898]!=struct.pack('>2I',VROM,VROM+len(old)):
        raise ValueError('Native catalogue asset binding changed')
    pointers=donor_texture_pointers(rel,tuple(row[1] for row in ROWS))
    data=bytearray(old);records=[]
    for name,donor,width,target,load,quad,left in ROWS:
        if model_texture_shape(rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+8])!=(width,16,3,1):
            raise ValueError('English catalogue label shape changed')
        if (old[load:load+56]!=expected_load(target,64,False)
                or old[load+56:load+72]!=struct.pack('>4I',0x01004008,0x0C000000+quad,0x06000204,0x00020604)):
            raise ValueError('Native catalogue load/quad/triangles changed')
        refs=[at for at in range(0,len(old)-7,8)
              if old[at:at+8]==struct.pack('>2I',0xFD700000,0x0C000000+target)]
        if refs!=[load]:raise ValueError('Unaccounted catalogue texture reader')
        expected=expected_load(target,width,True)
        if compiled[name]!=expected:raise ValueError('Compiled catalogue load differs from native GBI')
        value=source_pixels(rel,donor,width)
        data[target:target+1024]=value+bytes(1024-len(value))
        data[load:load+56]=expected
        for at in range(quad,quad+64,16):
            x,y,z,flag,s,t,*colour=struct.unpack_from('>3hH2h4B',old,at)
            if (x not in (left,left+56) or y not in (-79,-93) or z or flag
                    or s not in (0,2048) or t not in (0,512)):
                raise ValueError('Native catalogue label geometry changed')
            struct.pack_into('>h',data,at,left+(x-left)*width//64)
            struct.pack_into('>h',data,at+8,s*width//64)
        records.append({'label':name,'gc_texture':f'{donor.gc:08X}',
            'texture_vrom':f'{VROM+target:08X}','width':width,'height':16,
            'texture_sha256':sha256(value),'load_sha256':sha256(expected)})
    data=bytes(data)
    return data,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'asset_vrom':f'{VROM:08X}','native_asset_sha256':NATIVE_SHA,'asset_sha256':sha256(data),
        'labels':records,'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'command_source_sha256':sha256((ROOT/'overlays/catalogue_artwork/labels.c').read_bytes()),
        'allocation_changed':False,'cpu_code_changed':False,'saved_format_changed':False,
        'native_controls_preserved':True,'status':'English catalogue labels installed; ordinary acceptance pending'}


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Catalogue artwork requires the complete notice/tune baseline')
    if sha256(by_vrom(base)[VROM].extract(base))!=NATIVE_SHA:
        raise ValueError('Catalogue asset already contains unrelated changes')
    data,profile=patch_assets(native,rel,symbols,compiled)
    image,patch,result=rebuild(native,base,report,{VROM:data})
    result['catalogue_artwork']=profile
    result['release_status']='English catalogue controls with all prior fixes; ordinary screen acceptance pending'
    return image,patch,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/catalogue-artwork-01')
    args=parser.parse_args();base=ROOT/'build/tune-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        commands(ROOT/'build/catalogue-artwork-commands'))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
