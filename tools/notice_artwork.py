"""Port all four bulletin-board control labels without changing saved notices."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom
from artwork_chain import rebuild
from building_artwork import donor_texture_pointers
from map_artwork import Donor,compile_commands,port_quad
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='2725492f603d6dda9d1984ae4e3dcced520786a6c43e9180082e288d62cdd419'
VROM=0xABA000
NATIVE_SHA='9b21110f4a2cbbdaae0fcfed2c1c1ebb3f929dc0af9ac756e5716543d9f86d38'
# label, donor, width, original texture, new texture, load, quad, donor vertex index
ROWS=(('latest',Donor(0x4C3A20,0x4CCFF0,8),80,0x858,0x858,0x610,0x200,24),
      ('entry',Donor(0x4C3F20,0x4CCFD0,8),64,0xC58,0xD58,0x5C0,0x1C0,20),
      ('quit',Donor(0x4C4320,0x4CD020,8),32,0x1058,0x1158,0x680,0x240,28),
      ('write',Donor(0x4C4520,0x4CD058,8),64,0x1458,0x1458,0x6F0,0x280,32))
QUAD_LEFT={'latest':-128,'entry':-13,'quit':71,'write':79}


def commands(directory):
    return compile_commands(directory,ROOT/'overlays/notice_artwork/labels.c',
                            tuple((row[0],56) for row in ROWS))


def expected_load(offset,width,clamp):
    mask=0 if width==80 else 6 if width==64 else 5
    mode=(0x90200 if clamp else 0x50100)+(mask<<4)
    return struct.pack('>14I',0xFD700000,0x0C000000+offset,0xF5700000,0x07000000+mode,
        0xE6000000,0,0xF3000000,0x07000000+((width*16//2-1)<<12)+((2048+width//8-1)//(width//8)),
        0xE7000000,0,0xF5680000+((width//8)<<9),mode,0xF2000000,((width-1)*4<<12)+60)


def source_pixels(rel,donor,width):
    values=untile(rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*16],width,16,8)
    return bytes((v<<4&240)|(v>>4) for v in values)


def patch_assets(native,rel,symbols,compiled):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Unexpected English notice-artwork source')
    pointers=donor_texture_pointers(rel,tuple(row[1] for row in ROWS))
    old=by_vrom(native)[VROM].extract(native)
    if sha256(old)!=NATIVE_SHA or set(compiled)!={row[0] for row in ROWS}:
        raise ValueError('Unexpected native notice asset or compiled-label inventory')
    data=bytearray(old);data[0x858:0x1858]=bytes(4096)
    regions=[];records=[]
    for name,donor,width,original,target,load,quad,index in ROWS:
        if model_texture_shape(rel[DATA_BASE+donor.gc_model:DATA_BASE+donor.gc_model+8])!=(width,16,3,1):
            raise ValueError('English notice label dimensions changed')
        if old[load:load+56]!=expected_load(original,64,False):
            raise ValueError('Native notice label load changed')
        if old[load+56:load+64]!=struct.pack('>2I',0x01004008,0x0C000000+quad):
            raise ValueError('Native notice label quad reference changed')
        refs=[at for at in range(0,len(old)-7,8)
              if old[at:at+8]==struct.pack('>2I',0xFD700000,0x0C000000+original)]
        if refs!=[load]:raise ValueError('Native label has an unaccounted texture reader')
        expected=expected_load(target,width,True)
        if compiled[name]!=expected:raise ValueError('Compiled label differs from native GBI specification')
        converted=source_pixels(rel,donor,width)
        if not 0x858<=target<target+len(converted)<=0x1858:
            raise ValueError('English label exceeds the original four-label allocation')
        if any(target<b and a<target+len(converted) for a,b in regions):
            raise ValueError('English labels overlap')
        regions.append((target,target+len(converted)))
        data[target:target+len(converted)]=converted;data[load:load+56]=expected
        source_quad=rel[DATA_BASE+0x4CCBA0+index*16:DATA_BASE+0x4CCBA0+(index+4)*16]
        result=bytearray(port_quad(old[quad:quad+64],source_quad,scale=1))
        old_vertices=list(struct.iter_unpack('>3hH2h4B',old[quad:quad+64]))
        source_vertices=list(struct.iter_unpack('>3hH2h4B',source_quad))
        sx=min(v[0] for v in source_vertices);sy=max(v[1] for v in source_vertices)
        ny=max(v[1] for v in old_vertices)
        for at in range(0,64,16):
            x,y=struct.unpack_from('>2h',result,at)
            struct.pack_into('>2h',result,at,x-sx+QUAD_LEFT[name],y-sy+ny)
        data[quad:quad+64]=result
        records.append({'label':name,'gc_texture':f'{donor.gc:08X}',
            'native_texture':f'{VROM+target:08X}','width':width,'height':16,
            'texture_sha256':sha256(converted),'load_sha256':sha256(expected),
            'quad_sha256':sha256(result)})
    # Keep the native up/down glyphs, at their native size and Y, before each label.
    for quad,old_left,new_left in ((0x180,-64,-142),(0x140,-5,-27)):
        for at in range(quad,quad+64,16):
            x=struct.unpack_from('>h',old,at)[0]
            if x not in (old_left,old_left+14):raise ValueError('Native notice arrow position changed')
            struct.pack_into('>h',data,at,x-old_left+new_left)
    data=bytes(data)
    return data,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'asset_vrom':f'{VROM:08X}','native_asset_sha256':NATIVE_SHA,'asset_sha256':sha256(data),
        'labels':records,'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'command_source_sha256':sha256((ROOT/'overlays/notice_artwork/labels.c').read_bytes()),
        'texture_region_bytes':4096,'texture_bytes_used':3840,'allocation_changed':False,
        'cpu_code_changed':False,'saved_format_changed':False,'native_icons_preserved':True,
        'status':'English control artwork installed; ordinary screen acceptance pending'}


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Notice artwork requires the complete corrected keyboard/artwork baseline')
    if sha256(by_vrom(base)[VROM].extract(base))!=NATIVE_SHA:
        raise ValueError('Notice artwork already contains unrelated changes')
    data,profile=patch_assets(native,rel,symbols,compiled)
    image,patch,result=rebuild(native,base,report,{VROM:data})
    result['notice_artwork']=profile
    result['release_status']='English bulletin-board controls with all prior fixes; ordinary screen acceptance pending'
    return image,patch,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/notice-artwork-01')
    args=parser.parse_args();base=ROOT/'build/keyboard-grid-cursor-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
        commands(ROOT/'build/notice-artwork-commands'))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
