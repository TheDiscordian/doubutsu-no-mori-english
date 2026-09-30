"""Extend the complete installed font with source-bound code/card glyphs."""
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

from aflib import by_vrom,sha256
from accent_mail_overlays import rows,packed_rows
from catalogue_names import Image,elf_inventory
from extended_glyphs import FONT_SHA256,source_atlas,ACCENT_GLYPHS
from font import get_glyph,pack_pixels,resize_glyph
from font_polygon_edges import padded_glyph
from gc_text import decoder_tables
from npc_mail_show import relocate_verified_data
from toolchain import IMAGE
from v3_asset_loader import ROOT,MODULE

VROM,RAM=0x03400000,0x80C00000
PIXELS_RAM,TITLE_RAM=0x804DA000,0x804EA000
PREFIX=27744
IMAGE_SHA='66f4bf55eb09ae4d241c275c7d7eaf9ed54b02dc4b65eb226f98682c876e1991'
REL_SHA='4757b124e5687488c35bd8eed5ac8e4e4e1f8acfef66ce3a5f0bd4a4a113cbe9'
ENTRIES={444:'af_np_glyph_index',600:'af_np_glyph_width',892:'af_np_glyph_end',
    936:'af_np_glyph_code_width',1016:'af_np_glyph_texture_code',1052:'af_np_glyph_texture'}
IMPORTS={'glyph_resource':RAM+11316,'active_glyph':RAM+11312,
    'af_np_previous_font_install':RAM+13296,'af_np_previous_poly':RAM+12492}
SOURCES=('tools/v3_nook_font.py','overlays/v3/nook_font.c',
    'overlays/v3/nook_code_string.c','overlays/v3/nook_code_string.h','runtime/commands.c',
    'overlays/classic_letters/append.ld','tools/extended_glyphs.py',
    'tools/font_polygon_edges.py','tools/font.py','runtime/crc32.c','runtime/crc32.h',
    'overlays/v3/resource_dma.h','tools/v3_physical_resources.py')


def assets(source):
    decoder=ROOT/'local/ac-decomp/tools/msg_tool.py'
    table=decoder_tables(decoder)['CHAR_MAP']
    if (table[0xD1],table[0xD4])!=('#','⚷'):
        raise ValueError('Changed donor code/card character identities')
    atlas=source_atlas(source.rel,source.symbols,decoder,mail=True,accents=True)
    pixels=[0]*(192*256);widths=[];padded=[];receipts=[]
    from textcodec import ENCODE
    half_codes={code for _,code,half in ACCENT_GLYPHS if half}|{0xD1}
    for code,name in enumerate(table):
        half=code in half_codes or name in ENCODE
        original=get_glyph(atlas,code)
        glyph,width=resize_glyph(original) if half else (original,12)
        x,y=code%16*12,code//16*16
        for row,line in enumerate(glyph):pixels[(y+row)*192+x:(y+row)*192+x+12]=line
        widths.append(width);padded.append(padded_glyph(glyph))
        receipts.append(dict(character=name,code=code,encoding=f'80{code:02X}',
            width=width,source_font_sha256=FONT_SHA256,
            source_glyph_sha256=sha256(pack_pixels([p for row in original for p in row])),
            native_glyph_sha256=sha256(pack_pixels([p for row in glyph for p in row]))))
    header=struct.pack('>8I',0x41464E46,1,256,192,256,288,24864,61728)
    packet=header+bytes(widths)+pack_pixels(pixels)+b''.join(padded)
    if len(packet)!=61728 or len(packet)&15:raise ValueError('Invalid complete Nook name glyph packet')
    return packet,receipts


