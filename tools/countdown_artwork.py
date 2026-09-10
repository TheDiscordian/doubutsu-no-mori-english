"""Install the exact GC English countdown labels without changing the timer."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,u32,verified_rom
from artwork_chain import rebuild
from building_artwork import Texture,donor_texture_pointers,palette_equivalent,model_refs
from map_artwork import Donor
from nookington_sign import OBJECT,NEW_OBJECT,TABLE,SLOT_SIZE
from nookington_details import READERS,verify_readers as verify_nookington
from texture_preview import native_range,decode,png_rgba
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='69c695c746959f9c3f5b2bda3d56020ce24fdd7a1ec341285ea9696f0738c7c4'
START,END=0x6838,0x8C80
SLICE_SHA='951601010899e42143c277c7aff2412923726bbce2a80bdacb71c8b16f886b01'
ROWS=(Texture('obj_e_count_t2_tex_txt',0xD65A58,0x518640,0xD5C0E8,0x501800,0x5196C0,0x3B0,0x519B60,8),
      Texture('obj_e_count_t3_tex_txt',0xD66258,0x518E40,0xD5C0E8,0x501800,0x5196C0,0x3B0,0x519B90,8))
DONORS=(Donor(0x518640,0x519B60,8),Donor(0x518E40,0x519B90,8),
        Donor(0x518640,0x519BD8,8),Donor(0x518E40,0x519C08,8))
ACTORS={0x944E90:'4cd38ec47aa9e77dcb892daff87e8485ddb56de27b2b76e12f2bf0dc55cb9099',
        0x945A20:'c52cbfe1f17a672d222c9a8a27de4c5c2d99b5d37d470ed5b681e28204ba68a2',
        0x94B4B0:'ec0d4ecb90e43428bdccb9ca20ede1ecacb9189bb205e4d07c981607036f1db1',
        0x94BF40:'0d1040793f9e3771611b391c04fa095b62874f9b40e05f1c4f47c0cb0c968faa'}


def assets(native,rel,symbols):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied English countdown source')
    obj=by_vrom(native)[OBJECT].extract(native)
    if sha256(obj[START:END])!=SLICE_SHA:raise ValueError('Changed original countdown slice')
    pointers=donor_texture_pointers(rel,DONORS)
    vertex_pointers={0x519B7C:0x5198F0,0x519BF4:0x5197F0};found={}
    table,size=u32(rel,0x28),u32(rel,0x2C)
    for module,first in struct.iter_unpack('>II',rel[table:table+size]):
        section,address=None,0
        for at in range(first,len(rel)-7,8):
            delta,kind,target_section,target=struct.unpack_from('>HBBI',rel,at)
            if kind==203:break
            if kind==202:section,address=target_section,0;continue
            address+=delta
            if section!=5 or address not in vertex_pointers or kind in (0,201,204):continue
            if ((module,kind,target_section)!=(u32(rel,0),1,5) or vertex_pointers[address]!=target
                    or address in found or u32(rel,DATA_BASE+address)!=0):
                raise ValueError('Changed actual countdown vertex fixup')
            found[address]=target
        else:raise ValueError('Unterminated countdown fixup stream')
    if found!=vertex_pointers:raise ValueError('Missing actual countdown vertex bindings')
    if native_range(native,0xD65258,2048)!=pack4(untile(rel[DATA_BASE+0x517E40:DATA_BASE+0x518640],128,32,4)):
        raise ValueError('COUNTDOWN/NEW YEAR source artwork is no longer identical')
    converted={};profiles=[]
    # Both native consumers match the exact vertex groups loaded by the donor models.
    gc_vertices=(rel[DATA_BASE+0x5198F0:DATA_BASE+0x5198F0+192]
                 +rel[DATA_BASE+0x5197F0:DATA_BASE+0x5197F0+256])
    for row in ROWS:
        if symbols.decode().count(f'{row.symbol} = .data:0x{row.gc:08X}; // type:object size:0x800 ')!=1:
            raise ValueError('Missing exact countdown texture symbol')
        if model_texture_shape(rel[DATA_BASE+row.gc_model:DATA_BASE+row.gc_model+8])!=(128,32,2,0):
            raise ValueError('Changed countdown texture shape')
        samples=untile(rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048],128,32,4)
        palette_equivalent(native_range(native,row.native_palette,32),rel[DATA_BASE+0x501800:DATA_BASE+0x501820],set(samples))
        refs,count=model_refs(obj,row,gc_vertices)
        if len(refs)!=2 or count!=14:raise ValueError('Changed countdown texture readers')
        data=pack4(samples);converted[row.native]=data
        profiles.append({'symbol':row.symbol,'native_texture_vrom':f'{row.native:08X}',
            'gc_texture_offset':f'{row.gc:08X}','source_sha256':sha256(native_range(native,row.native,2048)),
            'texture_sha256':sha256(data),'native_loads':refs,'matched_vertex_uses':count})
    return converted,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'textures':profiles,'donor_pointers':{f'{k:08X}':f'{v:08X}' for k,v in sorted({**pointers,**found}.items())},
        'geometry_changed':False,'palettes_changed':False,'animation_changed':False,'actors_changed':False,
        'allocation_changed':False,'saved_formats_changed':False,'timer_logic_changed':False,
        'status':'Exact GC English countdown artwork installed; ordinary event acceptance pending'}


def verify_readers(native,built):
    original=by_vrom(native);files=by_vrom(built)
    for v,digest in {**READERS,**ACTORS}.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed countdown actor or structure reader')
    old=original[OBJECT].extract(native);obj=files[OBJECT].extract(built);expanded=files[NEW_OBJECT].extract(built)
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed countdown retained/streamed ownership')
    table=files[TABLE].extract(built);pal=files[0xD5D000].extract(built)
    for i,(starts,ends) in enumerate(((8,0xC0),(0x178,0x230))):
        if ((u32(table,starts+0x21*4),u32(table,ends+0x21*4))!=(0x6000000+START-8,0x6000000+END)
                or u32(pal,8+(0x4A+i*91)*4)!=0x60010E8):raise ValueError('Changed seasonal countdown reader')
    if (obj[START:0x7A58]!=old[START:0x7A58] or obj[0x8A58:END]!=old[0x8A58:END]
            or obj[0x8C98:0xA418]!=old[0x8C98:0xA418]
            or native_range(built,0xD5C0E8,32)!=native_range(native,0xD5C0E8,32)):
        raise ValueError('Changed countdown model, animation, digits, or palette')


def build(native,base,report,rel,symbols):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Countdown artwork requires the complete fortune-booth predecessor')
    verify_readers(native,base);converted,profile=assets(native,rel,symbols);files=by_vrom(base)
    old=files[OBJECT].extract(base);expanded=files[NEW_OBJECT].extract(base)
    obj,new_expanded=bytearray(old),bytearray(expanded)
    for address,data in converted.items():
        at=address-OBJECT
        if old[at:at+2048]!=native_range(native,address,2048):raise ValueError('Countdown atlas already has unrelated edits')
        obj[at:at+2048]=data;new_expanded[at:at+2048]=data
    table=files[TABLE].extract(base);checked=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            at,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=at<=len(expanded)-size or not 0<size<=SLOT_SIZE:raise ValueError('Countdown exceeds a building slot')
            if kind!=0x21 and expanded[at:at+size]!=new_expanded[at:at+size]:raise ValueError('Countdown changes another structure')
            checked+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(obj),NEW_OBJECT:bytes(new_expanded)})
    profile['building_ranges_checked']=checked;result['countdown_artwork']=profile
    result['nookington_sign']['object_sha256']=sha256(new_expanded)
    result['nookington_details'].update(object_sha256=sha256(obj),streamed_object_sha256=sha256(new_expanded))
    result['release_status']='English countdown and all prior artwork/text; ordinary event acceptance pending'
    verify_readers(native,image);verify_nookington(image,native)
    return image,patch,result


def measure_text(ledger,native,built,report):
    verified_rom(native);installed=report.get('countdown_artwork')
    if installed:
        verify_readers(native,built)
        converted,profile=assets(native,(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        profile['building_ranges_checked']=92
        if profile!=installed:raise ValueError('Changed installed countdown profile')
        for address,data in converted.items():
            if any(native_range(built,owner+address-OBJECT,2048)!=data for owner in (OBJECT,NEW_OBJECT)):
                raise ValueError('English countdown is absent from a retained or active object')
    for label,japanese,english,address in (('prefix','あと',None,0xD65A58),('minutes','ふん',b'min.',0xD66258),
                                           ('seconds','びょう',b'sec.',0xD66258)):
        identity='art_countdown:'+label;ledger.add_transcribed_artwork(identity,japanese,native_range(native,address,2048))
        if installed:
            if english:ledger.credit(identity,english,'countdown_artwork')
            else:ledger.rows[identity]['replacements'].append({'route':'countdown_artwork',
                'sha256':sha256(converted[address]),'intentional_gc_artwork_omission':True})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'build/countdown-artwork-01');a=p.parse_args()
    base=ROOT/'build/fortune-booth-artwork-01';native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for label,rom in (('original',native),('english',image)):
        for row in ROWS:
            outputs[f'{label}-{row.native:08X}.png']=png_rgba(128,32,decode(native_range(rom,row.native,2048),128,32,
                'ci4',native_range(native,0xD5C0E8,32)),5)
    a.output.mkdir(parents=True,exist_ok=False)
    for name,data in outputs.items():
        with (a.output/name).open('xb') as target:target.write(data)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
