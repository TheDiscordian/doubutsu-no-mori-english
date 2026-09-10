"""Pinned apology editor image; complete previous editing code remains owned."""
import json
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build_apology_overlay import IMPORTS,HOOKS,RAM,sources,patched_prefix,relocations
from toolchain import KNOWN_IMAGES
import hboard_overlay as previous
from npc_mail_show import relocate_verified_data

EXTRA_POOL=256
POOL_WORD=0x25CE0C20
ELF_SHA='184a75a0735b72022f93893aa671b2bd3a5e70c8238364b946b83487b63b80fc'
APPROVED={
    'bytes':23168,'prefix_bytes':20416,'code_end':23120,'bss_start':23152,
    'overlay_sha256':'dbd2d3dd642f49d2fdb17a3b24d3a0a553b2cbaa4ad21aabc84c135255a0bc0d',
    'previous_sha256':'265ed7752365a963b5dcb4d5e21f39ba085564615b4aba8b1aaa07a60d5a21a6',
    'previous_relocation_sha256':'a7b8a96e5b090f95be9cf85c6258117de29fc8f0edcc28186a0666b72150c3ab',
    'suffix_sha256':'4cfc987823b018d2524776e97bff2327e167cc20ca8d1cc54ef46c216296d0cb',
    'relocation_bytes':1680,
    'relocation_sha256':'2f440329fa515189e7215bb4f8f024defb60e055a74f46ec4f0b2fcd07801176',
    'symbols':{'af_apology_edit':21016,'af_apology_editor_command':21968,
        'af_apology_editor_cursor':22608,'af_apology_editor_destruct':21940,
        'af_apology_editor_exchange':22460,'af_apology_editor_init':21712,
        'af_apology_editor_key_draw':22856,'af_apology_valid':20804},
}


def preceding(data,reloc):
    prefix=bytearray(data[:APPROVED['prefix_bytes']])
    for at,(_,target,kind) in HOOKS.items():
        struct.pack_into('>I',prefix,at-RAM,target if kind==2 else 0x0C000000|((target>>2)&0x3FFFFFF))
    sections=struct.unpack_from('>5I',reloc)
    rows=[word for word in struct.unpack_from('>'+str(sections[4])+'I',reloc,20)
          if word&0xFFFFFF<APPROVED['prefix_bytes'] and word&0xFFFFFF!=0x808877E4-RAM]
    length=(24+len(rows)*4+15)&~15
    prior_rel=(struct.pack('>5I',APPROVED['prefix_bytes'],0,0,0,len(rows))+
               struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-len(rows)*4)+struct.pack('>I',length))
    return bytes(prefix),prior_rel


def validate(native,data,reloc,report=None):
    if (len(data)!=APPROVED['bytes'] or sha256(data)!=APPROVED['overlay_sha256']
            or len(reloc)!=APPROVED['relocation_bytes'] or sha256(reloc)!=APPROVED['relocation_sha256']
            or len(data)>previous.ORIGINAL_RESIDENT+previous.POOL_EXTRA+EXTRA_POOL
            or any(data[APPROVED['bss_start']:])):
        raise ValueError('Changed bounded apology editor code, state, or relocation')
    prefix,prior_rel=preceding(data,reloc)
    if (sha256(prefix)!=APPROVED['previous_sha256'] or sha256(prior_rel)!=APPROVED['previous_relocation_sha256']
            or data[:len(prefix)]!=patched_prefix(prefix,APPROVED['symbols'])):
        raise ValueError('Changed preceding complete owner editor')
    previous.validate(native,prefix,prior_rel)
    if report is not None:
        if (any(report.get(key)!=value for key,value in APPROVED.items())
                or report.get('version')!=1 or report.get('ram')!=RAM or report.get('toolchain_image') not in KNOWN_IMAGES
                or report.get('sources')!=sources() or report.get('imports')!=IMPORTS
                or sha256(json.dumps(report.get('elf_relocations'),separators=(',',':')).encode())!=ELF_SHA
                or reloc!=relocations(prior_rel,report['elf_relocations'],len(data))):
            raise ValueError('Stale apology source, compiled profile, or relocation evidence')
    spec=previous.Image(RAM,len(data),struct.unpack_from('>5I',reloc))
    old=previous.Image(RAM,len(prefix),struct.unpack_from('>5I',prior_rel))
    for base in (0x801A0000,0x802F8010,(0x80400000-len(data))&~15):
        current=relocate_verified_data(spec,data,reloc,base)
        retained=relocate_verified_data(old,prefix,prior_rel,base)
        for at in range(0,len(prefix),4):
            if RAM+at not in HOOKS and current[at:at+4]!=retained[at:at+4]:
                raise ValueError('Apology relocation changes previous code or state')
        for at,(name,_,kind) in HOOKS.items():
            target=base+APPROVED['symbols'][name]
            word=target if kind==2 else 0x0C000000|((target>>2)&0x3FFFFFF)
            if struct.unpack_from('>I',current,at-RAM)[0]!=word:
                raise ValueError('Apology hook relocates to the wrong function')
    return spec


def metadata():
    value=bytearray(previous.metadata())
    struct.pack_into('>4I',value,0,previous.NEW_VROM,previous.NEW_VROM+APPROVED['bytes'],RAM,RAM+APPROVED['bytes'])
    struct.pack_into('>I',value,20,RAM+APPROVED['symbols']['af_apology_editor_destruct'])
    return bytes(value)


