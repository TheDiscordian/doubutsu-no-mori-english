"""Compile a bounded GC-style stall with one shared mesh and a reflected placement."""
import argparse
import json
from pathlib import Path
import struct

from aflib import sha256,by_vrom,u32,verified_rom
from artwork_chain import rebuild
from fortune_booth_artwork import convert_palette
from map_artwork import compile_commands
from stall_model_source import source,inspect,ROOT,VERTICES,TEXTURES
from title_assets import DATA_BASE,untile,pack4
from nookington_sign import OBJECT,NEW_OBJECT,TABLE,SLOT_SIZE
from nookington_details import READERS,verify_readers as verify_nookington
from texture_preview import native_range,decode,png_rgba

PALETTE_OFFSETS={0x5B8F60:0x92A98,0x5B8F80:0x92AB8,0x5B8FA0:0x92AD8}
TEXTURE_OFFSETS={0x5B9CC0:0x92B38,0x5B8FC0:0x93380,0x5B93C0:0x93780,0x5B9BC0:0x93F80}
MATRIX,VERTEX_DATA,MODEL=0x92AF8,0x94080,0x94EA0
LEFT,RIGHT=0x93348,0x95440
START,END=0x92A98,0x95478
BASE_SHA='3d0cc3c0db2b6a200adaecbb07733ea3a2537ed0223947192fc6a9cb677a2c99'
SLICE_SHA='608bf509e44565573def8b38d3cc79eff8ccca42a9711da5093ed1f464fd7900'
ACTORS={0x937120:'e5687d71cf30895cfc7166391a1ffb99756de9a7ae3211b07a9633108aaa6395',
        0x937820:'70f07bcfc2b227a4b44be2cd2c10266ff4f6f19df62719f31b50994ef5c6f671'}
COMMAND_HASHES={'model':'f461e67de06b222b6b679b660d0be37a2502dd5e171d2c246b61e6889c1411ed',
                'left':'5ebe6e722d6448cbd25961802b4e353172cb82cc5c4e6e822746a960f6fe679f',
                'right':'8ad84792087d9ded1b4ff229412a8c155dde9d42f1bd18ca7db14e3826af7d39'}


