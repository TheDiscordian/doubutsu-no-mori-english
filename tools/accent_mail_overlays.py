"""Build guarded accent adapters while retaining complete preceding overlay images."""
import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import by_vrom,sha256,verified_rom
from check_keyboard_assembly import IMAGE
from extended_font_cartridge import validate as validate_font
from npc_mail_show import relocate_verified_data
from accent_mail_font import PROFILE as FONT_PROFILE

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='be3636e5a32b7bf628dd7ad9ed492b577b5c55f4d89c14a89dde24f48c074282'
MODULE_SHA='493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6'
FONT_POINTER=0x80199F04
KINDS={'32':2,'26':4,'HI16':5,'LO16':6}
TREASURE=('af_notice_treasure_valid','af_notice_treasure_pack','af_notice_treasure_decode_parts')
RESIDENT={'af_crc32':0x80195938,'af_mail_record_pack':0x80198DD4,
          'af_mail_record_unpack':0x80198FDC,'af_mail_restore':0x80196C28,'af_mail_format':0x80197654}
BASE_IMAGES={
    'creator':('d51d0b94aa3d638f4b675978646f62d3c98fd09aea60f1abcdea2cd335af1ade',
               '95f09d4b0c6ea100caa03cf798ee217836670c4e102ab5538dc2cb7be74b34a1'),
    'notice':('4c90884012ca787e44b20e5052e984c2f1b39e1d9e184da3094d9af283a8f428',
              'd407cdd681b0ae42d48f4b0e29b072b0797519829ef7bc6309d28b8ecdc696ad'),
}


def source_hashes():
    paths=['overlays/accent_mail/'+name for name in ('treasure.c','treasure.ld','literal.c','accent_mail.h')]
    paths+=['runtime/notice/'+name for name in ('treasure.h','record.h','initial.h')]
    paths+=['runtime/mail/'+name for name in ('catalog.h','format.h','record.h','glyph.h','view.h')]
    paths+=['runtime/crc32.h','overlays/mail_generation/generate.h','tools/accent_mail_font.py']
    return {p:sha256((ROOT/p).read_bytes()) for p in paths}


def dispatch(target):
    """Tail-call through the loader's existing owned image; preserve all five arguments."""
    offset=FONT_PROFILE['symbols'][target]
    if not 0<offset<0x8000:raise ValueError('Accent entry exceeds a signed bridge displacement')
    words=(0x3C190000|((FONT_POINTER+0x8000)>>16),0x8F390000|(FONT_POINTER&0xFFFF),
           0x13200004,0,0x27390000|offset,0x03200008,0,0x03E00008,0x00001025,0)
    return struct.pack('>10I',*words)


def rows(reloc,image_size):
    text,data,rodata,bss,count=struct.unpack_from('>5I',reloc)
    if text+data+rodata+bss!=image_size or bss or count>(len(reloc)-24)//4:
        raise ValueError('Accent prefix requires its complete stored original image')
    starts={1:0,2:text,3:text+data};sizes={1:text,2:data,3:rodata}
    result={}
    for entry in struct.unpack_from('>'+str(count)+'I',reloc,20):
        section,kind,offset=entry>>30,(entry>>24)&63,entry&0xFFFFFF
        if section not in starts or offset&3 or offset+4>sizes[section] or kind not in KINDS.values():
            raise ValueError('Invalid original accent-prefix relocation')
        at=starts[section]+offset
        if at in result:raise ValueError('Duplicate original accent-prefix relocation')
        result[at]=kind
    return result


def packed_rows(entries,size):
    values=[0x40000000|(kind<<24)|at for at,kind in sorted(entries.items())]
    length=(24+4*len(values)+15)&~15
    return (struct.pack('>5I',size,0,0,0,len(values))+struct.pack('>'+str(len(values))+'I',*values)
            +bytes(length-24-4*len(values))+struct.pack('>I',length))


@dataclass(frozen=True)
class Overlay:
    ram:int
    resident_bytes:int
    sections:tuple