def prepare(image,source,out,*,physical_resources,card_message=None,dialogue_fault=None,reuse=None):
    files=by_vrom(image);blob=files[VROM].extract(image)
    old,rel=blob[:PREFIX],blob[PREFIX:]
    if (sha256(old),sha256(rel))!=(IMAGE_SHA,REL_SHA):
        raise ValueError('Changed complete current font owner')
    module=files[MODULE].extract(image);config=struct.unpack_from('>8I',module,0x68)
    if config!=(VROM,len(blob),PREFIX,len(rel),PREFIX,0,zlib.crc32(blob),0x41464701):
        raise ValueError('Font resource does not match its current complete loader configuration')
    hashes={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}
    from aflib import CODE_RAM,CODE_VROM
    core=files[CODE_VROM].extract(image)
    title_start=0x800C8D98-CODE_RAM
    title=core[title_start:title_start+112]
    if (title[0x28:0x30]!=bytes.fromhex('0c026ff0afa60020') or
            title[0x58:0x60]!=bytes.fromhex('0c009b8400402025') or
            files[0xBC8000].size!=0x4830):
        raise ValueError('Changed native title key-data allocation or complete resource')
    title_binding=dict(function=0x800C8D98,bytes=112,sha256=sha256(title),
        resource_vrom=0xBC8000,resource_bytes=0x4830,resource_sha256=sha256(files[0xBC8000].extract(image)),
        callsite=0x800C8DC0,before=0x0C026FF0,ram=TITLE_RAM,end=TITLE_RAM+0x4830)
    imports=dict(IMPORTS)
    if card_message is not None:
        from aflib import CODE_RAM,CODE_VROM
        core=files[CODE_VROM].extract(image)
        if (not isinstance(card_message,int) or not 0<card_message<0x8000 or
                not isinstance(dialogue_fault,int) or not 0x80400000<=dialogue_fault<0x80800000 or
                core[0x800A21C0-CODE_RAM:0x800A21C8-CODE_RAM]!=bytes.fromhex('080655b000000000')):
            raise ValueError('Changed native message dispatcher or missing checked failure provider')
        imports.update(af_np_previous_dispatch=0x801956C0,af_np_dialogue_fault=dialogue_fault)
    out.mkdir(parents=True,exist_ok=False)
    if reuse is None:pixels,glyphs=assets(source)
    else:
        retained=json.loads((reuse/'profile.json').read_bytes())
        pixels=(reuse/'pixels.bin').read_bytes();glyphs=retained['glyphs']
        if (len(pixels)!=61728 or sha256(pixels)!=retained['physical_resource']['sha256'] or
                len(glyphs)!=256 or {r['code'] for r in glyphs}!=set(range(256)) or
                any(r['source_font_sha256']!=FONT_SHA256 for r in glyphs)):
            raise ValueError('Changed complete retained Nook glyph packet')
    from v3_physical_resources import allocate
    physical=allocate(image,physical_resources,pixels,'nook-name-font',best_fit=True)
    pixels_ram=PIXELS_RAM
    if pixels_ram+len(pixels)>0x80500000:raise ValueError('Nook glyphs exceed the owned Expansion Pak gap')
    generated=(f'#define AF_NP_PIXELS_BYTES {len(pixels)}u\n'
        f'#define AF_NP_PIXELS_RAM 0x{pixels_ram:X}u\n'
        f'#define AF_NP_TITLE_RAM 0x{TITLE_RAM:X}u\n#define AF_NP_TITLE_BYTES 0x4830u\n'
        f'#define AF_NP_PIXELS_ROM 0x{physical["physical"]|0x80000000:X}u\n'
        f'#define AF_NP_PIXELS_CRC 0x{zlib.crc32(pixels):X}u\n')
    (out/'nook-font-assets.inc').write_text(generated)
    (out/'pixels.bin').write_bytes(pixels)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        r=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if r.returncode:raise ValueError(r.stdout+r.stderr)
        return r.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
        '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror',
        '-D_LANGUAGE_C','-DF3DEX_GBI_2','-I/source/upstream/af/lib/ultralib/include','-I/out']
    if card_message is not None:flags.append(f'-DAF_NP_CARD_E_MESSAGE={card_message}')
    run('gcc',*flags,'/source/overlays/v3/nook_font.c','-o','extension.o')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/classic_letters/append.ld',
        f'--defsym=__classic_extension_base=0x{RAM+PREFIX:X}',
        *(f'--defsym={k}=0x{v:X}' for k,v in imports.items()),'-o','extension.elf','extension.o')
    if run('nm','--undefined-only','extension.elf').strip():raise ValueError('Unresolved Nook font binding')
    symbols={n:int(a,16) for a,k,n in (r.split() for r in run('nm','--defined-only','extension.elf').splitlines())}
    run('objcopy','-O','binary','extension.elf','extension.bin')
    extra=(out/'extension.bin').read_bytes();end=RAM+PREFIX+len(extra)
    if (symbols['__classic_start']!=RAM+PREFIX or symbols['__classic_end']!=end or
            not extra or len(extra)&15 or PREFIX+len(extra)>0x7FF0):
        raise ValueError('Nook font extension exceeds its owned image')
    entries=rows(rel,PREFIX);listing=run('readelf','-rW','extension.elf')
    inventory=elf_inventory(listing,RAM)
    for at,kind,target,name in inventory:
        if not PREFIX<=at<=PREFIX+len(extra)-4 or at&3:
            raise ValueError('Nook font relocation escapes appended owner')
        if RAM<=target<end:
            if target<RAM+PREFIX and imports.get(name)!=target:
                raise ValueError('Unapproved Nook retained-prefix binding')
            if at in entries:raise ValueError('Duplicate Nook font relocation')
            entries[at]=kind
        elif not (kind==4 and target in (0x8002FE00,0x80034CE0,0x8002BC60,0x8002BC90,0x80026B44,0x80026500,0x8009BFC0) or
                kind in (2,4,5,6) and imports.get(name)==target):
            raise ValueError('Unapproved external Nook font binding')
    data=bytearray(old+extra);patches=[]
    for at,name in {0:'af_np_font_install',**ENTRIES}.items():
        value=struct.pack('>2I',0x08000000|((symbols[name]>>2)&0x3FFFFFF),0)
        patches.append(dict(at=at,name=name,before=old[at:at+8].hex(),after=value.hex()))
        data[at:at+8]=value
        for place in tuple(entries):
            if at<=place<at+8:del entries[place]
        entries[at]=4
    data=bytes(data);relocation=packed_rows(entries,len(data));changed={
        i for p in patches for i in range(p['at'],p['at']+8)}
    for base in (0x801A0010,0x80378010):
        before=relocate_verified_data(Image(RAM,PREFIX,struct.unpack_from('>5I',rel)),old,rel,base)
        after=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',relocation)),data,relocation,base)
        if any(before[i]!=after[i] for i in range(PREFIX) if i not in changed):
            raise ValueError('Nook font extension changes unrelated retained code, pixels, or state')
    if len(relocation)>0x1000 or hashes!={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}:
        raise ValueError('Changed Nook font sources or excessive relocation size')
    joined=data+relocation
    report=dict(format='AFV3-NOOK-FONT-1',ram=RAM,vrom=VROM,bytes=len(data),
        sha256=sha256(data),relocation_bytes=len(relocation),relocation_sha256=sha256(relocation),
        blob_sha256=sha256(joined),previous_bytes=PREFIX,previous_sha256=IMAGE_SHA,
        previous_relocation_sha256=REL_SHA,previous_configuration=list(config),
        glyphs=glyphs,patches=patches,imports=imports,elf_relocations=inventory,
        symbols={n:a-RAM for n,a in symbols.items() if RAM+PREFIX<=a<end},
        source=hashes,flags=flags,toolchain=IMAGE,additional_allocation_bytes=len(joined)-len(blob),
        physical_resource=physical,pixel_allocation_bytes=0,
        pixels_ram=pixels_ram,pixels_end=pixels_ram+len(pixels),additional_resident_bytes=len(pixels),
        title_buffer=title_binding,
        native_execution_tested=False,existing_glyphs_and_letter_readers_retained=True)
    if card_message is not None:report['code_string_message']=card_message
    (out/'font.bin').write_bytes(data);(out/'relocation.bin').write_bytes(relocation)
    (out/'profile.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/'extension.asm').write_text(run('objdump','-d','extension.elf'))
    return joined,report


def bind_module(module,joined,report):
    if struct.unpack_from('>8I',module,0x68)!=tuple(report['previous_configuration']):
        raise ValueError('Changed complete font configuration before binding')
    # Retain the system allocator's real lower/upper checks and all other
    # loader instructions; only the checked image-size ceiling changes.
    if struct.unpack_from('>I',module,0x1924)[0]!=0x2C427000:
        raise ValueError('Changed current font-loader image ceiling')
    # SLTIU sign-extends its immediate: 0x8000 would compare against
    # 0xFFFF8000, not 32 KiB. The positive 0x7FF1 ceiling admits aligned
    # images through 0x7FF0 while retaining the real bounded comparison.
    struct.pack_into('>I',module,0x1924,0x2C427FF1)
    config=(VROM,len(joined),report['bytes'],report['relocation_bytes'],
        report['bytes'],0,zlib.crc32(joined),0x41464701)
    struct.pack_into('>8I',module,0x68,*config)
    report.update(configuration=list(config),loader_bound=dict(offset=0x1924,
        before='2c427000',after='2c427ff1'),image_limit=0x7FF0)