def command_source(rel,symbols):
    models,pointers=source(rel,symbols);model=models[0]
    lines=[];command_count=0
    def emit(value,count=1):
        nonlocal command_count
        lines.append('    '+value+',');command_count+=count
    emit('gsDPPipeSync()')
    emit('gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON)')
    emit('gsDPSetCombineLERP(TEXEL0, 0, SHADE, 0, 0, 0, 0, TEXEL0, PRIMITIVE, 0, COMBINED, 0, 0, 0, 0, COMBINED)')
    emit('gsDPSetRenderMode(G_RM_FOG_SHADE_A, G_RM_AA_ZB_TEX_EDGE2)')
    emit('gsDPSetTextureLUT(G_TT_RGBA16)')
    emit('gsDPSetPrimColor(0, 128, 255, 255, 255, 255)')
    expected={0xD7:(0xD7000002,0),0xFC:(0xFC127E60,0xFFFFF3F8),
              0xE2:(0xE200001C,0xC8113078),0xFA:(0xFA000080,0xFFFFFFFF)}
    for i,row in enumerate(model):
        op=row['opcode'];a,b=row['words']
        if op in expected:
            if (a,b)!=expected[op]:raise ValueError('Changed GC stall common rendering state')
        elif op==0xF0:
            emit('gsDPPipeSync()')
            emit(f"gsDPLoadTLUT_pal16(15, 0x{0x6000000+PALETTE_OFFSETS[row['target']]:08X})",6)
        elif op==0xFD:
            if i+1>=len(model) or model[i+1]['opcode']!=0xD2:raise ValueError('Missing GC stall wrap mode')
            mode=model[i+1]['words']
            expected_mode=(0xD2F0F500,0) if row['target']==0x5B9BC0 else (0xD2F0FA00,0)
            if mode!=expected_mode:raise ValueError(f'Unsupported GC stall wrap mode: {mode}')
            wrap='G_TX_WRAP' if row['target']==0x5B9BC0 else 'G_TX_MIRROR'
            w,h=row['width'],row['height']
            emit(f"gsDPLoadTextureBlock_4b(0x{0x6000000+TEXTURE_OFFSETS[row['target']]:08X}, G_IM_FMT_CI, {w}, {h}, 15, {wrap}, {wrap}, {w.bit_length()-1}, {h.bit_length()-1}, 0, 0)",7)
        elif op==0xD2:pass
        elif op==0xD9:
            emit('gsSPSetGeometryMode(G_LIGHTING)' if b&0x20000 else 'gsSPClearGeometryMode(G_LIGHTING)')
        elif op==0x01:
            emit(f"gsSPVertex(0x{0x6000000+VERTEX_DATA+row['start']*16:08X}, {row['count']}, 0)")
        elif op==0x0A:
            ts=row['triangles']
            for j in range(0,len(ts),2):
                if j+1<len(ts):emit('gsSP2Triangles('+', '.join(map(str,(*ts[j],0,*ts[j+1],0)))+')')
                else:emit('gsSP1Triangle('+', '.join(map(str,(*ts[j],0)))+')')
        elif op==0xDF:emit('gsSPEndDisplayList()')
        else:raise ValueError('Unconverted GC stall command')
    if command_count*8>RIGHT-MODEL:raise ValueError('Shared stall model exceeds its native slot')
    flags='G_ZBUFFER | G_SHADE | G_FOG | G_SHADING_SMOOTH'
    entries={
        'left':[f'gsSPLoadGeometryMode({flags} | G_CULL_BACK)',f'gsSPDisplayList(0x{0x6000000+MODEL:08X})',
                'gsSPEndDisplayList()']+['gsSPNoOp()']*4,
        'right':[f'gsSPMatrix(0x{0x6000000+MATRIX:08X}, G_MTX_MODELVIEW | G_MTX_MUL | G_MTX_PUSH)',
                 f'gsSPLoadGeometryMode({flags} | G_CULL_FRONT)',f'gsSPDisplayList(0x{0x6000000+MODEL:08X})',
                 'gsSPPopMatrix(G_MTX_MODELVIEW)','gsSPGeometryMode(G_CULL_FRONT, G_CULL_BACK)',
                 'gsSPEndDisplayList()','gsSPNoOp()']}
    output=['/* Generated from the locally supplied source; do not distribute extracted assets. */','#include <PR/mbi.h>']
    for name,values in entries.items():
        output.append(f'const Gfx stall_{name}[] __attribute__((section(".{name}"), aligned(8))) = {{')
        output.extend('    '+v+',' for v in values);output.append('};')
    output.append('const Gfx stall_model[] __attribute__((section(".model"), aligned(8))) = {')
    output.extend(lines);output.append('};')
    return '\n'.join(output)+'\n',command_count*8


def compile_model(rel,symbols,out):
    code,size=command_source(rel,symbols)
    out.mkdir(parents=True,exist_ok=False);source_file=out/'commands.c'
    with source_file.open('x') as target:target.write(code)
    compiled=compile_commands(out/'gbi',source_file,(('left',56),('right',56),('model',size)))
    return compiled,{'command_source_sha256':sha256(code.encode()),'model_bytes':size,
        'model_space_bytes':RIGHT-MODEL,'model_sha256':sha256(compiled['model']),
        'left_sha256':sha256(compiled['left']),'right_sha256':sha256(compiled['right'])}


