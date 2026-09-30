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
from v3_asset_loader import ROOT,MODULE,BLOB

VROM,RAM=0x03400000,0x80C00000
PIXELS_RAM,TITLE_RAM=0x807D9000,0x807E9000
# Whole source artwork, divided only at the atlas/padded-glyph boundary and
# between complete padded glyphs. Each live page has separate 16-byte guards.
PIXEL_PAGES=((0x80458010,24864),(0x806A90D0,27648),(0x807ED840,9216))
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


def retained_ram(report,font):
    """Exclude the font itself and one authenticated alias, not real owners."""
    import copy
    from v3_console_disk_install import reservations
    retained=copy.deepcopy(report)
    e=retained['equipment_resources']
    e['passwords'].pop('nook')
    state=e.get('private_save_bank',{}).get('retained_state',{})
    if 'title_buffer' in state:
        if state['title_buffer']!=font['title_buffer']:
            raise ValueError('Changed retained title-buffer alias')
        state.pop('title_buffer')
    yield from reservations(retained)
    # These native/static owners do not all have reservation-shaped receipts.
    yield 0x80000000,0x80458000
    from v3_asset_loader import BLOB_RAM
    yield BLOB_RAM,0x80500000


def check_pixel_layout(report,font):
    pages=font.get('pixel_pages')
    if pages is None:
        ranges=[(font['pixels_ram'],font['pixels_end'])]
    else:
        expected=[dict(ram=a,bytes=n,front_guard=a-16,end_guard=a+n,
            guard_value=0xAF4E4647,source_offset=sum(k for _,k in PIXEL_PAGES[:i]))
            for i,(a,n) in enumerate(PIXEL_PAGES)]
        if (pages!=expected or font['pixels_ram']!=PIXEL_PAGES[0][0] or
                font['pixels_end']!=PIXEL_PAGES[0][0]+PIXEL_PAGES[0][1] or
                sum(r['bytes'] for r in pages)!=font['physical_resource']['bytes']):
            raise ValueError('Changed complete source-ordered font page layout')
        ranges=[(p['front_guard'],p['end_guard']+16) for p in pages]
    title=font['title_buffer'];ranges.append((title['ram'],title['end']))
    for i,(first,last) in enumerate(ranges):
        if not 0x80458000<=first<last<=0x80800000 or any(
                a<last and first<b for a,b in ranges[:i]):
            raise ValueError('Invalid or overlapping font/title pages')
        for a,b in retained_ram(report,font):
            if first<b and a<last:
                raise ValueError('Password acquisition font/title overlaps a retained RAM owner')


def repair(base,prior,blob,core,module,output):
    """Rebuild only the complete font extension around retained artwork/code."""
    del blob,core
    import copy
    from v3_furniture_install import relocate_resource_plan
    from apply_translation import write_new
    equipment=copy.deepcopy(prior['equipment_resources'])
    nook=equipment['passwords']['nook'];old=nook['font']
    if old.get('pixel_pages') or not nook.get('installed'):
        raise ValueError('Font repair needs the complete contiguous predecessor')
    # Bind the current memory owners before running a compiler or writing ROM.
    planned=copy.deepcopy(old)
    planned.update(pixels_ram=PIXEL_PAGES[0][0],pixels_end=PIXEL_PAGES[0][0]+PIXEL_PAGES[0][1],
        pixel_pages=[dict(ram=a,bytes=n,front_guard=a-16,end_guard=a+n,
            guard_value=0xAF4E4647,source_offset=sum(k for _,k in PIXEL_PAGES[:i]))
            for i,(a,n) in enumerate(PIXEL_PAGES)])
    check_pixel_layout(prior,planned)
    joined,font=prepare(base,None,output/'font',physical_resources=prior['physical_resources'],
        card_message=old['code_string_message'],dialogue_fault=old['imports']['af_np_dialogue_fault'],current=old)
    bind_module(module,joined,font)
    check_pixel_layout(prior,font)
    if font['physical_resource']!=old['physical_resource'] or font['glyphs']!=old['glyphs']:
        raise ValueError('Font repair changes retained complete source artwork')
    # The loader's complete blob, including relocation, must leave both guards.
    if len(joined)>0x7FE0:
        raise ValueError('Repaired complete font exceeds guarded loader reservation')
    files=by_vrom(base)
    _,growth=relocate_resource_plan(base,files,VROM,joined,minimum_physical=0x100000,
        reservations=prior['physical_resources'],append_only=False,
        excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+files[BLOB].size),))
    font['repair']=dict(previous_blob_sha256=old['blob_sha256'],
        previous_pixels_ram=old['pixels_ram'],previous_pixels_end=old['pixels_end'],
        artwork_retained=True,complete_packet_crc_checked=True,source_order_retained=True,
        saved_format_changed=False,saved_profile_changed=False)
    nook['font']=font
    nook['additional_font_owner_bytes']+=len(joined)-len(files[VROM].extract(base))
    write_new(output/'font/installed.json',(json.dumps(font,ensure_ascii=False,indent=2)+'\n').encode())
    return equipment,{VROM:joined},dict(resource_growth=[growth]),[]


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


