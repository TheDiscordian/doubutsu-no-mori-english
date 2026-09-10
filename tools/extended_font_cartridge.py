"""Source-bound persistent glyph image and native overlay relocation format."""

from pathlib import Path
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256
from extended_glyphs import validate_resource
from runtime_layout import MODULE_RAM,MODULE_VROM,RESERVATION,LINKED_LIMIT

ROOT = Path(__file__).resolve().parents[1]
RAM, VROM, CONFIG_OFFSET, ABI = 0x80C00000,0x03400000,0x68,0x41464701
RESOURCE_HASH = '30dddc658038fea1a4abc359121e1e4fa110edac5f5757ad6001703eff8aae7e'
MAIL_RESOURCE_HASH = '12a90673f21a6c0bfa3fc05039279b1efc65d96319460ae36993eafa0822c105'
ACCENT_RESOURCE_HASH = '24ae623d2917a2370ec70504daf372be327c830d24fb37bacc68ad84f0bbe90e'


def source_hashes(world_names=False, accents=False, mail_literals=False):
    names = ['overlays/extended_font/'+name for name in ('font.c','font.h','native.c','texture.s')]
    names += ['overlays/extended_font_cartridge/'+name for name in ('entry.s','install.c','font.ld')]
    if world_names:
        names.remove('overlays/extended_font_cartridge/entry.s')
        names += ['overlays/world_names/'+name for name in ('entry.s','install.c','names.c','names.h')]
    if accents:
        names.remove('overlays/extended_font/font.c')
        names.append('overlays/accent_font/font.c')
    if mail_literals:
        names.remove('overlays/world_names/entry.s')
        names += ['overlays/accent_mail/'+name for name in
                  ('entry.s','install.c','accent_mail.h','format.c','catalog.c','generate.c','literal.c','view.c')]
        names += ['runtime/mail/'+name for name in ('catalog.h','format.h','record.h','glyph.h','view.h')]
        names += ['runtime/crc32.h','overlays/mail_generation/generate.h']
    return {name:sha256((ROOT/name).read_bytes()) for name in names}