def assets(native,rel,symbols,compiled):
    verified_rom(native);files=by_vrom(native);obj=files[OBJECT].extract(native)
    if sha256(obj[START:END])!=SLICE_SHA:raise ValueError('Changed original stall slice')
    for v,digest in ACTORS.items():
        if sha256(files[v].extract(native))!=digest:raise ValueError('Changed original stall actor')
    if files[0x937120].extract(native)[0x6BC:0x6C4]!=struct.pack('>II',0x06093348,0x06095440):
        raise ValueError('Changed native two-placement model table')
    code,size=command_source(rel,symbols)
    if (size!=1392 or set(compiled)!=set(COMMAND_HASHES)
            or any(sha256(compiled[name])!=digest for name,digest in COMMAND_HASHES.items())):
        raise ValueError('Changed independently compiled bounded stall commands')
    changes={LEFT:compiled['left'],RIGHT:compiled['right'],MODEL:compiled['model']}
    matrix=[0]*16
    for i,value in ((0,-1),(5,1),(10,1),(15,1)):matrix[i]=value
    changes[MATRIX]=struct.pack('>16h16H',*matrix,*([0]*16))
    for at,dest in PALETTE_OFFSETS.items():changes[dest]=convert_palette(rel[DATA_BASE+at:DATA_BASE+at+32])
    for at,dest in TEXTURE_OFFSETS.items():
        w,h=TEXTURES[at];changes[dest]=pack4(untile(rel[DATA_BASE+at:DATA_BASE+at+w*h//2],w,h,4))
    vertices=bytearray()
    for i in range(226):
        vertex=rel[DATA_BASE+VERTICES[0]+i*16:DATA_BASE+VERTICES[0]+(i+1)*16]
        if vertex[6:8]!=b'\0\1':raise ValueError('Changed GC stall vertex format')
        vertices.extend(vertex[:6]+b'\0\0'+vertex[8:])
    changes[VERTEX_DATA]=bytes(vertices)
    spans=sorted((at,at+len(data)) for at,data in changes.items())
    if (any(not START<=at<end<=END for at,end in spans)
            or any(a[1]>b[0] for a,b in zip(spans,spans[1:]))):raise ValueError('Stall assets overlap or exceed the native slice')
    profile={'version':1,'source_comparison':inspect(rel,symbols),'source_slice_sha256':SLICE_SHA,
        'source_command_sha256':sha256(code.encode()),'native_command_sha256':COMMAND_HASHES,
        'changes':[{'object_offset':f'{at:06X}','bytes':len(data),'sha256':sha256(data)} for at,data in sorted(changes.items())],
        'triangles_per_placement':133,'stored_vertices':226,'model_bytes':size,'model_spare_bytes':RIGHT-MODEL-size,
        'max_texture_tmem_bytes':2048,'max_extra_matrix_stack_depth':1,'right_placement':'X-reflected GC left-hand model',
        'source_right_mesh_exact':False,'visible_palette_colours_exact':True,'actor_changed':False,
        'shared_palette_changed':False,'allocation_changed':False,'saved_formats_changed':False,'goods_logic_changed':False,
        'status':'GC-style shared stall and reflected placement installed; ordinary appearance/event acceptance pending',
        'source_label_transcription_complete':False}
    return changes,profile


def verify_installed(native,built,changes=None):
    original=by_vrom(native)[OBJECT].extract(native)
    if sha256(original[START:END])!=SLICE_SHA:raise ValueError('Changed original stall slice')
    files=by_vrom(built)
    for v,digest in {**READERS,**ACTORS}.items():
        if sha256(files[v].extract(built))!=digest:raise ValueError('Changed stall actor or structure reader')
    table=files[TABLE].extract(built);pal=files[0xD5D000].extract(built)
    for i,(starts,ends) in enumerate(((8,0xC0),(0x178,0x230))):
        if ((u32(table,starts+0x1D*4),u32(table,ends+0x1D*4))!=(0x6000000+START-8,0x6000000+END)
                or u32(pal,8+(0x46+i*91)*4)!=0x6001088):raise ValueError('Changed seasonal stall ownership')
    if native_range(built,0xD5C088,32)!=native_range(native,0xD5C088,32):raise ValueError('Changed shared stall palette')
    obj,expanded=files[OBJECT].extract(built),files[NEW_OBJECT].extract(built)
    if len(obj)!=0x95480 or len(expanded)!=0x9AD80 or expanded[:len(obj)]!=obj:
        raise ValueError('Changed stall retained/streamed object size')
    expected=bytearray(original[START:END])
    for at,data in (changes or {}).items():expected[at-START:at-START+len(data)]=data
    if obj[START:END]!=expected or expanded[START:END]!=expected:raise ValueError('Incomplete or unreviewed stall model installation')


def build(native,base,report,rel,symbols,compiled):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Stall artwork requires the complete countdown predecessor')
    verify_installed(native,base);changes,profile=assets(native,rel,symbols,compiled)
    files=by_vrom(base);obj=bytearray(files[OBJECT].extract(base));old=files[NEW_OBJECT].extract(base);expanded=bytearray(old)
    for at,data in changes.items():obj[at:at+len(data)]=data;expanded[at:at+len(data)]=data
    table=files[TABLE].extract(base);checked=0
    for starts,ends in ((8,0xC0),(0x178,0x230)):
        for kind in range(46):
            start,end=u32(table,starts+kind*4),u32(table,ends+kind*4)
            at,size=start-0x6000000+8,(end-start-8+15)&~15
            if not 0<=at<=len(expanded)-size or not 0<size<=SLOT_SIZE:raise ValueError('Stall exceeds a native building slot')
            if kind!=0x1D and old[at:at+size]!=expanded[at:at+size]:raise ValueError('Stall changes another structure')
            checked+=1
    image,patch,result=rebuild(native,base,report,{OBJECT:bytes(obj),NEW_OBJECT:bytes(expanded)})
    profile['building_ranges_checked']=checked;result['stall_artwork']=profile
    result['nookington_sign']['object_sha256']=sha256(expanded)
    result['nookington_details'].update(object_sha256=sha256(obj),streamed_object_sha256=sha256(expanded))
    result['release_status']='GC-style stall and all prior English artwork/text; ordinary placement/event acceptance pending'
    verify_installed(native,image,changes);verify_nookington(image,native)
    return image,patch,result


def verify_current(native,built,report):
    installed=report.get('stall_artwork')
    if not installed:return
    compiled={name:native_range(built,NEW_OBJECT+at,size) for name,at,size in
              (('left',LEFT,56),('right',RIGHT,56),('model',MODEL,1392))}
    changes,profile=assets(native,(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(),compiled)
    profile['building_ranges_checked']=92
    if profile!=installed:raise ValueError('Changed installed stall artwork profile')
    verify_installed(native,built,changes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compile-only',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'build/stall-artwork-01');args=parser.parse_args()
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    compiled,profile=compile_model(rel,symbols,args.output/'commands')
    if args.compile_only:
        print(json.dumps({'commands':profile,'source_comparison':inspect(rel,symbols),'cartridge_built':False},indent=2));return
    native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();base=ROOT/'build/countdown-artwork-01'
    image,patch,report=build(native,(base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),rel,symbols,compiled)
    outputs={'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,'build.json':(json.dumps(report,indent=2)+'\n').encode()}
    for at,pal in ((0x5B9CC0,0x5B8FA0),(0x5B8FC0,0x5B8F60),(0x5B93C0,0x5B8F80),(0x5B9BC0,0x5B8F60)):
        w,h=TEXTURES[at]
        outputs[f'{at:08X}.png']=png_rgba(w,h,decode(native_range(image,NEW_OBJECT+TEXTURE_OFFSETS[at],w*h//2),w,h,'ci4',
            native_range(image,NEW_OBJECT+PALETTE_OFFSETS[pal],32)),4)
    for name,data in outputs.items():
        with (args.output/name).open('xb') as target:target.write(data)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch),'commands':profile},indent=2))


if __name__=='__main__':main()