def prepare(image,source,out,*,physical_resources,card_message=None,dialogue_fault=None,reuse=None,current=None):
    files=by_vrom(image);blob=files[VROM].extract(image)
    old,rel=blob[:PREFIX],blob[PREFIX:]
    if current is not None:
        if (sha256(blob)!=current['blob_sha256'] or
                sha256(blob[:current['bytes']])!=current['sha256'] or
                sha256(blob[current['bytes']:])!=current['relocation_sha256']):
            raise ValueError('Changed complete installed Nook font before repair')
        old=bytearray(old)
        entries=rows(blob[current['bytes']:],current['bytes'])
        patches=current['patches']
        if {p['at']:p['name'] for p in patches}!={0:'af_np_font_install',**ENTRIES}:
            raise ValueError('Incomplete installed Nook font prefix bindings')
        for p in patches:
            at=p['at']
            if old[at:at+8]!=bytes.fromhex(p['after']):
                raise ValueError('Changed retained Nook font entry')
            old[at:at+8]=bytes.fromhex(p['before'])
            for place in tuple(entries):
                if at<=place<at+8:del entries[place]
        entries={a:k for a,k in entries.items() if a<PREFIX}
        entries.update({0:4,444:5,448:6,892:5,896:6,1052:5,1056:6})
        old=bytes(old);rel=packed_rows(entries,PREFIX)
    if (sha256(old),sha256(rel))!=(IMAGE_SHA,REL_SHA):
        raise ValueError('Changed complete current font owner')
    module=files[MODULE].extract(image);config=struct.unpack_from('>8I',module,0x68)
    expected=(VROM,len(blob),PREFIX,len(rel),PREFIX,0,zlib.crc32(blob),0x41464701)
    if current is not None:expected=tuple(current['configuration'])
    if config!=expected:
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
    if current is not None:
        physical=dict(current['physical_resource'])
        pixels=image[physical['physical']:physical['physical']+physical['bytes']]
        glyphs=current['glyphs']
        if (len(pixels)!=61728 or sha256(pixels)!=physical['sha256'] or
                len(glyphs)!=256 or {r['code'] for r in glyphs}!=set(range(256)) or
                any(r['source_font_sha256']!=FONT_SHA256 for r in glyphs) or
                not any(all(r.get(k)==physical[k] for k in ('id','physical','bytes','sha256'))
                    for r in physical_resources)):
            raise ValueError('Changed complete installed Nook glyph artwork')
    elif reuse is None:pixels,glyphs=assets(source)
    else:
        retained=json.loads((reuse/'profile.json').read_bytes())
        pixels=(reuse/'pixels.bin').read_bytes();glyphs=retained['glyphs']
        if (len(pixels)!=61728 or sha256(pixels)!=retained['physical_resource']['sha256'] or
                len(glyphs)!=256 or {r['code'] for r in glyphs}!=set(range(256)) or
                any(r['source_font_sha256']!=FONT_SHA256 for r in glyphs)):
            raise ValueError('Changed complete retained Nook glyph packet')
    from v3_physical_resources import allocate
    if current is None:physical=allocate(image,physical_resources,pixels,'nook-name-font',best_fit=True)
    pixels_ram=PIXELS_RAM if current is None else PIXEL_PAGES[0][0]
    if pixels_ram+len(pixels)>TITLE_RAM or TITLE_RAM+0x4830>0x80800000:
        raise ValueError('Nook glyph/title buffers exceed their Expansion Pak reservations')
    generated=(f'#define AF_NP_PIXELS_BYTES {len(pixels)}u\n'
        f'#define AF_NP_PIXELS_RAM 0x{pixels_ram:X}u\n'
        f'#define AF_NP_TITLE_RAM 0x{TITLE_RAM:X}u\n#define AF_NP_TITLE_BYTES 0x4830u\n'
        f'#define AF_NP_PIXELS_ROM 0x{physical["physical"]|0x80000000:X}u\n'
        f'#define AF_NP_PIXELS_CRC 0x{zlib.crc32(pixels):X}u\n')
    if current is not None:
        generated+='#define AF_NP_SPLIT_PIXELS 1\n'
        for i,(address,n) in enumerate(PIXEL_PAGES):
            generated+=f'#define AF_NP_PAGE_{i}_RAM 0x{address:X}u\n#define AF_NP_PAGE_{i}_BYTES {n}u\n'
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
    if current is not None:
        report['pixel_pages']=[dict(ram=a,bytes=n,front_guard=a-16,end_guard=a+n,
            guard_value=0xAF4E4647,source_offset=sum(k for _,k in PIXEL_PAGES[:i]))
            for i,(a,n) in enumerate(PIXEL_PAGES)]
        report['pixels_end']=pixels_ram+PIXEL_PAGES[0][1]
        report['previous_loader_word']=struct.unpack_from('>I',module,0x1924)[0]
    (out/'font.bin').write_bytes(data);(out/'relocation.bin').write_bytes(relocation)
    (out/'profile.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    (out/'extension.asm').write_text(run('objdump','-d','extension.elf'))
    return joined,report


def bind_module(module,joined,report):
    if struct.unpack_from('>8I',module,0x68)!=tuple(report['previous_configuration']):
        raise ValueError('Changed complete font configuration before binding')
    # Retain the system allocator's real lower/upper checks and all other
    # loader instructions; only the checked image-size ceiling changes.
    before=report.get('previous_loader_word',0x2C427000)
    if before not in (0x2C427000,0x2C427FF1) or struct.unpack_from('>I',module,0x1924)[0]!=before:
        raise ValueError('Changed current font-loader image ceiling')
    # SLTIU sign-extends its immediate: 0x8000 would compare against
    # 0xFFFF8000, not 32 KiB. The positive 0x7FF1 ceiling admits aligned
    # images through 0x7FF0 while retaining the real bounded comparison.
    struct.pack_into('>I',module,0x1924,0x2C427FF1)
    config=(VROM,len(joined),report['bytes'],report['relocation_bytes'],
        report['bytes'],0,zlib.crc32(joined),0x41464701)
    struct.pack_into('>8I',module,0x68,*config)
    report.update(configuration=list(config),loader_bound=dict(offset=0x1924,
        before=f'{before:08x}',after='2c427ff1'),image_limit=0x7FF0)
