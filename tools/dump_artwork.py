"""Port both English dump signs while retaining native models and collection rules."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,u32,verified_rom
from artwork_chain import rebuild
from building_artwork import Texture,donor_texture_pointers,palette_equivalent,model_refs,OBJECT
from nookington_sign import NEW_OBJECT,TABLE,SLOT_SIZE
from nookington_details import READERS,verify_readers as verify_nookington
from texture_preview import native_range,decode,png_rgba
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='2795a31a259996395dafb5df4e46c00f46a1109eda46e6a15119927d9d01d193'
ROWS=(Texture('obj_s_dump_t1_tex',0xD6E4D0,0x5208A0,0xD5C1C8,0x5018C0,0x5218A0,0x440,0x521CE0,0x90),
      Texture('obj_w_dump_t1_tex',0xD6FAC8,0x521E00,0xD5C1C8,0x5018C0,0x522E00,0x440,0x523240,0x90))
RANGES=((0xFEE8,0x114D0),(0x114E0,0x12AC8))


def assets(native,rel,symbols):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied English dump artwork source')
    pointers=donor_texture_pointers(rel,ROWS);obj=by_vrom(native)[OBJECT].extract(native)
    converted={};labels=[]
    for row in ROWS:
        binding=f'{row.symbol} = .data:0x{row.gc:08X}; // type:object size:0x800 '
        if symbols.decode().count(binding)!=1:raise ValueError('Missing exact dump texture symbol')
        model=rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        if model_texture_shape(model)!=(128,32,2,0):raise ValueError('Changed English dump texture shape')
        samples=untile(rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048],128,32,4)
        palette_equivalent(native_range(native,row.native_palette,32),
            rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32],set(samples))
        refs,count=model_refs(obj,row,rel[DATA_BASE+row.gc_vertices:DATA_BASE+row.gc_vertices+row.vertex_bytes])
        if len(refs)!=1 or count!=44:raise ValueError('Changed native dump model/UV readers')
        result=pack4(samples);at=row.native-OBJECT;original=obj[at:at+2048]
        if original==result:raise ValueError('English dump does not replace Japanese artwork')
        converted[row.native]=result
        labels.append({'symbol':row.symbol,'native_texture_vrom':f'{row.native:08X}',
            'gc_texture_offset':f'{row.gc:08X}','source_sha256':sha256(original),
            'texture_sha256':sha256(result),'native_loads':refs,'matched_vertex_uses':count,
            'japanese':'ゴミ 月木','english':'Dump'})
    return converted,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'textures':labels,'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'geometry_changed':False,'palettes_changed':False,'code_changed':False,'allocation_changed':False,
        'saved_formats_changed':False,'collection_schedule_changed':False,
        'status':'Both English dump signs installed; ordinary scene/hardware acceptance pending'}


def verify_readers(native,built):
    original=by_vrom(native);files=by_vrom(built)
    for v,digest in READERS.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed current building loader/range/palette table')
    old,obj=original[OBJECT].extract(native),files[OBJECT].extract(built)
    expanded=files[NEW_OBJECT].extract(built)
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed dump retained/streamed object ownership')
    table=files[TABLE].extract(built);palette_table=files[0xD5D000].extract(built)
    for i,(row,(start,end)) in enumerate(zip(ROWS,RANGES)):
        starts,ends=((8,0xC0),(0x178,0x230))[i]
        if ((u32(table,starts+0x28*4),u32(table,ends+0x28*4))!=(0x6000000+start-8,0x6000000+end)
                or u32(palette_table,8+(0x51+i*91)*4)!=0x60011C8
                or native_range(built,row.native_palette,32)!=native_range(native,row.native_palette,32)):
            raise ValueError('Changed dump seasonal reader or palette')
        at=row.native-OBJECT
        if obj[start:at]!=old[start:at] or obj[at+2048:end]!=old[at+2048:end]:
            raise ValueError('Dump model, animation, or second atlas changed')


def build(native,base,report,rel,symbols):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Dump artwork requires the complete Nookington detail predecessor')
    verify_readers(native,base);verify_nookington(base,native)
    converted,profile=assets(native,rel,symbols);files=by_vrom(base)
    old=files[OBJECT].extract(base);expanded=files[NEW_OBJECT].extract(base)
    obj,new_expanded=bytearray(old),bytearray(expanded)
    for address,data in converted.items():
        at=address-OBJECT
        if old[at:at+2048]!=native_range(native,address,2048):
            raise ValueError('Dump texture already has unrelated edits')
        obj[at:at+2048]=data;new_expanded[at:at+2048]=data
    table=files[TABLE].extract(base);count=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            at,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=at<=len(expanded)-size or not 0<size<=SLOT_SIZE:
                raise ValueError('Dump artwork exceeds a native building slot')
            if kind!=0x28 and expanded[at:at+size]!=new_expanded[at:at+size]:
                raise ValueError('Dump artwork changes another building')
            count+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(obj),NEW_OBJECT:bytes(new_expanded)})
    profile['building_ranges_checked']=count
    result['dump_artwork']=profile
    result['nookington_sign']['object_sha256']=sha256(new_expanded)
    result['nookington_details'].update(object_sha256=sha256(obj),streamed_object_sha256=sha256(new_expanded))
    result['release_status']='English dump signs and complete prior artwork/menu/text; ordinary acceptance pending'
    verify_readers(native,image);verify_nookington(image,native)
    return image,patch,result


def measure_text(ledger,native,built,report):
    verified_rom(native);installed=report.get('dump_artwork')
    if installed:
        verify_readers(native,built)
        converted,profile=assets(native,(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        profile['building_ranges_checked']=92
        if installed!=profile:raise ValueError('Changed installed English dump profile')
        for address,data in converted.items():
            if any(native_range(built,owner+address-OBJECT,2048)!=data for owner in (OBJECT,NEW_OBJECT)):
                raise ValueError('English dump is absent from a retained or active stream')
    for i,row in enumerate(ROWS):
        identity='art_dump_sign:'+('summer' if i==0 else 'winter')
        ledger.add_transcribed_artwork(identity,'ゴミ 月木',native_range(native,row.native,2048))
        if installed:ledger.credit(identity,b'Dump','dump_artwork')


def projection(texture,palette):
    rgba=decode(texture,128,32,'ci4',palette);out=bytearray()
    for y in range(36):
        for x in range(32):
            at=((31-x)*128+92+y)*4;out.extend(rgba[at:at+4])
    return png_rgba(32,36,out,6)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/dump-artwork-01');a=p.parse_args()
    base=ROOT/'build/nookington-details-01';native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((base/'build.json').read_text()),(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for season,row in zip(('summer','winter'),ROWS):
        palette=native_range(native,row.native_palette,32)
        for name,rom,address in (('original',native,row.native),('english',image,NEW_OBJECT+row.native-OBJECT)):
            outputs[f'{season}-{name}.png']=projection(native_range(rom,address,2048),palette)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,data in outputs.items():
        with (a.output/name).open('xb') as target:target.write(data)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