def compile_treasure(ram,prefix_size,symbols,out):
    imports={**RESIDENT,**{name:ram+symbols[name] for name in
             ('af_notice_treasure_mask','af_notice_record_expand','af_notice_record_pack')}}
    out.mkdir(parents=True,exist_ok=True)
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{out.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                              capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError('Accent overlay '+tool+' failed: '+result.stdout+result.stderr)
        return result.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
           '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
           '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    for name in ('treasure','literal'):
        run('gcc',*flags,f'/source/overlays/accent_mail/{name}.c','-o',name+'.o')
    start=ram+prefix_size
    run('ld','-EB','--emit-relocs','-T','/source/overlays/accent_mail/treasure.ld',
        f'--defsym=__accent_extension_base=0x{start:08X}',
        *(f'--defsym={k}=0x{v:08X}' for k,v in imports.items()),
        '-Map=extension.map','-o','extension.elf','treasure.o','literal.o')
    if run('nm','--undefined-only','extension.elf').strip():raise ValueError('Undefined accent overlay import')
    defined={}
    for line in run('nm','--defined-only','extension.elf').splitlines():
        parts=line.split()
        if len(parts)==3:defined[parts[2]]=int(parts[0],16)
    run('objcopy','-O','binary','extension.elf','extension.bin')
    data=(out/'extension.bin').read_bytes();end=start+len(data)
    if defined.get('__accent_start')!=start or defined.get('__accent_end')!=end or not 0<len(data)<=0x1000 or len(data)&15:
        raise ValueError('Changed accent overlay section ownership')
    entries={};inventory=[]
    relocations=run('readelf','-rW','extension.elf')
    for line in relocations.splitlines():
        if 'R_MIPS_' not in line:continue
        match=re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match:raise ValueError('Unapproved accent ELF relocation: '+line)
        at,kind,target,name=int(match[1],16),KINDS[match[2]],int(match[3],16),match[4]
        if not start<=at<end or at&3:raise ValueError('Accent relocation escapes appended image')
        inventory.append([at-ram,kind,target,name])
        if ram<=target<end:
            if not (start<=target<end or imports.get(name)==target):raise ValueError('Unapproved prefix function import')
            if at-ram in entries:raise ValueError('Duplicate accent ELF relocation')
            entries[at-ram]=kind
        elif kind!=4 or imports.get(name)!=target:raise ValueError('Changed resident accent import')
    (out/'extension.asm').write_text(run('objdump','-d','extension.elf'))
    (out/'extension-relocations.txt').write_text(relocations)
    return data,entries,{'symbols':{k:v-ram for k,v in defined.items() if start<=v<end},
        'imports':imports,'elf_relocations':inventory,'extension_code_end':defined['__accent_code_end']-ram,
        'flags':flags,'stack_usage':{n:(out/(n+'.su')).read_text() for n in ('treasure','literal')}}


def build_one(kind,data,reloc,prior,out,*,articles=None):
    if kind in BASE_IMAGES and (sha256(data),sha256(reloc))!=BASE_IMAGES[kind]:
        raise ValueError('Changed complete preceding '+kind+' image')
    ram=prior['ram'];prefix=len(data);entries=rows(reloc,prefix);symbols=prior['symbols'];sources=source_hashes()
    metadata={};extension=b''
    if kind!='event':
        extension,extra,metadata=compile_treasure(ram,prefix,symbols,out)
        if set(entries)&set(extra):raise ValueError('Appended accent relocation overlaps original image')
        entries.update(extra)
    result=bytearray(data+extension);patches=[]
    def patch(at,value,name,relocation=None):
        if at&3 or at+len(value)>prefix or any(at<p['at']+len(bytes.fromhex(p['after'])) and p['at']<at+len(value) for p in patches):
            raise ValueError('Overlapping or unbounded accent prefix patch')
        patches.append({'at':at,'before':bytes(result[at:at+len(value)]).hex(),'after':value.hex(),'name':name})
        result[at:at+len(value)]=value
        for place in tuple(entries):
            if at<=place<at+len(value):del entries[place]
        if relocation is not None:entries[at]=relocation
    if kind!='event':
        for name in TREASURE:
            target=ram+metadata['symbols'][name.replace('af_notice_','af_accent_')]
            patch(symbols[name],struct.pack('>2I',0x08000000|((target>>2)&0x3FFFFFF),0),name,4)
    if kind in ('creator','event'):
        base=0 if kind=='creator' else prior['creator_offset']
        local=symbols if kind=='creator' else prior['creator']['symbols']
        for name,target in (('af_mail_capture_set','af_accent_capture_set'),('af_mail_generate','af_accent_mail_generate')):
            patch(base+local[name],dispatch(target),name)
    if kind=='creator':
        if articles is None or sha256(articles)!='b218119460fdbb472e641cbbc6d77ff809d489bda8b8622f0157562294d575ff':
            raise ValueError('Missing complete accented item article metadata')
        at=symbols['af_item_article_data']
        if sha256(data[at:at+len(articles)])!='5c4d9b4f8e8775ea1ebbb11252a0c39244cd3b68f3016001f7a7123f6b16da6b':
            raise ValueError('Changed preceding embedded item articles')
        # Data rows need no relocation changes; retain only the changed spans.
        spans=[(16,32)]+[(48+5*r,5) for r in (304,396,615,617,1415)]
        for offset,size in spans:
            before=bytes(result[at+offset:at+offset+size]);after=articles[offset:offset+size]
            patches.append({'at':at+offset,'before':before.hex(),'after':after.hex(),'name':'item_article'})
            result[at+offset:at+offset+size]=after
    final=bytes(result);relocations=packed_rows(entries,len(final))
    limit=0x10000 if kind=='creator' else 0x8000 if kind=='notice' else 0xC000
    if len(final)>limit or len(relocations)>0x1000:raise ValueError('Accent image or relocation exceeds loader bounds')
    spec=Overlay(ram,len(final),struct.unpack_from('>5I',relocations))
    relocate_verified_data(spec,final,relocations,0x801A0010)
    restored=bytearray(final[:prefix])
    for row in patches:
        at=row['at'];before=bytes.fromhex(row['before']);restored[at:at+len(before)]=before
    if bytes(restored)!=data or source_hashes()!=sources:raise ValueError('Accent prefix/source retention failed')
    report={'version':1,'kind':kind,'ram':ram,'bytes':len(final),'prefix_bytes':prefix,
        'sha256':sha256(final),'relocation_bytes':len(relocations),'relocation_sha256':sha256(relocations),
        'previous_sha256':sha256(data),'previous_relocation_sha256':sha256(reloc),
        'previous_overlay':prior,'previous_relocation':reloc.hex(),
        'extension_sha256':sha256(extension),'patches':patches,'sources':sources,
        'font_image_sha256':FONT_PROFILE['image_sha256'],'font_pointer':FONT_POINTER,
        'toolchain_image':IMAGE,'installed':False,**metadata}
    out.mkdir(parents=True,exist_ok=True)
    (out/'overlay.bin').write_bytes(final);(out/'relocation.bin').write_bytes(relocations)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=Path('build/apology-input-pilot'))
    p.add_argument('--font',type=Path,default=Path('build/accent-mail-font'))
    p.add_argument('--output',type=Path,default=Path('build/accent-mail-overlays'))
    a=p.parse_args()
    verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    built=(a.base/'animal-forest-halfwidth.z64').read_bytes();report=json.loads((a.base/'build.json').read_text())
    if sha256(built)!=BASE_SHA or report['output_sha256']!=BASE_SHA:raise ValueError('Changed complete accent baseline ROM')
    module=report['runtime_module']
    if module['module_sha256']!=MODULE_SHA or int(module['symbols']['af_extended_font_image'],16)!=FONT_POINTER:
        raise ValueError('Changed startup-owned font pointer import')
    font=json.loads((a.font/'font.json').read_text())
    validate_font((a.font/'font.bin').read_bytes(),(a.font/'relocation.bin').read_bytes(),font)
    if font.get('mail_literals') is not True:raise ValueError('Accent adapters require the full literal-mail font')
    files=by_vrom(built);results={}
    for kind in ('creator','notice','event'):
        if kind=='creator':
            prior=module['npc_mail_loader']['overlay'];blob=files[0x03200000].extract(built)
            data,reloc=blob[:prior['bytes']],blob[prior['bytes']:]
        else:
            detail=report['noticeboard' if kind=='notice' else 'event_actor'];prior=detail['overlay']
            data=files[int(detail['vrom'],16)].extract(built)
            reloc=files[int(detail['relocation_vrom'],16)].extract(built)
            if kind=='event':
                from event_actor import PREFIX_BYTES
                prior={**prior,'creator_offset':PREFIX_BYTES}
        results[kind]=build_one(kind,data,reloc,prior,a.output/kind,
            articles=(ROOT/'build/accent-item-articles/articles.bin').read_bytes() if kind=='creator' else None)
    print(json.dumps({k:{x:r[x] for x in ('bytes','prefix_bytes','sha256','relocation_bytes','installed')} for k,r in results.items()},indent=2))


if __name__=='__main__':main()
