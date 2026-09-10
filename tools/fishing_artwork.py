"""Port source-matching English fishing props without changing the fishing event."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,u32,verified_rom
from artwork_chain import rebuild
from building_artwork import Texture,donor_texture_pointers,palette_equivalent,model_refs,OBJECT
from map_artwork import Donor,compile_commands
from nookington_sign import NEW_OBJECT,TABLE,SLOT_SIZE
from nookington_details import READERS,verify_readers as verify_nookington
from texture_preview import native_range,decode,png_rgba
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,model_texture_shape
from police_artwork import native_triangles

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='5c5206c9a8ee548900ba264276f5052a4ed8b5a13803ffcf1a6b44c880f17226'
NOOP=bytes.fromhex('E000000000000000')
GC_TRIANGLES=bytes.fromhex('0A0A8398A41882000000F731CD62D490')
# side, type, palette type, slice start/end, T1, T3, T3 vertices/triangles,
# GC vertices/count, GC T1/T3 command, GC T3 vertex pointer site/target.
ROWS=(('left',0x25,0x4E,0x8C7A8,0x8E828,0xDEB028,0xDEC028,0x8CC58,0x8CFE0,
       0x5B81E0,0x5B0,0x5B87B0,0x5B8870,0x5B888C,0x5B8690),
      ('right',0x26,0x4F,0x8A738,0x8C798,0xDE8F98,0xDE9F98,0x8ABC8,0x8AF50,
       0x5B88A8,0x590,0x5B8E58,0x5B8F18,0x5B8F34,0x5B8D38))
RETAINED=(0,1,2,3,4,5,6,7,8,9,10,11,16,17,18,19)
GC_TOPOLOGY=((0,1,2),(3,4,5),(6,7,8),(9,10,11),(12,13,14),(12,14,15))


def commands(out):
    return compile_commands(out,ROOT/'overlays/fishing/artwork.c',(('remove',8),))['remove']


def vertex_bindings(rel):
    wanted={row[13]:row[14] for row in ROWS};found={}
    table,size=u32(rel,0x28),u32(rel,0x2C)
    for module,first in struct.iter_unpack('>II',rel[table:table+size]):
        section,address=None,0
        for at in range(first,len(rel)-7,8):
            delta,kind,target_section,target=struct.unpack_from('>HBBI',rel,at)
            if kind==203:break
            if kind==202:section,address=target_section,0;continue
            address+=delta
            if section!=5 or address not in wanted or kind in (0,201,204):continue
            if ((module,kind,target_section,target)!=(u32(rel,0),1,5,wanted[address])
                    or address in found or u32(rel,DATA_BASE+address)!=0
                    or rel[DATA_BASE+address-4:DATA_BASE+address]!=bytes.fromhex('01010020')
                    or rel[DATA_BASE+address+4:DATA_BASE+address+20]!=GC_TRIANGLES):
                raise ValueError('Changed actual GC fishing placard omission binding')
            found[address]=target
        else:raise ValueError('Unterminated supplied fishing model fixup stream')
    if found!=wanted:raise ValueError('Missing actual GC fishing vertex fixup')
    return found


def changes(native,rel,symbols,compiled):
    verified_rom(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256 or compiled!=NOOP:
        raise ValueError('Changed English fishing source or independently compiled native command')
    original=by_vrom(native)[OBJECT].extract(native)
    donors=tuple(Donor(target,row[index],8) for row in ROWS for target,index in ((0x5B69E0,11),(0x5B79E0,12)))
    pointers=donor_texture_pointers(rel,donors);vertices=vertex_bindings(rel)
    for name,at in (('obj_e_turi_t1_tex',0x5B69E0),('obj_e_turi_t3_tex',0x5B79E0)):
        if symbols.decode().count(f'{name} = .data:0x{at:08X}; // type:object size:0x800 ')!=1:
            raise ValueError('Missing scoped fishing source texture symbol')
    result={};textures=[];geometry=[]
    for i,row in enumerate(ROWS):
        side,kind,pal,start,end,t1,t3,vtx,tri,gc_vtx,vbytes,cmd1,cmd3,_,target=row
        palette=0xD5C168+i*32
        for name,native_at,gc_at,command in (('barrel',t1,0x5B69E0,cmd1),('portrait',t3,0x5B79E0,cmd3)):
            if model_texture_shape(rel[DATA_BASE+command:DATA_BASE+command+8])!=(128,32,2,0):
                raise ValueError('Changed English fishing texture shape')
            samples=untile(rel[DATA_BASE+gc_at:DATA_BASE+gc_at+2048],128,32,4)
            palette_equivalent(native_range(native,palette,32),rel[DATA_BASE+0x5B69C0:DATA_BASE+0x5B69E0],set(samples))
            converted=pack4(samples);at=native_at-OBJECT
            result[at]=converted
            textures.append({'side':side,'kind':name,'native_texture_vrom':f'{native_at:08X}',
                'gc_texture_offset':f'{gc_at:08X}','source_sha256':sha256(original[at:at+2048]),
                'texture_sha256':sha256(converted)})
        source=Texture('barrel',t1,0x5B69E0,palette,0x5B69C0,gc_vtx,vbytes,cmd1,8)
        refs,count=model_refs(original,source,rel[DATA_BASE+gc_vtx:DATA_BASE+gc_vtx+vbytes])
        if len(refs)!=1 or count!=(48 if i==0 else 46):raise ValueError('Changed original fishing barrel vertex uses')
        native_vertices=[original[vtx+n*16:vtx+(n+1)*16] for n in range(20)]
        donor_vertices=[rel[DATA_BASE+target+n*16:DATA_BASE+target+(n+1)*16] for n in range(16)]
        key=lambda vertex:vertex[:6]+vertex[8:]
        if [key(native_vertices[n]) for n in RETAINED]!=[key(v) for v in donor_vertices]:
            raise ValueError('GC fishing adaptation changes retained geometry/UV/lighting')
        expected=struct.pack('>2I',0x01014028,0x6000000+vtx)
        if (original[tri-8:tri]!=expected or original[tri+32:tri+40]!=bytes.fromhex('DF00000000000000')
                or original[tri+16:tri+24]!=bytes.fromhex('06181A1C00181C1E')):
            raise ValueError('Changed native fishing placard draw reader')
        old=native_triangles(original[tri:tri+32]);mapped=tuple(tuple(RETAINED[n] for n in t) for t in GC_TOPOLOGY)
        if old!=list(mapped[:4])+[(12,13,14),(12,14,15)]+list(mapped[4:]):
            raise ValueError('Native fishing triangles differ beyond the scoped placard')
        result[tri+16]=compiled
        geometry.append({'side':side,'barrel_vertex_uses':count,'native_barrel_loads':refs,
            'removed_triangle_offset':f'{tri+16:06X}','removed_triangles':[[12,13,14],[12,14,15]],
            'retained_triangles':[list(t) for t in mapped],'remaining_vertices_unchanged':True})
    return result,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'textures':textures,'geometry':geometry,
        'donor_texture_pointers':{f'{k:08X}':f'{v:08X}' for k,v in pointers.items()},
        'donor_vertex_pointers':{f'{k:08X}':f'{v:08X}' for k,v in vertices.items()},
        'command_source_sha256':sha256((ROOT/'overlays/fishing/artwork.c').read_bytes()),
        'command_sha256':sha256(compiled),'palettes_changed':False,'cpu_code_changed':False,
        'allocation_changed':False,'saved_formats_changed':False,'event_logic_changed':False,
        'status':'English-GC barrel/portrait and scoped placard omission; ordinary event acceptance pending'}


def verify_installed(native,built,expected):
    original=by_vrom(native);files=by_vrom(built)
    for v,digest in READERS.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed current fishing structure reader')
    obj=files[OBJECT].extract(built);expanded=files[NEW_OBJECT].extract(built)
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed retained/current fishing resource ownership')
    table=files[TABLE].extract(built);palettes=files[0xD5D000].extract(built)
    old=original[OBJECT].extract(native)
    for i,row in enumerate(ROWS):
        side,kind,pal,start,end,*_=row
        for season,(starts,ends) in enumerate(((8,0xC0),(0x178,0x230))):
            if ((u32(table,starts+kind*4),u32(table,ends+kind*4))!=(0x6000000+start-8,0x6000000+end)
                    or u32(palettes,8+(pal+season*91)*4)!=0x6001168+i*32):
                raise ValueError('Changed fishing season or palette reader')
        if native_range(native,0xD5C168+i*32,32)!=native_range(built,0xD5C168+i*32,32):
            raise ValueError('Changed fishing palette')
        wanted=bytearray(old[start:end])
        for at,data in expected.items():
            if start<=at<end:wanted[at-start:at-start+len(data)]=data
        if obj[start:end]!=wanted or expanded[start:end]!=wanted:
            raise ValueError('Fishing changes are absent or alter an unrelated native field')


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Fishing artwork requires the complete English dump predecessor')
    expected,profile=changes(native,rel,symbols,compiled)
    verify_installed(native,base,{})
    files=by_vrom(base);old=files[OBJECT].extract(base);expanded=files[NEW_OBJECT].extract(base)
    obj,new_expanded=bytearray(old),bytearray(expanded)
    for at,data in expected.items():obj[at:at+len(data)]=data;new_expanded[at:at+len(data)]=data
    table=files[TABLE].extract(base);count=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            at,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=at<=len(expanded)-size or not 0<size<=SLOT_SIZE:
                raise ValueError('Fishing artwork exceeds a native building slot')
            if kind not in (0x25,0x26) and expanded[at:at+size]!=new_expanded[at:at+size]:
                raise ValueError('Fishing artwork changes another building')
            count+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(obj),NEW_OBJECT:bytes(new_expanded)})
    profile['building_ranges_checked']=count;result['fishing_artwork']=profile
    result['nookington_sign']['object_sha256']=sha256(new_expanded)
    result['nookington_details'].update(object_sha256=sha256(obj),streamed_object_sha256=sha256(new_expanded))
    result['release_status']='English-GC fishing artwork and all prior fixes; ordinary event acceptance pending'
    verify_installed(native,image,expected);verify_nookington(image,native)
    return image,patch,result


def measure_text(ledger,native,built,report):
    verified_rom(native);installed=report.get('fishing_artwork')
    if installed:
        expected,profile=changes(native,(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),NOOP)
        profile['building_ranges_checked']=92
        if installed!=profile:raise ValueError('Changed English fishing artwork profile')
        verify_installed(native,built,expected)
    for row in ROWS:
        for kind,japanese,address in (('barrel','魚政',row[5]),('headquarters','本部',row[6])):
            identity=f'art_fishing:{row[0]}:{kind}'
            ledger.add_transcribed_artwork(identity,japanese,native_range(native,address,2048))
            if installed:
                proof=expected[address-OBJECT] if kind=='barrel' else expected[row[8]+16]
                ledger.rows[identity]['replacements'].append({'route':'fishing_artwork',
                    'sha256':sha256(proof),'intentional_gc_artwork_omission':True})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/fishing-artwork-01');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    base=ROOT/'build/dump-artwork-01';native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((base/'build.json').read_text()),(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),commands(a.output/'gbi'))
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for i,row in enumerate(ROWS):
        for kind,at in (('barrel',row[5]),('portrait',row[6])):
            texture=native_range(image,NEW_OBJECT+at-OBJECT,2048)
            outputs[f'{row[0]}-{kind}.png']=png_rgba(128,32,
                decode(texture,128,32,'ci4',native_range(native,0xD5C168+i*32,32)),4)
    for name,data in outputs.items():
        with (a.output/name).open('xb') as target:target.write(data)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