def allocation(tag_size):
    from letter_names import allocation as letter_allocation
    current=letter_allocation(tag_size)
    growth=APPROVED['bytes']-previous.APPROVED['bytes']
    result={'editor_growth':growth,'extra_pool_bytes':EXTRA_POOL,
            'combined_growth_used':current['combined_growth_used']+growth,
            'combined_pool_bytes':current['combined_pool_bytes']+EXTRA_POOL,
            'conservative_required':current['conservative_required']+growth}
    if (result['combined_growth_used']>previous.POOL_EXTRA+4096+EXTRA_POOL
            or result['conservative_required']>result['combined_pool_bytes']):
        raise ValueError('Apology editor exceeds the complete shared submenu reservation')
    return result


def verify_owned_parts(built,native,report=None):
    # Deliberately does not call letter/inventory/notice shared verifiers.
    from inventory_english import NEW_VROM as TAG_VROM
    from letter_names import NEW_VROM as LETTER_VROM, POOL_PATCH
    files,originals=by_vrom(built),by_vrom(native)
    if (previous.EDITOR in files or previous.EDITOR_RELOC in files
            or previous.NEW_VROM not in files or previous.NEW_RELOCATION not in files
            or LETTER_VROM not in files or TAG_VROM not in files
            or files[previous.NEW_VROM].index!=originals[previous.EDITOR].index
            or files[previous.NEW_RELOCATION].index!=originals[previous.EDITOR_RELOC].index):
        raise ValueError('Missing complete apology editor DMA ownership')
    if len(files[previous.NEW_VROM].extract(built))!=APPROVED['bytes']:
        from keyboard_grid_overlay import verify_owned_parts as verify_grid
        return verify_grid(built,native,apology_report=report)
    validate(native,files[previous.NEW_VROM].extract(built),files[previous.NEW_RELOCATION].extract(built),
             report['overlay'] if report is not None else None)
    at=previous.METADATA[previous.EDITOR][0]
    needed=allocation(len(files[TAG_VROM].extract(built)))
    code=files[CODE_VROM].extract(built)
    if (files[previous.OWNER].extract(built)[at:at+32]!=metadata()
            or files[previous.HBOARD].extract(built)!=previous.patch_window(native)
            or files[previous.HBOARD_RELOC].extract(built)!=originals[previous.HBOARD_RELOC].extract(native)
            or struct.unpack_from('>I',code,POOL_PATCH-CODE_RAM)[0]!=POOL_WORD
            or struct.unpack_from('>I',code,0x800C4AFC-CODE_RAM)[0]!=0x3C0E8089
            or report is not None and report.get('allocation')!=needed):
        raise ValueError('Missing apology editor owner, window, or shared allocation')
    return {'owner_offset':at,'owner_bytes':metadata(),'pool_word':POOL_WORD,'pool_extra':previous.POOL_EXTRA+EXTRA_POOL,
            'allocation':needed}


def install(native,replacements,relocations,module,directory):
    from inventory_english import VROM as TAG_VROM
    from letter_names import VROM as LETTER_VROM, NEW_VROM as LETTER_NEW, POOL_PATCH, POOL_WORD as OLD_POOL
    data=(directory/'overlay.bin').read_bytes();reloc=(directory/'relocation.bin').read_bytes()
    report=json.loads((directory/'overlay.json').read_text());validate(native,data,reloc,report)
    prefix,old_rel=preceding(data,reloc)
    if (replacements.get(previous.EDITOR)!=prefix or replacements.get(previous.EDITOR_RELOC)!=old_rel
            or relocations.get(previous.EDITOR)!=previous.NEW_VROM
            or relocations.get(previous.EDITOR_RELOC)!=previous.NEW_RELOCATION
            or relocations.get(LETTER_VROM)!=LETTER_NEW):
        raise ValueError('Apology input requires the complete owner and letter editors')
    owner,code=bytearray(replacements[previous.OWNER]),bytearray(replacements[CODE_VROM])
    at=previous.METADATA[previous.EDITOR][0]
    if (owner[at:at+32]!=previous.metadata()
            or struct.unpack_from('>I',code,POOL_PATCH-CODE_RAM)[0]!=OLD_POOL
            or struct.unpack_from('>I',code,0x800C4AFC-CODE_RAM)[0]!=0x3C0E8089):
        raise ValueError('Overlapping apology owner or shared pool edit')
    needed=allocation(len(replacements[TAG_VROM]))
    owner[at:at+32]=metadata();struct.pack_into('>I',code,POOL_PATCH-CODE_RAM,POOL_WORD)
    replacements.update({previous.EDITOR:data,previous.EDITOR_RELOC:reloc,
                         previous.OWNER:bytes(owner),CODE_VROM:bytes(code)})
    return {'overlay':report,'allocation':needed,'vrom':f'{previous.NEW_VROM:08X}',
            'relocation_vrom':f'{previous.NEW_RELOCATION:08X}','input_capacity':10,
            'name_entry_kind':3,'new_saved_bytes':0,'new_resident_module_bytes':0}


def verify_installation(built,native,report):
    from letter_names import verify_shared_parts
    from apology_targets import verify_installation as verify_targets
    entry=report['apology_input']
    verify_owned_parts(built,native,entry)
    verify_shared_parts(built,native,report['runtime_module'])
    verify_targets(built,native,report)
    if (entry.get('vrom')!=f'{previous.NEW_VROM:08X}'
            or entry.get('relocation_vrom')!=f'{previous.NEW_RELOCATION:08X}'
            or entry.get('input_capacity')!=10 or entry.get('name_entry_kind')!=3
            or entry.get('new_saved_bytes')!=0 or entry.get('new_resident_module_bytes')!=0):
        raise ValueError('Incomplete apology editor installed evidence')
    for old,new in ((previous.EDITOR,previous.NEW_VROM),(previous.EDITOR_RELOC,previous.NEW_RELOCATION)):
        if report.get('vrom_relocations',{}).get(f'{old:08X}')!=f'{new:08X}':
            raise ValueError('Missing apology editor DMA evidence')
    return entry