def relocate(data,relocations,base,*,mail_literals=False):
    if (not 0<len(data)<=0x3000 or len(data)&15 or not 32<=len(relocations)<=0x1000
            or len(relocations)&15 or type(base) is not int or base&15
            or not MODULE_RAM+RESERVATION<=base<=0x80400000-len(data)):
        raise ValueError('Invalid persistent font image/relocation allocation')
    text,writable,rodata,bss,count = struct.unpack_from('>5I',relocations)
    if (not text or any(n&15 for n in (text,writable,rodata,bss))
            or text+writable+rodata+bss!=len(data) or any(data[text+writable+rodata:])
            or count>(len(relocations)-24)//4 or any(relocations[20+count*4:-4])
            or struct.unpack_from('>I',relocations,len(relocations)-4)[0]!=len(relocations)):
        raise ValueError('Invalid persistent font sections or relocation padding')
    sections = {1:(0,text),2:(text,writable),3:(text+writable,rodata)}
    out,high,jumps = bytearray(data),{},set()
    previous = -1
    for entry in struct.unpack_from('>'+str(count)+'I',relocations,20):
        section,kind,offset = entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in sections: raise ValueError('Unknown font relocation section')
        start,size = sections[section];at=start+offset
        if offset&3 or not previous<at or offset+4>size: raise ValueError('Invalid font relocation order/bounds')
        previous=at;word=struct.unpack_from('>I',data,at)[0]
        if kind==2:
            if not RAM<=word<RAM+len(data): raise ValueError('Font data pointer escapes image')
            word+=base-RAM
        elif kind==4:
            target=0x80000000|((word&0x3FFFFFF)<<2)
            if section!=1 or word>>26 not in (2,3) or not RAM<=target<RAM+text:
                raise ValueError('Invalid font jump relocation')
            word=(word&0xFC000000)|(((base+target-RAM)&0xFFFFFFF)>>2);jumps.add(at)
        elif kind==5:
            register=(word>>16)&31
            if section!=1 or word>>26!=15 or register in high: raise ValueError('Invalid font high relocation')
            high[register]=at,word
            continue
        elif kind==6:
            register=(word>>21)&31
            if section!=1 or word>>26 not in (9,35,43,49,57) or register not in high:
                raise ValueError('Invalid font low relocation')
            high_at,high_word=high.pop(register)
            target=((high_word&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            if not RAM<=target<RAM+len(data): raise ValueError('Font paired pointer escapes image')
            target+=base-RAM
            struct.pack_into('>I',out,high_at,(high_word&0xFFFF0000)|(((target+32768)>>16)&65535))
            word=(word&0xFFFF0000)|(target&65535)
        else: raise ValueError('Unsupported font relocation')
        struct.pack_into('>I',out,at,word)
    if high: raise ValueError('Unpaired font high relocation')
    seen=set()
    for at in range(0,text,4):
        word=struct.unpack_from('>I',data,at)[0]
        if word>>26 not in (2,3): continue
        target=0x80000000|((word&0x3FFFFFF)<<2)
        if RAM<=target<RAM+text: seen.add(at)
        elif target not in ({0x800906B4,0x80195938,0x80198DD4,0x80198FDC} if mail_literals else {0x800906B4}):
            raise ValueError('Unapproved external font jump')
    if seen!=jumps: raise ValueError('Missing complete font jump inventory')
    return bytes(out)


def validate(data,relocations,report):
    if report.get('unapproved_candidate'):
        raise ValueError('Unapproved font measurement is not an installable profile')
    mail = report.get('mail_glyphs',False)
    world = report.get('world_names',False)
    accents = report.get('accent_glyphs',False)
    literals = report.get('mail_literals',False)
    if (type(mail) is not bool or type(world) is not bool or type(accents) is not bool
            or type(literals) is not bool or (literals and not accents)
            or (world and not mail) or (accents and not world)):
        raise ValueError('Invalid persistent font glyph capability')
    resource_hash = ACCENT_RESOURCE_HASH if accents else MAIL_RESOURCE_HASH if mail else RESOURCE_HASH
    if (report.get('ram')!=RAM or report.get('bytes')!=len(data)
            or report.get('relocation_bytes')!=len(relocations)
            or report.get('sha256')!=sha256(data) or report.get('relocation_sha256')!=sha256(relocations)
            or report.get('sources')!=source_hashes(world,accents,literals) or report.get('resource_sha256')!=resource_hash):
        raise ValueError('Stale or altered persistent font build')
    relocate(data,relocations,0x801A0010,mail_literals=literals)
    symbols=report['symbols'];text=struct.unpack_from('>I',relocations)[0]
    if symbols.get('af_font_entry')!=0 or any(type(value) is not int or value&3
            or not 0<=value<len(data) for value in symbols.values()):
        raise ValueError('Invalid persistent font symbols')
    for name in ('af_font_install','af_glyph_draw_char','af_glyph_code_width','af_glyph_texture',
                 'af_glyph_load_texture','af_glyph_skip_tag','native_width'):
        if not 0<=symbols.get(name,len(data))<text: raise ValueError('Missing persistent font entry')
    at=symbols.get('af_font_resource',len(data))
    resource=data[at:at+1600]
    if at&15 or at<text or sha256(validate_resource(resource,mail=mail,accents=accents))!=resource_hash:
        raise ValueError('Changed persistent font pixels or mapping')
    state=struct.unpack_from('>3I',relocations)
    for name in ('glyph_resource','active_glyph'):
        if not sum(state)<=symbols.get(name,0)<len(data): raise ValueError('Font state overlaps immutable instructions')
    if world:
        from world_names import validate_image
        validate_image(data,relocations,report)


def configuration(data,relocations,report):
    validate(data,relocations,report)
    return [VROM,len(data)+len(relocations),len(data),len(relocations),
            struct.unpack_from('>I',relocations)[0],0,zlib.crc32(data+relocations),ABI]


def mail_capability(directory):
    """Bind catalogue-four widths to a complete approved font, not a flag alone."""
    from mail_glyph_codes import WIDTHS
    data,reloc = ((directory/name).read_bytes() for name in ('font.bin','relocation.bin'))
    report = json.loads((directory/'font.json').read_text())
    validate(data,reloc,report)
    if report.get('mail_glyphs') is not True:
        raise ValueError('Complete mail glyphs require the fourteen-cell cartridge font')
    at = report['symbols']['af_font_resource']
    resource = data[at:at+1600]
    if {bytes((0x80,resource[32+i])):resource[48+i] for i in range(14)} != WIDTHS:
        raise ValueError('Mail glyph widths differ from the complete cartridge resource')
    return sha256(data+reloc)


def planned_capability(rom,replacements,additions,module,directory):
    """Validate the real installation on copies before importing dependent text.

    The builder repeats installation on the final cartridge before publication.
    A directory flag or candidate metadata alone cannot grant glyph support.
    """
    from glyph_codes import WIDTHS
    approval=install(rom,dict(replacements),dict(additions),dict(module),directory)
    font=approval['font'];data=(directory/'font.bin').read_bytes()
    at=font['symbols']['af_font_resource'];resource=data[at:at+1600]
    if {bytes((0x80,resource[32+i])):resource[48+i] for i in range(5)} != WIDTHS:
        raise ValueError('Dialogue glyph widths differ from the complete cartridge resource')
    return approval['blob_sha256']


def native_evidence(rom,current):
    original=by_vrom(rom)[CODE_VROM].extract(rom)
    guards={}
    for start,end in ((0x80090178,0x80090188),(0x8009028C,0x8009034C),
                      (0x8009069C,0x80090878),(0x8009113C,0x800918E8),
                      (0x80091C98,0x80091DFC),(0x800A23C4,0x800A23EC)):
        expected=bytearray(original[start-CODE_RAM:end-CODE_RAM])
        if start==0x8009028C: expected[8:12]=bytes(4)
        if current[start-CODE_RAM:end-CODE_RAM]!=expected:
            raise ValueError(f'Changed native English-font consumer at {start:08X}')
        guards[f'{start:08X}']=sha256(expected)
    # System allocator/free, relocation, DMA, and cache maintenance stay native.
    for start,end in ((0x8002BC60,0x8002BCC0),(0x8002B9C0,0x8002BC00),
                      (0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54)):
        at=0x1060+start-0x80025C60
        guards[f'{start:08X}']=sha256(rom[at:at+end-start])
    return guards


def verify_configuration(module_data,blob,module):
    approval=module.get('extended_font')
    if not isinstance(approval,dict) or not isinstance(approval.get('configuration'),list):
        raise ValueError('Persistent font requires its configured build approval')
    expected=approval['configuration']
    if (len(expected)!=8 or any(type(v) is not int or not 0<=v<=0xFFFFFFFF for v in expected)
            or len(blob)!=expected[1] or not 0<expected[2]<len(blob)
            or sha256(blob)!=approval.get('blob_sha256')):
        raise ValueError('Changed approved persistent font blob')
    actual=configuration(blob[:expected[2]],blob[expected[2]:],approval['font'])
    if actual!=expected or module_data[CONFIG_OFFSET:CONFIG_OFFSET+32]!=struct.pack('>8I',*actual):
        raise ValueError('Persistent font configuration differs from its validated image')


def install(rom,replacements,additions,module,directory):
    from runtime_module import BOOTSTRAP_RAM,runtime_source_hashes
    if (not module or module.get('source_sha256')!=sha256(rom) or MODULE_VROM not in additions
            or module.get('runtime_sources')!=runtime_source_hashes(ROOT/'runtime')):
        raise ValueError('Persistent font requires the current complete resident module')
    binary=bytearray(additions[MODULE_VROM]);baseline=bytearray(binary)
    if len(binary)!=RESERVATION or any(binary[CONFIG_OFFSET:CONFIG_OFFSET+32]) or VROM in additions:
        raise ValueError('Changed or duplicate persistent font configuration')
    for offset,vrom in ((56,0x02A00000),(60,0x02C00000),(64,0x02E00000),(68,0x03000000)):
        value=struct.unpack_from('>I',baseline,offset)[0]
        if value and (value!=vrom or vrom not in additions): raise ValueError('Unverified preceding font dependency')
        baseline[offset:offset+4]=bytes(4)
    if any(baseline[0x48:0x68]) or module.get('npc_mail_loader'):
        from npc_mail_loader import VROM as NPC_VROM,verify_configuration as verify_npc
        verify_npc(binary,additions.get(NPC_VROM,b''),module)
        baseline[0x48:0x68]=bytes(32)
    if sha256(baseline)!=module['module_sha256']:
        raise ValueError('Changed persistent font resident code')
    target=int(module['symbols'].get('af_extended_font_init','0'),16)
    if target&3 or not MODULE_RAM+0x300<=target<MODULE_RAM+min(module['linked_bytes'],LINKED_LIMIT):
        raise ValueError('Missing bounded persistent font initializer')
    current=replacements.get(CODE_VROM,by_vrom(rom)[CODE_VROM].extract(rom))
    evidence=native_evidence(rom,current)
    bootstrap=current[BOOTSTRAP_RAM-CODE_RAM:0x800D66D0-CODE_RAM]
    startup=struct.pack('>4I',0x0C00AFDE,0,0x0C000000|((target&0x0FFFFFFF)>>2),0)
    if bootstrap.count(startup)!=1: raise ValueError('Persistent font must load after system-heap initialization')
    report=json.loads((directory/'font.json').read_text())
    data,relocations=(directory/'font.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
    approved=configuration(data,relocations,report);blob=data+relocations
    if report.get('world_names'):
        from world_names import dependencies
        evidence['world_names']=dependencies(rom,current,binary,additions,module)
    files=by_vrom(rom)
    intervals=[(entry.vstart,entry.vend) for entry in files.values()]
    intervals += [(start,start+len(value)) for start,value in additions.items()]
    if any(start<VROM+len(blob) and VROM<end for start,end in intervals):
        raise ValueError('Persistent font overlaps an existing cartridge file')
    first=DMA_START+len(files)*16;end=first+(len(additions)+2)*16
    if end>DMA_END or rom[first:end]!=bytes(end-first): raise ValueError('Persistent font lacks unused DMA capacity')
    struct.pack_into('>8I',binary,CONFIG_OFFSET,*approved)
    approval={'configuration':approved,'blob_sha256':sha256(blob),'font':report,'native_evidence':evidence}
    additions[MODULE_VROM],additions[VROM]=bytes(binary),blob
    module['extended_font']=approval
    return {**approval,'system_allocation_bytes':len(blob)+15,
            'scope':'Startup-owned glyph code/pixels and message reveal; editors and saves remain unchanged'}
