"""Translate the native sale banner and port the English Nookington door label."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,u32,verified_rom
from artwork_chain import rebuild
from building_artwork import donor_texture_pointers,palette_equivalent
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,pixels,pack_pixels
from keyboard import label_pixels
from map_artwork import Donor
from nookington_sign import OBJECT,NEW_OBJECT,TABLE,SEASONS,SLICE_HASHES,OLD_SIZE,NEW_SIZE,SLOT_SIZE
from texture_preview import native_range,decode,png_rgba,rgba5551
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,model_texture_shape
from textcodec import encode

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='0173bb83decfda63b299fb40aedd22121b546818081754032e60fc3b96d9a257'
FONT_SHA='7e4fdb93f1b0109e3d609434163d8c31174ef6699b7d439aef1a8305a18d2798'
OBJECT_SHA='3144a0cfbfff0cb69db0883721f4192747e32c4aeecb1758634088bcf2363a0b'
EXPANDED_SHA='709e617739e96777a6f8915205060a43242c60c9077827718d6c74e1fec70bbb'
READERS={
    TABLE:'a4f33bb4c76cb8c8ebb9df0232e15ccf381ba386b7eed358132b2fb0051a4446',
    0x8CB690:'8b630ea1fcd07133d4c4615d0eb0e69f0f23162f81b68347fd5a2796559b93e4',
    0x8D0D20:'11adb4697e0d2789cedec5ba0eada223dd21c92817e54096a44f6821c1ad0d67',
    0xD5D000:'76ff36c9a7ccd0ad3def96bf3125e1db4fe8e5cdbf1cea2a9f98c96ac505c052',
}
TEXTURE=0xBD8
DOOR=(29,38,3,29)
BLUE=(73,127,17,30)
DONORS=(Donor(0x58A140,0x58C5D8,0x58),Donor(0x58C7C0,0x58EBD8,0x58))
GC_VERTICES={0x58C61C:0x58BA40,0x58EC1C:0x58E040}
GC_VERTEX_BYTES=bytes.fromhex('0fa0000000d500010000fc00000088ff0000000000d5000100000000000088ff'
    '0000177000d5000106000000000088ff0fa0177000d500010600fc00000088ff')


def source(native):
    verified_rom(native);obj=by_vrom(native)[OBJECT].extract(native)
    for (_,old,*_),digest in zip(SEASONS,SLICE_HASHES):
        if sha256(obj[old:old+OLD_SIZE])!=digest:raise ValueError('Changed original Nookington slice')
    return obj


def donor_bindings(rel,symbols):
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied English Nookington source')
    pointers=donor_texture_pointers(rel,DONORS)
    for season,row in zip(('s','w'),DONORS):
        binding=f'obj_{season}_shop4_t2_tex_txt = .data:0x{row.gc:08X}; // type:object size:0x800 '
        if symbols.decode().count(binding)!=1:raise ValueError('Missing scoped Nookington T2 symbol')
        model=rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+row.model_bytes]
        if (model_texture_shape(model)!=(128,32,2,0)
                or model[64:72]!=bytes.fromhex('0100400800000000')):
            raise ValueError('Changed donor doorway dimensions or vertex command')
    found={};table,size=u32(rel,0x28),u32(rel,0x2C)
    for module,first in struct.iter_unpack('>II',rel[table:table+size]):
        section,address=None,0
        for at in range(first,len(rel)-7,8):
            delta,kind,target_section,target=struct.unpack_from('>HBBI',rel,at)
            if kind==203:break
            if kind==202:section,address=target_section,0;continue
            address+=delta
            if section!=5 or address not in GC_VERTICES or kind in (0,201,204):continue
            if ((module,kind,target_section,target)!=(u32(rel,0),1,5,GC_VERTICES[address])
                    or address in found or u32(rel,DATA_BASE+address)!=0
                    or rel[DATA_BASE+target:DATA_BASE+target+64]!=GC_VERTEX_BYTES):
                raise ValueError('Changed actual English door vertex binding')
            found[address]=target
        else:raise ValueError('Unterminated English model relocation stream')
    if found!=GC_VERTICES:raise ValueError('Missing English door vertex fixup')
    return {f'{k:08X}':f'{v:08X}' for k,v in sorted({**pointers,**found}.items())}


def textures(native,font,rel,symbols):
    obj=source(native);bindings=donor_bindings(rel,symbols)
    if sha256(font)!=FONT_SHA:raise ValueError('Changed installed Latin font')
    atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    label=label_pixels(atlas,'CLEARANCE',54)
    if any(label[:54*2]) or any(label[54*14:]):raise ValueError('Clearance glyph ink exceeds retained rows')
    donor=untile(rel[DATA_BASE+0x58C7C0:DATA_BASE+0x58CFC0],128,32,4)
    door_used={donor[y*128+x] for y in range(DOOR[2],DOOR[3]) for x in range(DOOR[0],DOOR[1])}
    result=[];rows=[]
    for i,(season,old,*_) in enumerate(SEASONS):
        palette=native_range(native,0xD5BA08+i*32,32)
        palette_equivalent(palette,rel[DATA_BASE+0x58C7A0:DATA_BASE+0x58C7C0],door_used)
        colours=[rgba5551(v) for v in struct.unpack('>16H',palette)]
        # Keep the original blue and white antialias colours; never change the palette.
        intensity=[]
        for alpha in range(16):
            target=[(colours[9][c]*(15-alpha)+colours[1][c]*alpha)/15 for c in range(3)]
            intensity.append(min((9,8,1),key=lambda k:sum((colours[k][c]-target[c])**2 for c in range(3))))
        original=obj[old+TEXTURE:old+TEXTURE+2048];changed=pixels(original)
        for v in range(DOOR[2],DOOR[3]):
            for u in range(DOOR[0],DOOR[1]):changed[v*128+u]=donor[v*128+u]
        for v in range(BLUE[2],BLUE[3]):
            for u in range(BLUE[0],BLUE[1]):changed[v*128+u]=9
        for y in range(12):
            for x in range(54):changed[(17+y)*128+126-x]=intensity[label[(y+2)*54+x]]
        converted=pack_pixels(changed);result.append(converted)
        rows.append({'season':season,'source_texture_vrom':f'{OBJECT+old+TEXTURE:08X}',
            'source_sha256':sha256(original),'texture_sha256':sha256(converted),
            'japanese':'クリアランス','english':'CLEARANCE','intensity_palette_indices':intensity})
    return result,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'source_font_sha256':FONT_SHA,'door_gc_data_offset':'0058C7C0','donor_bindings':bindings,
        'door_rectangle':list(DOOR),'banner_rectangle':list(BLUE),'textures':rows,
        'geometry_changed':False,'palettes_changed':False,'cpu_code_changed':False,
        'allocation_changed':False,'saved_formats_changed':False,
        'status':'English door and complete clearance lettering installed; ordinary scene acceptance pending'}


def verify_readers(built,native):
    files=by_vrom(built);original=source(native);obj=files[OBJECT].extract(built)
    expanded=files[NEW_OBJECT].extract(built)
    for v,digest in READERS.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed current Nookington reader')
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed retained/streamed Nookington ownership')
    table=files[TABLE].extract(built)
    for i,(_,old,new,start_at,end_at) in enumerate(SEASONS):
        if (u32(table,start_at),u32(table,end_at))!=(0x6000000+new-8,0x6000000+new+NEW_SIZE):
            raise ValueError('Nookington no longer streams the translated slice')
        # Both texture consumers, including all their native vertices and draw commands.
        for begin,end in ((0,0x40),(0x5F0,0x6D0),(0x7E0,0x8B8),(0xB18,0xBD8)):
            if obj[old+begin:old+end]!=original[old+begin:old+end]:
                raise ValueError('Changed retained Nookington texture reader')
            expected=bytearray(original[old+begin:old+end])
            for at,target in ((0x844,TEXTURE),(0x884,0x5F0),(0xB7C,TEXTURE),(0xBC4,0)):
                if begin<=at<end:struct.pack_into('>I',expected,at-begin,0x6000000+new+target)
            if expanded[new+begin:new+end]!=expected:raise ValueError('Changed streamed Nookington texture reader')
        if native_range(built,0xD5BA08+i*32,32)!=native_range(native,0xD5BA08+i*32,32):
            raise ValueError('Changed Nookington palette')


def build(native,base,report,rel,symbols):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Nookington details require the complete gyroid/menu predecessor')
    verify_readers(base,native);files=by_vrom(base)
    old,expanded=files[OBJECT].extract(base),files[NEW_OBJECT].extract(base)
    if sha256(old)!=OBJECT_SHA or sha256(expanded)!=EXPANDED_SHA:
        raise ValueError('Changed approved complete building predecessor')
    converted,profile=textures(native,files[FONT_VROM].extract(base),rel,symbols)
    new_obj,new_expanded=bytearray(old),bytearray(expanded)
    for data,(_,old_at,new_at,*_) in zip(converted,SEASONS):
        for target,offset in ((new_obj,old_at),(new_expanded,old_at),(new_expanded,new_at)):
            if target[offset+TEXTURE:offset+TEXTURE+2048]!=source(native)[old_at+TEXTURE:old_at+TEXTURE+2048]:
                raise ValueError('Nookington details texture has unreviewed changes')
            target[offset+TEXTURE:offset+TEXTURE+2048]=data
    table=files[TABLE].extract(base);checked=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            offset,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=offset<=len(expanded)-size or not 0<size<=SLOT_SIZE:
                raise ValueError('Nookington details exceed the native building slot')
            if kind!=11 and new_expanded[offset:offset+size]!=expanded[offset:offset+size]:
                raise ValueError('Nookington details change another building stream')
            checked+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(new_obj),NEW_OBJECT:bytes(new_expanded)})
    profile.update(object_sha256=sha256(new_obj),streamed_object_sha256=sha256(new_expanded),
        building_ranges_checked=checked)
    result['nookington_details']=profile
    result['nookington_sign']['object_sha256']=sha256(new_expanded)
    for row,(_,_,offset,*_) in zip(result['nookington_sign']['seasons'],SEASONS):
        row['sha256']=sha256(new_expanded[offset:offset+NEW_SIZE])
    result['release_status']='Complete Nookington door/clearance lettering and prior English; ordinary acceptance pending'
    verify_readers(image,native)
    return image,patch,result


def measure_text(ledger,native,built,report):
    original=source(native);installed=report.get('nookington_details')
    if installed:
        verify_readers(built,native);files=by_vrom(built)
        expected,profile=textures(native,files[FONT_VROM].extract(built),
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        obj,expanded=files[OBJECT].extract(built),files[NEW_OBJECT].extract(built)
        profile.update(object_sha256=sha256(obj),streamed_object_sha256=sha256(expanded),building_ranges_checked=92)
        if installed!=profile:raise ValueError('Changed installed Nookington details profile')
        for data,(_,old,new,*_) in zip(expected,SEASONS):
            if any(target[offset+TEXTURE:offset+TEXTURE+2048]!=data
                   for target,offset in ((obj,old),(expanded,old),(expanded,new))):
                raise ValueError('English Nookington details are not fully installed')
    for season,old,*_ in SEASONS:
        identity='art_nookington_clearance:'+season
        ledger.add(identity,encode('クリアランス',ledger.info))
        ledger.rows[identity]['source_sha256']=sha256(original[old+TEXTURE:old+TEXTURE+2048])
        if installed:ledger.credit(identity,b'CLEARANCE','nookington_details')


def project_texture(texture,palette,first,last):
    """Read-only front projection using the native wall/door UV directions."""
    rgba=decode(texture,128,32,'ci4',palette);out=bytearray()
    for y in range(last-first):
        for x in range(32):
            at=((31-x)*128+last-1-y)*4;out.extend(rgba[at:at+4])
    return png_rgba(32,last-first,out,6)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/nookington-details-01');a=p.parse_args()
    base=ROOT/'build/gyroid-service-01';native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((base/'build.json').read_text()),(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for i,(season,old,new,*_) in enumerate(SEASONS):
        palette=native_range(native,0xD5BA08+i*32,32)
        for label,rom,address in (('original',native,OBJECT+old),('english',image,NEW_OBJECT+new)):
            texture=native_range(rom,address+TEXTURE,2048)
            for kind,first,last in (('door',0,48),('poster',72,128)):
                outputs[f'{season}-{kind}-{label}.png']=project_texture(texture,palette,first,last)
    for name,data in outputs.items():
        with (a.output/name).open('xb') as target:target.write(data)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch),
        'building_ranges_checked':report['nookington_details']['building_ranges_checked']}))


if __name__=='__main__':main()
