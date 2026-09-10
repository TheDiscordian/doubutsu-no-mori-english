"""Inspect the supplied GC festival mesh and its reflected-placement differences."""
import argparse
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
import struct

from aflib import sha256,u32
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256,model_texture_shape

ROOT=Path(__file__).resolve().parents[1]
MODELS=(0x5BB2E8,0x5BC368)
VERTICES=(0x5BA4C0,0x5BB540)
TEXTURES={0x5B8FC0:(64,32),0x5B93C0:(128,32),0x5B9BC0:(32,16),0x5B9CC0:(64,64)}
PALETTES=(0x5B8F60,0x5B8F80,0x5B8FA0)


def packed(data,count_vertices):
    if not data or len(data)%8:raise ValueError('Invalid packed stall triangle bytes')
    first,second=struct.unpack_from('>II',data);count=(first>>17&127)+1
    size=(1+(max(0,count-3)+3)//4)*8
    if first>>24!=0x0A or second&15 or size!=len(data):raise ValueError('Unsupported stall triangle header')
    result=[]
    for i,(a,b) in enumerate(struct.iter_unpack('>II',data)):
        if b&15:raise ValueError('Unsupported stall triangle mode')
        words=[b>>4&32767,((a&3)<<13)|(b>>19&8191),a>>2&32767]
        if i:words.append(a>>17&32767)
        result.extend(tuple(w>>shift&31 for shift in (0,5,10)) for w in words)
    if any(t!=(0,0,0) for t in result[count:]) or any(v>=count_vertices for t in result[:count] for v in t):
        raise ValueError('Stall triangles escape loaded vertices or have nonzero padding')
    return result[:count]


def source(rel,symbols):
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:raise ValueError('Changed supplied GC stall source')
    for name,at,size in (('obj_e_yatai_l_model',MODELS[0],0x258),('obj_e_yatai_r_model',MODELS[1],0x258),
                         ('obj_e_yatai_l_v',VERTICES[0],0xE20),('obj_e_yatai_r_v',VERTICES[1],0xE20)):
        if symbols.decode().count(f'{name} = .data:0x{at:08X}; // type:object size:0x{size:X} ')!=1:
            raise ValueError('Missing exact GC stall model symbol')
    pointers={};table,size=u32(rel,0x28),u32(rel,0x2C)
    for module,first in struct.iter_unpack('>II',rel[table:table+size]):
        section,address=None,0
        for at in range(first,len(rel)-7,8):
            delta,kind,target_section,target=struct.unpack_from('>HBBI',rel,at)
            if kind==203:break
            if kind==202:section,address=target_section,0;continue
            address+=delta
            if (section!=5 or not any(base<=address<base+0x258 for base in MODELS)
                    or kind in (0,201,204)):continue
            if (module,kind,target_section)!=(u32(rel,0),1,5) or address in pointers or u32(rel,DATA_BASE+address):
                raise ValueError('Changed stall model relocation')
            pointers[address]=target
        else:raise ValueError('Unterminated stall source fixup stream')
    models=[];used=set()
    for base,vertex_base in zip(MODELS,VERTICES):
        at=base;rows=[];loaded=[];material=None;palette=None;lit=False
        while at<base+0x258:
            a,b=struct.unpack_from('>II',rel,DATA_BASE+at);op=a>>24
            record={'at':at,'words':(a,b),'opcode':op}
            if op in (0xF0,0xFD,0x01):
                if at+4 not in pointers:raise ValueError('Missing active stall source pointer')
                record['target']=pointers[at+4];used.add(at+4)
            if op==0xF0:
                if a!=0xF08F4010 or record['target'] not in PALETTES:raise ValueError('Unknown stall palette load')
                palette=record['target']
            elif op==0xFD:
                material=record['target'];shape=model_texture_shape(rel[DATA_BASE+at:DATA_BASE+at+8])
                if material not in TEXTURES or shape!=(*TEXTURES[material],2,0):raise ValueError('Unknown stall texture')
                record.update(palette=palette,width=shape[0],height=shape[1])
            elif op==0xD9:
                if a!=0xD9000000 or b not in (0x210405,0x230405):raise ValueError('Unknown stall geometry mode')
                lit=bool(b&0x20000)
            elif op==0x01:
                start=record['target']-vertex_base;count=(a>>12)&255
                if start<0 or start%16 or not 1<=count<=32 or start+count*16>0xE20 or a!=(0x01000000|count<<12|count<<1):
                    raise ValueError('Stall vertex load escapes its bound array')
                loaded=[rel[DATA_BASE+vertex_base+start+i*16:DATA_BASE+vertex_base+start+(i+1)*16] for i in range(count)]
                record.update(start=start//16,count=count)
            elif op==0x0A:
                if not loaded or material is None:raise ValueError('Stall triangles lack vertices/material')
                count=(a>>17&127)+1;size=(1+(max(0,count-3)+3)//4)*8
                if at+size>base+0x258:raise ValueError('Stall triangles escape the model')
                triangles=packed(rel[DATA_BASE+at:DATA_BASE+at+size],len(loaded))
                record.update(triangles=triangles,loaded=loaded,material=material,lit=lit)
                rows.append(record);at+=size;continue
            elif op==0xDF:
                if a!=0xDF000000 or b or at!=base+0x250:raise ValueError('Unknown stall model termination')
            elif op not in (0xD7,0xFC,0xE2,0xD2,0xFA):raise ValueError('Unknown stall graphics command')
            rows.append(record);at+=8
        models.append(rows)
    if used!=set(pointers):raise ValueError('Unaccounted stall model pointer')
    return models,pointers


def reflected(vertex,lit):
    value=bytearray(vertex)
    struct.pack_into('>h',value,0,-struct.unpack_from('>h',value)[0])
    if lit:value[12]=(-value[12])&255
    return bytes(value)


def faces(model,mirror=False):
    out=[]
    for row in model:
        for indices in row.get('triangles',[]):
            vertices=[row['loaded'][i] for i in indices]
            if mirror:vertices=[reflected(v,row['lit']) for v in vertices][::-1]
            out.append((row['material'],row['lit'],vertices))
    return out


def plane_boundaries(triangles):
    buckets=defaultdict(Counter)
    for material,lit,vertices in triangles:
        xyz=[struct.unpack_from('>3h',v) for v in vertices]
        u=[xyz[1][i]-xyz[0][i] for i in range(3)];w=[xyz[2][i]-xyz[0][i] for i in range(3)]
        normal=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]]
        divisor=math.gcd(*normal)
        if not divisor:raise ValueError('Degenerate source stall triangle')
        plane=tuple(x//divisor for x in normal);plane+=(-sum(plane[i]*xyz[0][i] for i in range(3)),)
        edges=buckets[(material,lit,plane)]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            if edges[(b,a)]:edges[(b,a)]-=1
            else:edges[(a,b)]+=1
    return {key:+value for key,value in buckets.items() if +value}


def inspect(rel,symbols):
    models,pointers=source(rel,symbols);left,right=faces(models[0],True),faces(models[1])
    key=lambda face:(face[0],face[1],tuple(sorted(face[2])))
    a,b=Counter(map(key,left)),Counter(map(key,right))
    edges_a,edges_b=plane_boundaries(left),plane_boundaries(right)
    return {'source_rel_sha256':REL_SHA256,'source_symbols_sha256':SYMBOLS_SHA256,
        'donor_pointer_count':len(pointers),'triangles_per_variant':[len(left),len(right)],
        'identical_reflected_triangle_faces':sum((a&b).values()),
        'reflected_left_only_faces':sum((a-b).values()),'right_only_faces':sum((b-a).values()),
        'plane_buckets':[len(edges_a),len(edges_b)],'identical_plane_boundaries':edges_a==edges_b,
        'distinct_plane_keys':len(set(edges_a)^set(edges_b)),
        'differing_common_plane_boundaries':sum(edges_a[k]!=edges_b[k] for k in set(edges_a)&set(edges_b)),
        'model_installed':False,'status':'Source inspection only; reflected native model conversion remains pending'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    print(json.dumps(inspect((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()),indent=2))


if __name__=='__main__':main()
