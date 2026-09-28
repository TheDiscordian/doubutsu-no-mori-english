"""Complete streamed-texture NPC meshes through the existing character converter.

This preparation owns no actor ID, runtime allocation, or selection. The caller
must connect the native drawing/voice/actor readers before enabling a character.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import sha256,u32
from apply_translation import write_new
from map_artwork import compile_commands
from title_assets import model_texture_shape,pack4,untile
from v3_furniture_pipeline import Source,ROOT
from v3_gorilla_art import convert_commands
from v3_villager_art import DRAW_BASE,DRAW_STRIDE,native_palette,normalise_vertex_flags
from v3_villager_mesh import faces

MODEL_LIMIT=0x2800
TEXTURE_LIMIT=0x1620


def prepare(source,index):
    table=source.raw('npc_draw_data_tbl')
    if type(index)!=int or not 0<=index<len(table)//DRAW_STRIDE:
        raise ValueError('NPC draw index leaves the verified donor table')
    at=DRAW_BASE+index*DRAW_STRIDE;row=table[index*DRAW_STRIDE:(index+1)*DRAW_STRIDE]
    links=source.pointers(at,DRAW_STRIDE)
    if not {at+4,at+8,at+12,*range(at+16,at+48,4)}<=set(links):
        raise ValueError('NPC lacks a complete skeleton, body, palette, or eight eyes')
    skeleton_at=links[at+4];name,_,size=source.containing(skeleton_at,exact=True)
    skeleton=source.raw(name);joint_count,visible=skeleton[:2]
    if size!=8 or not 1<=visible<=joint_count<=26 or skeleton[2:]!=bytes(6):
        raise ValueError('Unsupported complete rotation skeleton')
    sk_links=source.pointers(skeleton_at,8)
    if set(sk_links)!={skeleton_at+4}:raise ValueError('Missing NPC joint-table binding')
    joints_at=sk_links[skeleton_at+4];joint_name,_,joint_bytes=source.containing(joints_at,exact=True)
    joints=source.raw(joint_name);joint_links=source.pointers(joints_at,joint_bytes)
    if (joint_bytes!=joint_count*12 or len(joint_links)!=visible or
            any((p-joints_at)%12 for p in joint_links)):
        raise ValueError('Incomplete NPC joint model hierarchy')
    # A preorder hierarchy has one root and exhausts each child count exactly.
    pending=1
    for offset in range(0,joint_bytes,12):
        if not pending:raise ValueError('NPC hierarchy has multiple roots')
        pending+=joints[offset+4]-1
    if pending:raise ValueError('NPC hierarchy has missing children')
    models={};vertex_arrays=set();tiles={}
    for target in dict.fromkeys(joint_links.values()):
        label,p,n=source.containing(target,exact=True);raw=source.raw(label)
        pointers=source.pointers(p,n);pos=0
        while pos<n:
            a,b=struct.unpack_from('>II',raw,pos);op=a>>24;step=8
            if op==1:
                address=pointers.get(p+pos+4)
                if address is None:raise ValueError('NPC mesh has an unbound vertex load')
                vertex_arrays.add(source.containing(address))
            elif op==0xFD:
                w,h,fmt,bits=model_texture_shape(raw[pos:pos+8])
                if (fmt,bits)!=(2,0) or b>>24 not in (8,9,11):
                    raise ValueError('Streamed character needs an unsupported texture source')
                if b in tiles and tiles[b]!=(w,h):raise ValueError('Inconsistent NPC texture dimensions')
                tiles[b]=(w,h);step=16
            elif op==0x0A:
                count=(a>>17&127)+1;step=(1+(max(0,count-3)+3)//4)*8
            pos+=step
        if pos!=n:raise ValueError('Truncated NPC mesh command')
        models[target]=(label,raw,pointers)
    if len(vertex_arrays)!=1:raise ValueError('NPC mesh needs one complete shared vertex array')
    vertex_name,vertex,vertex_bytes=vertex_arrays.pop()
    vertices,normalised=normalise_vertex_flags(source.raw(vertex_name))
    if source.pointers(vertex,vertex_bytes):raise ValueError('NPC vertex array contains pointers')
    body_name,body_at,body_size=source.containing(links[at+8],exact=True)
    palette_name,palette_at,palette_size=source.containing(links[at+12],exact=True)
    if palette_size!=32 or source.pointers(palette_at,palette_size) or source.pointers(body_at,body_size):
        raise ValueError('Unbound or pointer-bearing NPC texture data')
    texture=bytearray(native_palette(source.raw(palette_name)));resources=[];eye_offsets=[];mouth_offsets=[]
    # Keep the body first: native drawing preloads 4 KiB at this pointer, even
    # though CI4 models only use the lower 2 KiB before their palettes load.
    # Following expressions and final padding make that complete read safe.
    body_offset=len(texture);texture.extend(bytes(body_size))
    def expressions(first,count,kind):
        result=[]
        for i in range(count):
            p=at+first+i*4
            if p not in links:
                if kind=='mouth' and not any(at+first+j*4 in links for j in range(count)):return []
                raise ValueError('Partial NPC expression set')
            label,address,n=source.containing(links[p],exact=True)
            raw=source.raw(label)
            if n!=256 or source.pointers(address,n):raise ValueError('Unsupported NPC expression size')
            out=pack4(untile(raw,32,16,4));offset=len(texture);texture.extend(out);result.append(offset)
            resources.append(dict(kind=kind,index=i,symbol=label,source_offset=address,bytes=n,
                offset=offset,source_sha256=sha256(raw),sha256=sha256(out),width=32,height=16))
        return result
    eye_offsets=expressions(16,8,'eye');mouth_offsets=expressions(48,6,'mouth')
    if set(links)!={at+4,at+8,at+12,*range(at+16,at+48,4),
            *(range(at+48,at+72,4) if mouth_offsets else ())}:
        raise ValueError('Unhandled NPC draw-record resource')
    body=source.raw(body_name);converted=bytearray(body_size);used=bytearray(body_size)
    bindings={}
    for pointer,(w,h) in sorted(tiles.items()):
        segment,offset=pointer>>24,pointer&0xFFFFFF;n=w*h//2
        if segment in (8,9):
            if offset or (w,h)!=(32,16) or segment==9 and not mouth_offsets:
                raise ValueError('Mesh references an absent or partial facial expression')
            bindings[pointer]=(pointer,w,h);continue
        if offset+n>body_size or any(used[offset:offset+n]):
            raise ValueError('Overlapping or out-of-bounds body tile')
        raw=body[offset:offset+n];out=pack4(untile(raw,w,h,4))
        converted[offset:offset+n]=out;used[offset:offset+n]=bytes([1])*n
        resources.append(dict(kind='body',symbol=body_name,source_offset=body_at+offset,
            bytes=n,offset=body_offset+offset,source_sha256=sha256(raw),sha256=sha256(out),width=w,height=h))
        bindings[pointer]=(0x07000000+offset,w,h)
    if not all(used):raise ValueError('Unaccounted NPC body texels')
    texture[body_offset:body_offset+body_size]=converted
    # The streamed lists replace that preload with exact per-material loads.
    # No texture is cropped, overlapped, or changed to satisfy the read bounds.
    texture.extend(bytes(max(0,body_offset+4096-len(texture))))
    texture.extend(bytes(-len(texture)%16))
    if len(texture)>TEXTURE_LIMIT:raise ValueError('Complete NPC texture bank exceeds its reserved buffer')
    text=['/* Generated from the supplied donor; do not distribute. */','#include <PR/mbi.h>']
    sections=[];records=[]
    for target,(label,raw,pointers) in models.items():
        # All matrices are written before the graphics task executes. A mesh
        # may reference a later joint (Tortimer's mouth uses the head matrix).
        commands,native_bytes,materials,triangles=convert_commands(raw,target,pointers,vertex,vertex_bytes,
            streamed_textures=bindings,matrix_count=visible)
        text.extend((f'const Gfx {label}[] __attribute__((section(".{label}"),aligned(8))) = {{',*commands,'};'))
        sections.append((label,native_bytes));records.append(dict(symbol=label,donor_offset=target,
            source_sha256=sha256(raw),bytes=native_bytes,materials=materials,triangles=triangles))
    return dict(source='\n'.join(text)+'\n',sections=tuple(sections),records=records,
        vertices=vertices,vertex_start=vertex,vertex_bytes=vertex_bytes,vertex_flags_normalised=normalised,
        skeleton=skeleton,joints=joints,joints_at=joints_at,joint_links=joint_links,
        texture=bytes(texture),body_offset=body_offset,body_bytes=body_size,
        eye_offsets=eye_offsets,mouth_offsets=mouth_offsets,resources=resources,
        draw_index=index,draw_row=row,draw_sha256=sha256(row),
        aliases=[i for i in range(len(table)//DRAW_STRIDE)
            if table[i*DRAW_STRIDE:(i+1)*DRAW_STRIDE]==row and
            {p-(DRAW_BASE+i*DRAW_STRIDE):t for p,t in source.pointers(DRAW_BASE+i*DRAW_STRIDE,DRAW_STRIDE).items()}
            =={p-at:t for p,t in links.items()}])


def build(source,index,output):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored NPC output')
    prepared=prepare(source,index);output.mkdir(parents=True)
    write_new(output/'commands.c',prepared['source'].encode())
    compiled=compile_commands(output/'gbi',output/'commands.c',prepared['sections'])
    model=bytearray(prepared['vertices']);offsets={}
    for r in prepared['records']:
        data=compiled[r['symbol']];offsets[r['donor_offset']]=len(model)
        original=source.raw(r['symbol'])
        donor=faces(original,donor=True,streamed=True,vertex_start=prepared['vertex_start'],
            vertex_bytes=prepared['vertex_bytes'],start=r['donor_offset'],
            pointers=source.pointers(r['donor_offset'],len(original)))
        native=faces(data,donor=False,vertex_bytes=prepared['vertex_bytes'],streamed=True)
        if len(donor)!=len(native):raise ValueError('Converted NPC loses mesh faces')
        for (df,dm),(nf,nm) in zip(donor,native):
            image,w,h,pair,extent=dm;target,tile,mode,nw,nh=nm
            if image>>24==11:image=0x07000000|(image&0xFFFFFF)
            wrap={0:2,1:0,2:1}
            if (not any(nf==df[i:]+df[:i] for i in range(3)) or target!=image or
                    (tile>>9&511)*8!=w//2 or mode>>20&15!=pair>>12&15 or
                    (1<<(mode>>4&15),1<<(mode>>14&15))!=(w,h) or
                    ((nw-1)*4,(nh-1)*4)!=extent or
                    (mode>>8&3,mode>>18&3)!=(wrap[pair>>10&3],wrap[pair>>8&3])):
                raise ValueError('Converted NPC changes a face, joint matrix, or texture binding')
        r.update(offset=len(model),sha256=sha256(data));model.extend(data)
    joint_offset=len(model);joints=bytearray(prepared['joints'])
    for p,target in prepared['joint_links'].items():
        struct.pack_into('>I',joints,p-prepared['joints_at'],0x06000000+offsets[target])
    model.extend(joints);skeleton_offset=len(model)
    model.extend(prepared['skeleton'][:4]+struct.pack('>I',0x06000000+joint_offset))
    model.extend(bytes(-len(model)%16))
    if len(model)>MODEL_LIMIT:raise ValueError('Complete streamed NPC mesh exceeds its reserved model bank')
    write_new(output/'model.bin',model);write_new(output/'texture.bin',prepared['texture'])
    report=dict(format='AFV3-NPC-STREAM-ART-1',draw_index=index,source_aliases=prepared['aliases'],
        donor_draw_sha256=prepared['draw_sha256'],model_bytes=len(model),model_sha256=sha256(model),
        texture_bytes=len(prepared['texture']),texture_sha256=sha256(prepared['texture']),
        skeleton=0x06000000+skeleton_offset,joint_offset=joint_offset,
        joints=prepared['skeleton'][0],visible_joints=prepared['skeleton'][1],
        vertices=prepared['vertex_bytes']//16,triangles=sum(r['triangles'] for r in prepared['records']),
        model_limit=MODEL_LIMIT,texture_limit=TEXTURE_LIMIT,body_offset=prepared['body_offset'],
        body_bytes=prepared['body_bytes'],eye_offsets=prepared['eye_offsets'],mouth_offsets=prepared['mouth_offsets'],
        resources=prepared['resources'],models=prepared['records'],runtime_installed=False,
        animations_installed=False,selectable=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in ('tools/v3_npc_stream_art.py',
            'tools/v3_gorilla_art.py','tools/v3_villager_mesh.py','tools/v3_villager_art.py',
            'tools/title_assets.py','tools/map_artwork.py')})
    write_new(output/'art.json',(json.dumps(report,indent=2)+'\n').encode());return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draw-index',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    r=build(source,args.draw_index,args.output)
    print(json.dumps({k:r[k] for k in ('model_bytes','texture_bytes','joints','visible_joints','triangles','runtime_installed')}))
