"""Convert the supplied GC fortune table inside the original native model allocation."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,u32,verified_rom
from artwork_chain import rebuild
from map_artwork import compile_commands
from nookington_sign import OBJECT,NEW_OBJECT,TABLE,SLOT_SIZE
from nookington_details import READERS,verify_readers as verify_nookington
from texture_preview import native_range,decode,png_rgba,rgba5551
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,untile,pack4,rgb5a3,model_texture_shape
from police_artwork import native_triangles

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='ec2917b38e47e936b69b203ffa99913e7fedad9d4ae29e8c368db5441b64ed13'
START,END,ENTRY,PACK,MODEL=0x21EE8,0x23BA8,0x22388,0x223A8,0x23118
SLICE_SHA='0c547c6a0e81556f63dba55d0eaa5805142c4ae7ea7414b8069b53c9e29a8ca3'
ACTORS={0x9428A0:'f703f3c123d8a1433af942970bae72c8592ea7d53c608a9c608b26a6ff7d8b0d',
        0x942E50:'d599b128dae9e9a5046981273458dc40fb3c84ee172665be07b134ca31457ee2'}
OLD_ENTRY=bytes.fromhex('DE000000060221A8DE00000006022248DE000000060222E0DF00000000000000')
NEW_ENTRY=bytes.fromhex('DE00000006023118DF00000000000000E000000000000000E000000000000000')
MODEL_SHA='b6a87f4315dc26fff9ab629f823940fcdfb0883af09f2db054771de0bdd7d711'
POINTERS={0x53E92C:0x53DBC0,0x53E934:0x53DDE0,0x53E954:0x53E5E0,
          0x53E984:0x53DBA0,0x53E98C:0x53DBE0,0x53E99C:0x53E790}
TRIANGLES=(
    ((0,1,2),(0,2,3),(1,4,5),(1,5,2),(6,7,8),(6,8,9),(10,11,12),(11,13,12),
     (11,14,13),(11,15,14),(16,17,18),(19,20,21),(20,22,21),(19,23,20),
     (23,24,20),(24,25,20),(25,22,20),(24,26,25)),
    tuple(t for i in range(0,24,4) for t in ((i,i+1,i+2),(i,i+2,i+3))),
)


def commands(out):
    return compile_commands(out,ROOT/'overlays/mikuji/artwork.c',(('entry',32),('model',416)))


def packed_triangles(data,vertices):
    """Decode the actual GC five-bit triangle stream and reject nonzero padding."""
    if not data or len(data)%8:raise ValueError('Invalid packed GC triangle length')
    a,b=struct.unpack_from('>II',data)
    count=(a>>17&127)+1
    if a>>24!=0x0A or b&15 or not 3<=count<=127:raise ValueError('Unsupported packed GC triangle header')
    result=[]
    for i,(a,b) in enumerate(struct.iter_unpack('>II',data)):
        if b&15:raise ValueError('Unknown packed GC triangle mode')
        words=[b>>4&0x7FFF,((a&3)<<13)|(b>>19&0x1FFF),a>>2&0x7FFF]
        if i:words.append(a>>17&0x7FFF)
        result.extend(tuple(w>>shift&31 for shift in (0,5,10)) for w in words)
    if len(data)!=(1+(max(0,count-3)+3)//4)*8 or any(t!=(0,0,0) for t in result[count:]):
        raise ValueError('Packed GC triangle count or padding changed')
    if any(v>=vertices for t in result[:count] for v in t):raise ValueError('GC triangle escapes loaded vertices')
    return tuple(result[:count])


def source_bindings(rel,symbols):
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied GC fortune-table source')
    for name,at,size in (('obj_e_mikuji_1',0x53DDE0,0x800),('obj_e_mikuji_2',0x53DBE0,0x200),
                         ('obj_e_mikuji_v',0x53E5E0,0x330),('obj_e_mikuji_model',0x53E910,0xB8)):
        if symbols.decode().count(f'{name} = .data:0x{at:08X}; // type:object size:0x{size:X} ')!=1:
            raise ValueError('Missing exact GC fortune-table symbol')
    found={};table,size=u32(rel,0x28),u32(rel,0x2C)
    for module,first in struct.iter_unpack('>II',rel[table:table+size]):
        section,address=None,0
        for at in range(first,len(rel)-7,8):
            delta,kind,target_section,target=struct.unpack_from('>HBBI',rel,at)
            if kind==203:break
            if kind==202:section,address=target_section,0;continue
            address+=delta
            if section!=5 or not 0x53E910<=address<0x53E9C8 or kind in (0,201,204):continue
            if ((module,kind,target_section)!=(u32(rel,0),1,5) or POINTERS.get(address)!=target
                    or address in found or u32(rel,DATA_BASE+address)!=0):
                raise ValueError('Changed actual fortune-table material/vertex fixup')
            found[address]=target
        else:raise ValueError('Unterminated GC fortune-table fixup stream')
    if found!=POINTERS:raise ValueError('Missing GC fortune-table fixup')
    for at,shape in ((0x53E930,(64,64,2,0)),(0x53E988,(32,32,2,0))):
        if model_texture_shape(rel[DATA_BASE+at:DATA_BASE+at+8])!=shape:
            raise ValueError('Changed GC fortune-table texture format')
    if (packed_triangles(rel[DATA_BASE+0x53E958:DATA_BASE+0x53E980],27)!=TRIANGLES[0]
            or packed_triangles(rel[DATA_BASE+0x53E9A0:DATA_BASE+0x53E9C0],24)!=TRIANGLES[1]):
        raise ValueError('GC fortune-table triangle sequence changed')
    return {f'{k:08X}':f'{v:08X}' for k,v in found.items()}


def convert_palette(data):
    if len(data)!=32:raise ValueError('Fortune table requires exactly sixteen palette entries')
    result=bytearray()
    for word, in struct.iter_unpack('>H',data):
        colour=rgb5a3(word)
        if colour[3] not in (0,255):raise ValueError('GC fortune palette needs unsupported partial alpha')
        converted=(colour[0]>>3)<<11|(colour[1]>>3)<<6|(colour[2]>>3)<<1|int(bool(colour[3]))
        if colour[3] and rgba5551(converted)!=colour:raise ValueError('GC fortune palette loses a visible colour')
        result.extend(struct.pack('>H',converted))
    return bytes(result)


def source(native):
    verified_rom(native);files=by_vrom(native);obj=files[OBJECT].extract(native)
    if sha256(obj[START:END])!=SLICE_SHA or obj[ENTRY:PACK]!=OLD_ENTRY:
        raise ValueError('Changed original fortune-booth slice or root display list')
    for v,digest in ACTORS.items():
        if sha256(files[v].extract(native))!=digest:raise ValueError('Changed original fortune-table actor')
    if files[0x9428A0].extract(native).count(bytes.fromhex('3C18060227182388'))!=1:
        raise ValueError('Changed native fortune-table root draw call')
    return obj


def package(native,rel,symbols,compiled):
    old=source(native);bindings=source_bindings(rel,symbols)
    if (set(compiled)!={'entry','model'} or compiled['entry']!=NEW_ENTRY
            or len(compiled['model'])!=416 or sha256(compiled['model'])!=MODEL_SHA):
        raise ValueError('Changed independently compiled fortune-table commands')
    model=compiled['model']
    if (tuple(native_triangles(model[21*8:30*8]))!=TRIANGLES[0]
            or tuple(native_triangles(model[45*8:51*8]))!=TRIANGLES[1]):
        raise ValueError('Native model does not retain every GC triangle in order')
    native_vertices=[]
    for at in (0x21EE8,0x21FC8,0x22088):
        count={0x21EE8:14,0x21FC8:12,0x22088:18}[at]
        native_vertices.extend(struct.unpack_from('>3h',old,at+i*16) for i in range(count))
    native_bounds=[(min(v[i] for v in native_vertices),max(v[i] for v in native_vertices)) for i in range(3)]
    gc_vertices=rel[DATA_BASE+0x53E5E0:DATA_BASE+0x53E910];new_vertices=bytearray()
    positions=[]
    for vertex in (gc_vertices[i:i+16] for i in range(0,len(gc_vertices),16)):
        if vertex[6:8]!=b'\0\1':raise ValueError('Unknown GC vertex flag')
        new_vertices.extend(vertex[:6]+b'\0\0'+vertex[8:]);positions.append(struct.unpack_from('>3h',vertex))
    bounds=[(min(v[i] for v in positions),max(v[i] for v in positions)) for i in range(3)]
    if any(low<nlow or high>nhigh for (low,high),(nlow,nhigh) in zip(bounds,native_bounds)):
        raise ValueError('GC fortune-table geometry escapes the original booth bounds')
    palettes=[convert_palette(rel[DATA_BASE+at:DATA_BASE+at+32]) for at in (0x53DBC0,0x53DBA0)]
    textures=[pack4(untile(rel[DATA_BASE+at:DATA_BASE+at+w*h//2],w,h,4))
              for at,w,h in ((0x53DDE0,64,64),(0x53DBE0,32,32))]
    data=b''.join(palettes+textures+[bytes(new_vertices),model])
    if len(new_vertices)!=816 or PACK+len(data)!=0x232B8 or PACK+len(data)>END:
        raise ValueError('GC fortune table exceeds the original texture storage')
    return data,{'version':1,'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'source_slice_sha256':SLICE_SHA,'donor_pointers':bindings,'package_sha256':sha256(data),
        'package_object_offset':f'{PACK:06X}','package_bytes':len(data),'unused_slice_tail_bytes':END-PACK-len(data),
        'vertex_count':51,'triangle_count':30,'native_bounds':[list(b) for b in native_bounds],
        'gc_bounds':[list(b) for b in bounds],'native_command_sha256':MODEL_SHA,
        'command_source_sha256':sha256((ROOT/'overlays/mikuji/artwork.c').read_bytes()),
        'native_entry_sha256':sha256(NEW_ENTRY),'max_texture_tmem_bytes':2048,
        'palette_sha256':[sha256(p) for p in palettes],'texture_sha256':[sha256(t) for t in textures],
        'visible_colours_exact':True,'shared_palette_changed':False,'actor_code_changed':False,
        'allocation_changed':False,'saved_formats_changed':False,'event_logic_changed':False,
        'status':'Complete source-matching GC fortune table installed; ordinary scene/event acceptance pending'}


def verify_installed(native,built,data=None):
    old=source(native);files=by_vrom(built)
    for v,digest in {**READERS,**ACTORS}.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed fortune-table actor/relocation/structure reader')
    table=files[TABLE].extract(built)
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        if (u32(table,starts+0x20*4),u32(table,ends+0x20*4))!=(0x6000000+START-8,0x6000000+END):
            raise ValueError('Fortune table no longer uses the native seasonal slot')
    obj,expanded=files[OBJECT].extract(built),files[NEW_OBJECT].extract(built)
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed retained/streamed fortune-table ownership')
    expected=bytearray(old[START:END])
    if data is not None:
        expected[ENTRY-START:PACK-START]=NEW_ENTRY
        expected[PACK-START:PACK-START+len(data)]=data
    for actual in (obj,expanded):
        if actual[START:END]!=expected:raise ValueError('Fortune-table model is absent or changes an unrelated native field')


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Fortune-table artwork requires the complete fishing predecessor')
    verify_installed(native,base);data,profile=package(native,rel,symbols,compiled)
    files=by_vrom(base);old=files[OBJECT].extract(base);expanded=files[NEW_OBJECT].extract(base)
    obj,new_expanded=bytearray(old),bytearray(expanded)
    for target in (obj,new_expanded):target[ENTRY:PACK]=NEW_ENTRY;target[PACK:PACK+len(data)]=data
    table=files[TABLE].extract(base);count=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            at,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=at<=len(expanded)-size or not 0<size<=SLOT_SIZE:
                raise ValueError('Fortune table exceeds a native building slot')
            if kind!=0x20 and expanded[at:at+size]!=new_expanded[at:at+size]:
                raise ValueError('Fortune table changes another building stream')
            count+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(obj),NEW_OBJECT:bytes(new_expanded)})
    profile['building_ranges_checked']=count;result['fortune_booth_artwork']=profile
    result['nookington_sign']['object_sha256']=sha256(new_expanded)
    result['nookington_details'].update(object_sha256=sha256(obj),streamed_object_sha256=sha256(new_expanded))
    result['release_status']='GC English fortune-table artwork and all prior fixes; ordinary event acceptance pending'
    verify_installed(native,image,data);verify_nookington(image,native)
    return image,patch,result


def measure_text(ledger,native,built,report):
    source(native);installed=report.get('fortune_booth_artwork')
    if installed:
        # The installed command hash is checked against its independently compiled identity.
        model=native_range(built,NEW_OBJECT+MODEL,416)
        data,profile=package(native,(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),
            {'entry':NEW_ENTRY,'model':model})
        profile['building_ranges_checked']=92
        if profile!=installed:raise ValueError('Changed installed fortune-table artwork profile')
        verify_installed(native,built,data)
    identity='art_fortune_booth:label'
    ledger.add_transcribed_artwork(identity,'おみくじ',native_range(native,0xD80BA8,2048))
    if installed:ledger.rows[identity]['replacements'].append({'route':'fortune_booth_artwork',
        'sha256':sha256(data),'intentional_gc_artwork_omission':True})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/fortune-booth-artwork-01');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    base=ROOT/'build/fishing-artwork-01';native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),
        json.loads((base/'build.json').read_text()),(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),commands(a.output/'gbi'))
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for name,texture,palette,w,h in (('table',0x223E8,0x223A8,64,64),('decoration',0x22BE8,0x223C8,32,32)):
        outputs[name+'.png']=png_rgba(w,h,decode(native_range(image,NEW_OBJECT+texture,w*h//2),w,h,'ci4',
            native_range(image,NEW_OBJECT+palette,32)),4)
    for name,value in outputs.items():
        with (a.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch),
        'model':report['fortune_booth_artwork']}))


if __name__=='__main__':main()
