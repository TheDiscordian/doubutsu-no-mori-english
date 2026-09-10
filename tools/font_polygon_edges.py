"""Install transparent filtering borders for V1's proportional polygon glyphs."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,make_ups,sha256,verified_rom
from apply_translation import write_new
from catalogue_names import Image,elf_inventory
from extended_font_cartridge import ACCENT_RESOURCE_HASH
from extended_glyphs import validate_resource
from font import ATLAS_OFFSET,ATLAS_SIZE,FONT_VROM,get_glyph,pack_pixels,pixels
from npc_mail_show import relocate_verified_data
from textcodec import LATIN
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb'
MODULE,VROM,RAM,PREFIX=0x2800000,0x3400000,0x80C00000,12000
MODULE_SHA='e593fe4ea961cf114687a068b33808addf7d15fd75998d27c5a712250197a3fd'
PREFIX_SHA='62b84f16a8d36f2bd65162844f3826e6541f6878a5f02d64583f2a99ac6b0f42'
REL_SHA='3c1304a9b3c064e97a92e24bf589a8db0e19df9f6c95cf151e467fd60f09c3e5'
FONT_SHA='7e4fdb93f1b0109e3d609434163d8c31174ef6699b7d439aef1a8305a18d2798'
POLY_START,POLY_END=0x800911E8,0x800913D4
POLY_SHA='a9c017ac6e6c2c15cf4851e14855350aae39d51ef78fa78eb6668a1244b0cd36'
IMPORTS={'af_previous_install':RAM+11800,'af_glyph_texture':RAM+1052,'af_glyph_texture_code':RAM+1016}

def source_hashes():
    return {p:sha256((ROOT/p).read_bytes()) for p in ('tools/font_polygon_edges.py','overlays/font_edges/draw.c')}

def padded_glyph(glyph):
    if len(glyph)!=16 or any(len(row)!=12 for row in glyph): raise ValueError('Invalid native glyph cell')
    out=[0]*288
    for y,row in enumerate(glyph): out[(y+1)*16+1:(y+1)*16+13]=row
    return pack_pixels(out)

def inputs(base):
    if sha256(base)!=BASE_SHA: raise ValueError('Font-edge correction requires exact V1RC2')
    files=by_vrom(base)
    module=files[MODULE].extract(base);blob=files[VROM].extract(base)
    config=struct.unpack_from('>8I',module,0x68)
    if (sha256(module)!=MODULE_SHA or config!=(VROM,12704,PREFIX,704,PREFIX,0,0x5885271B,0x41464701)
            or len(blob)!=12704 or sha256(blob[:PREFIX])!=PREFIX_SHA or sha256(blob[PREFIX:])!=REL_SHA):
        raise ValueError('Changed persistent font owner or loader configuration')
    original=files[CODE_VROM].extract(base)[POLY_START-CODE_RAM:POLY_END-CODE_RAM]
    if sha256(original)!=POLY_SHA: raise ValueError('Changed native polygon function')
    # A moved copy retains only ordinary instructions and external calls.
    for (word,) in struct.iter_unpack('>I',original):
        op=word>>26
        if op in (1,4,5,6,7,20,21,22,23) or (op==17 and (word>>21)&31==8):
            raise ValueError('Unreviewed relative branch in native polygon copy')
        if op in (2,3) and (0x80000000|((word&0x3FFFFFF)<<2)) not in (0x8009069C,0x80090848):
            raise ValueError('Unreviewed native polygon jump')
    font=files[FONT_VROM].extract(base)
    if sha256(font)!=FONT_SHA: raise ValueError('Changed source glyph atlas')
    atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    extended=blob[8992:8992+1600]
    validate_resource(extended,mail=True,accents=True)
    if sha256(extended)!=ACCENT_RESOURCE_HASH: raise ValueError('Changed extended glyph pixels')
    mapping=bytearray([255]*256);textures=[]
    if len(LATIN)!=81: raise ValueError('Changed proportional glyph inventory')
    for code in sorted(LATIN):
        mapping[code]=len(textures);textures.append(padded_glyph(get_glyph(atlas,code)))
    for slot in range(16): textures.append(padded_glyph(get_glyph(pixels(extended[64:]),slot)))
    return module,blob[:PREFIX],blob[PREFIX:],original,bytes(mapping),b''.join(textures)

def compile_image(base,out):
    module,previous,old_rel,original,mapping,textures=inputs(base)
    out.mkdir(parents=True,exist_ok=False)
    for name,value in (('previous.bin',previous),('original-poly.bin',original),('mapping.bin',mapping),('padded.bin',textures)):
        write_new(out/name,value)
    (out/'parts.s').write_text('''.section .native,"ax",@progbits
.incbin "previous.bin"
.section .text.original_poly,"ax",@progbits
.balign 4
.globl af_original_poly
af_original_poly:
.incbin "original-poly.bin"
.section .rodata.border,"a",@progbits
.balign 16
.globl af_border_map
af_border_map:
.incbin "mapping.bin"
.globl af_border_pixels
af_border_pixels:
.incbin "padded.bin"
''')
    (out/'image.ld').write_text('OUTPUT_ARCH(mips)\n'+''.join(f'{k} = 0x{v:08X};\n' for k,v in IMPORTS.items())+f'''
SECTIONS {{
 . = 0x{RAM:08X};
 .text : {{ KEEP(*(.native)) *(.text .text.*) *(.rodata .rodata.* .data .data.*)
            *(.bss .bss.* COMMON) . = ALIGN(16); }}
 ASSERT(SIZEOF(.text)<=0x7000,"Bordered font exceeds verified allocation limit")
 /DISCARD/ : {{ *(.reginfo .MIPS.abiflags .pdr .comment .gnu.attributes .note.*) }}
}}
''')
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('gcc','-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
        '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror',
        '-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include',
        '/source/overlays/font_edges/draw.c','-o','draw.o')
    run('as','-EB','-mabi=32','-march=vr4300','-o','parts.o','parts.s')
    run('ld','-EB','--emit-relocs','-T','image.ld','-o','image.elf','parts.o','draw.o')
    if run('nm','--undefined-only','image.elf').strip(): raise ValueError('Unresolved bordered-font symbol')
    defined={}
    for line in run('nm','--defined-only','image.elf').splitlines():
        parts=line.split()
        if len(parts)==3: defined[parts[2]]=int(parts[0],16)
    run('objcopy','-O','binary','-j','.text','image.elf','image.bin')
    image=bytearray((out/'image.bin').read_bytes())
    if image[:PREFIX]!=previous or len(image)>0x7000: raise ValueError('Changed retained font prefix')
    sections=struct.unpack_from('>5I',old_rel)
    if sections!=(PREFIX,0,0,0,170): raise ValueError('Changed retained font relocation layout')
    rows=list(struct.unpack_from('>170I',old_rel,20))
    if rows.count(0x44000000)!=1: raise ValueError('Missing original font entry relocation')
    listing=run('readelf','-rW','image.elf');inventory=elf_inventory(listing,RAM)
    for at,kind,target,symbol in inventory:
        if not PREFIX<=at<=len(image)-4 or not RAM<=target<RAM+len(image):
            raise ValueError('Bordered-font relocation escapes its owner')
        rows.append(0x40000000|kind<<24|at)
    if len({r&0xFFFFFF for r in rows})!=len(rows): raise ValueError('Duplicate font relocation')
    struct.pack_into('>I',image,0,0x08000000|(defined['af_border_install']>>2&0x3FFFFFF))
    count=len(rows);size=(24+count*4+15)&~15
    relocation=(struct.pack('>5I',len(image),0,0,0,count)+struct.pack('>'+str(count)+'I',*rows)
                +bytes(size-24-count*4)+struct.pack('>I',size))
    for address in (0x801A0010,0x80378010):
        before=relocate_verified_data(Image(RAM,PREFIX,sections),previous,old_rel,address)
        after=relocate_verified_data(Image(RAM,len(image),struct.unpack_from('>5I',relocation)),image,relocation,address)
        if after[8:PREFIX]!=before[8:]: raise ValueError('Bordered font changes relocated retained prefix')
        if struct.unpack_from('>I',after)[0] != 0x08000000|((address+defined['af_border_install']-RAM)>>2&0x3FFFFFF):
            raise ValueError('New font entry relocation fails')
    image=bytes(image)
    profile={'bytes':len(image),'image_sha256':sha256(image),'relocation_sha256':sha256(relocation),
        'relocation_bytes':len(relocation),'relocation_bases':['801A0010','80378010'],
        'symbols':{k:v-RAM for k,v in defined.items()},'elf_relocations':inventory,
        'stack_usage':(out/'draw.su').read_text(),'padded_glyphs':97,'padded_bytes':len(textures),
        'padded_sha256':sha256(textures),'mapping_sha256':sha256(mapping)}
    (out/'image.bin').write_bytes(image);(out/'relocation.bin').write_bytes(relocation)
    (out/'image.asm').write_text(run('objdump','-d','image.elf'))
    (out/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    return image,relocation,profile

def build(native,base,out):
    verified_rom(native)
    module,previous,old_rel,original,mapping,textures=inputs(base)
    hashes=source_hashes()
    image,reloc,profile=compile_image(base,out/'font')
    blob=image+reloc;changed=bytearray(module)
    if struct.unpack_from('>I',module,0x1964)[0]!=0x2C423000: raise ValueError('Changed font loader bound instruction')
    struct.pack_into('>I',changed,0x1964,0x2C427000)
    config=(VROM,len(blob),len(image),len(reloc),len(image),0,zlib.crc32(blob),0x41464701)
    struct.pack_into('>8I',changed,0x68,*config)
    result=reconstruct(native,base,{MODULE:bytes(changed),VROM:blob},resized=(VROM,))
    patch=make_ups(native,result)
    if apply_ups(native,patch)!=result: raise ValueError('Font-edge UPS reconstruction failed')
    if source_hashes()!=hashes: raise ValueError('Font-edge source changed during build')
    report={'version':1,'baseline_sha256':BASE_SHA,'source_sha256':sha256(native),'output_sha256':sha256(result),
        'patch_sha256':sha256(patch),'sources':hashes,'toolchain':IMAGE,'font':profile,'configuration':list(config),
        'font_blob_sha256':sha256(blob),'module_sha256':sha256(changed),
        'persistent_allocation_bytes':len(blob)+15,'allocation_growth_bytes':len(blob)-len(previous)-len(old_rel),
        'original_atlases_unchanged':True,'speech_renderer_unchanged':True,'advances_unchanged':True,
        'per_glyph_vertex_bytes':64,'per_glyph_display_commands':9,'save_format_changed':False,
        'native_validation':'pending','hardware_retest':'pending','fixed_issues':['V1-17']}
    return result,patch,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'build/v1rc2/Animal Forest English V1RC2.z64')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),args.base.read_bytes(),args.output)
    for name,data in {'animal-forest-font-edges.z64':image,'animal-forest-font-edges.ups':patch,
                      'fixes.json':(json.dumps(report,indent=2)+'\n').encode()}.items(): write_new(args.output/name,data)
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
