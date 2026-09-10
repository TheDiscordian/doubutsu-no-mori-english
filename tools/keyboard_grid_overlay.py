"""Guard the complete English-grid overlay and its unchanged native editor prefix."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom,replace_dma,make_ups,apply_ups
from build_keyboard_grid import ROOT,RAM,LIMIT,IMPORTS,HOOKS,sources,jump,patched_prefix,relocations
from check_keyboard_assembly import IMAGE
from npc_mail_show import relocate_verified_data
import apology_overlay as previous
import hboard_overlay as owner_editor

BASE_SHA='27f840aaea2693ac96fbbc084981dd978f8e376cbf8d7a1259666160d29f5f7d'
EXTRA_POOL=0x1600
POOL_WORD=0x25CE2220
ELF_SHA='d970718b2aea195662de03b1dfdb4188ed34284a36ec273f3898cdc891f44ec7'
APPROVED={
    'bytes':28656,'prefix_bytes':23168,'code_end':27776,'bss_start':28608,
    'overlay_sha256':'aa6807c5ebe327c295da87c62b23d4758adf56f6a4262f53d2477c7e31c1277f',
    'suffix_sha256':'cb7d5edad4c0d483d52753f8aa14ebf472f36cdd7019f99e998df00ab7ba95b0',
    'relocation_bytes':2096,
    'relocation_sha256':'fba855c08aa2f10f9ac3d5986e3a60bcd2502a5cf03c5f98ff03dd8b6874d017',
    'keycap_sha256':'a871104e645054f5dac54aa5f65849de6881572f51595c55b1b6548badc61b4f',
    'symbols':{'af_grid_apology':24744,'af_grid_context':28608,'af_grid_editor_destruct':25104,
        'af_grid_editor_draw':25748,'af_grid_editor_init':24940,'af_grid_editor_input':25136,
        'af_grid_editor_prepare':24888,'af_grid_key':23388,'af_grid_keycap':28256,
        'af_grid_owned':24620,'af_grid_reset':23352,'af_grid_tables':27776,'af_grid_update':23604},
}
CURSOR_APPROVED = dict(APPROVED, overlay_sha256='3f1c6fd50c06695d114dcd94785c26f80408493c74b7c4ccd8f644746c46c00c',
    suffix_sha256='06549f382d04cf0e3bab429d099ed7d63e0ca347c18f5c7abedb00c160442a51',
    relocation_sha256='6fc26aa496a5407b0af08239d0cf85c8cb5c602dc269fe85ad54699b8c01597f')
CURSOR_ELF_SHA = 'fa5fdce52953bc365a28c5f733d218998d1a179a0043dbd90c17f51ecec88cd9'


def preceding(data,reloc):
    prefix=bytearray(data[:APPROVED['prefix_bytes']])
    for at,(_,target) in HOOKS.items():struct.pack_into('>I',prefix,at-RAM,jump(target))
    sections=struct.unpack_from('>5I',reloc)
    rows=[word for word in struct.unpack_from('>'+str(sections[4])+'I',reloc,20)
          if word&0xFFFFFF<APPROVED['prefix_bytes']]
    length=(24+len(rows)*4+15)&~15
    prior_rel=struct.pack('>5I',len(prefix),0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I',*rows)+bytes(length-24-len(rows)*4)+struct.pack('>I',length)
    return bytes(prefix),prior_rel


def validate(native,data,reloc,report=None):
    from keyboard_grid_labels import compiled_form
    data=compiled_form(data)
    cursor = sha256(data)==CURSOR_APPROVED['overlay_sha256']
    approved = CURSOR_APPROVED if cursor else APPROVED
    version = 2 if cursor else 1
    if (len(data)!=approved['bytes'] or sha256(data)!=approved['overlay_sha256']
            or len(reloc)!=approved['relocation_bytes'] or sha256(reloc)!=approved['relocation_sha256']
            or len(data)>LIMIT or any(data[approved['bss_start']:])):
        raise ValueError('Changed bounded grid code, state, or relocation')
    prefix,prior_rel=preceding(data,reloc)
    previous.validate(native,prefix,prior_rel)
    if data[:len(prefix)]!=patched_prefix(prefix,APPROVED['symbols']):
        raise ValueError('Grid changes retained editor outside four hooks')
    table=APPROVED['symbols']['af_grid_tables'];cap=APPROVED['symbols']['af_grid_keycap']
    if (sha256(data[table:table+480])!='de0934289f9ee4f86cdadd87df63fe2eba0ab0b7d5cdb76949bd98ab7c54c0a7'
            or sha256(data[cap:cap+128])!=APPROVED['keycap_sha256']):
        raise ValueError('Grid layout or keycap resource changed')
    if report is not None:
        if (any(report.get(k)!=v for k,v in approved.items()) or report.get('sources')!=sources(version)
                or report.get('imports')!=IMPORTS or report.get('toolchain_image')!=IMAGE
                or report.get('version')!=version or report.get('ram')!=RAM
                or report.get('previous_sha256')!=sha256(prefix)
                or report.get('previous_relocation_sha256')!=sha256(prior_rel)
                or sha256(json.dumps(report.get('elf_relocations'),separators=(',',':')).encode())!=(CURSOR_ELF_SHA if cursor else ELF_SHA)
                or reloc!=relocations(prior_rel,report['elf_relocations'],len(data))):
            raise ValueError('Stale grid source, profile, or relocation evidence')
    spec=owner_editor.Image(RAM,len(data),struct.unpack_from('>5I',reloc))
    old=owner_editor.Image(RAM,len(prefix),struct.unpack_from('>5I',prior_rel))
    for base in (0x801A0000,0x802F8010,(0x80400000-len(data))&~15):
        current=relocate_verified_data(spec,data,reloc,base)
        retained=relocate_verified_data(old,prefix,prior_rel,base)
        for at in range(0,len(prefix),4):
            if RAM+at not in HOOKS and current[at:at+4]!=retained[at:at+4]:
                raise ValueError('Grid relocation changes previous editing code/state')
        for at,(name,_) in HOOKS.items():
            if struct.unpack_from('>I',current,at-RAM)[0]!=jump(base+APPROVED['symbols'][name]):
                raise ValueError('Grid hook relocates to the wrong function')
    return spec


def metadata():
    value=bytearray(previous.metadata())
    struct.pack_into('>4I',value,0,owner_editor.NEW_VROM,owner_editor.NEW_VROM+APPROVED['bytes'],RAM,RAM+APPROVED['bytes'])
    struct.pack_into('>I',value,20,RAM+APPROVED['symbols']['af_grid_editor_destruct'])
    return bytes(value)


def allocation(tag_size):
    prior=previous.allocation(tag_size)
    align=lambda n:(n+63)&~63
    growth=align(APPROVED['bytes'])-align(previous.APPROVED['bytes'])
    result={'editor_growth':growth,'extra_pool_bytes':EXTRA_POOL,
        'combined_growth_used':prior['combined_growth_used']+growth,
        'combined_pool_bytes':prior['combined_pool_bytes']+EXTRA_POOL,
        'conservative_required':prior['conservative_required']+growth}
    if (growth>EXTRA_POOL or result['conservative_required']>result['combined_pool_bytes']
            or POOL_WORD!=previous.POOL_WORD+EXTRA_POOL):
        raise ValueError('Grid exceeds the complete shared submenu reservation')
    return result


def verify_owned_parts(built,native,report=None,apology_report=None):
    from inventory_english import NEW_VROM as TAG_VROM
    from letter_names import NEW_VROM as LETTER_VROM,POOL_PATCH
    files,originals=by_vrom(built),by_vrom(native)
    for old,new in ((owner_editor.EDITOR,owner_editor.NEW_VROM),(owner_editor.EDITOR_RELOC,owner_editor.NEW_RELOCATION)):
        if old in files or new not in files or files[new].index!=originals[old].index:
            raise ValueError('Missing grid DMA ownership')
    if LETTER_VROM not in files or TAG_VROM not in files:raise ValueError('Missing preceding editors')
    data=files[owner_editor.NEW_VROM].extract(built);reloc=files[owner_editor.NEW_RELOCATION].extract(built)
    validate(native,data,reloc,report['overlay'] if report is not None else None)
    needed=allocation(len(files[TAG_VROM].extract(built)));at=owner_editor.METADATA[owner_editor.EDITOR][0]
    code=files[CODE_VROM].extract(built)
    pool_word=POOL_WORD
    from submenu_text import present as menu_text_present,verify_shared_parts as verify_menu_text
    if menu_text_present(files):pool_word=verify_menu_text(built,native)['pool_word']
    if (files[owner_editor.OWNER].extract(built)[at:at+32]!=metadata()
            or files[owner_editor.HBOARD].extract(built)!=owner_editor.patch_window(native)
            or files[owner_editor.HBOARD_RELOC].extract(built)!=originals[owner_editor.HBOARD_RELOC].extract(native)
            or struct.unpack_from('>I',code,POOL_PATCH-CODE_RAM)[0]!=pool_word
            or struct.unpack_from('>I',code,0x800C4AFC-CODE_RAM)[0]!=0x3C0E8089
            or report is not None and report.get('allocation')!=needed):
        raise ValueError('Missing grid owner, retained windows, or shared allocation')
    if apology_report is not None:
        prefix,prior_rel=preceding(data,reloc)
        previous.validate(native,prefix,prior_rel,apology_report['overlay'])
        if apology_report.get('allocation')!=previous.allocation(len(files[TAG_VROM].extract(built))):
            raise ValueError('Changed preceding apology allocation evidence')
    return {'owner_offset':at,'owner_bytes':metadata(),'pool_word':pool_word,
        'pool_extra':owner_editor.POOL_EXTRA+previous.EXTRA_POOL+EXTRA_POOL,'allocation':needed}


def build(native,base,report,directory):
    from inventory_english import NEW_VROM as TAG_VROM
    from letter_names import POOL_PATCH
    verified_rom(native)
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Grid requires the complete corrected collection baseline')
    previous.verify_owned_parts(base,native,report['apology_input'])
    files=by_vrom(base)
    data=(directory/'overlay.bin').read_bytes();reloc=(directory/'relocation.bin').read_bytes()
    profile=json.loads((directory/'overlay.json').read_text());validate(native,data,reloc,profile)
    prefix,prior_rel=preceding(data,reloc)
    if files[owner_editor.NEW_VROM].extract(base)!=prefix or files[owner_editor.NEW_RELOCATION].extract(base)!=prior_rel:
        raise ValueError('Grid does not retain this installed editor')
    owner=bytearray(files[owner_editor.OWNER].extract(base));code=bytearray(files[CODE_VROM].extract(base))
    at=owner_editor.METADATA[owner_editor.EDITOR][0]
    owner[at:at+32]=metadata();struct.pack_into('>I',code,POOL_PATCH-CODE_RAM,POOL_WORD)
    changed={owner_editor.NEW_VROM:data,owner_editor.NEW_RELOCATION:reloc,
             owner_editor.OWNER:bytes(owner),CODE_VROM:bytes(code)}
    moved={int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    replacements={int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in report['replacement_files']}
    additions={int(v,16):files[int(v,16)].extract(base) for v in report['added_files']}
    for original in replacements:
        target=moved.get(original,original)
        if target in changed:replacements[original]=changed[target]
    image=replace_dma(native,replacements,moved,additions);installed=by_vrom(image)
    if set(installed)!=set(files) or len(image)!=len(base):raise ValueError('Grid changes cartridge/DMA identities')
    for vrom,entry in files.items():
        expected=changed.get(vrom,entry.extract(base));actual=installed[vrom].extract(image)
        if vrom==0x19D40:actual,expected=actual[:16],expected[:16]
        if actual!=expected or installed[vrom].index!=entry.index:
            raise ValueError(f'Grid loses prior resource {vrom:08X}')
    ups=make_ups(native,image)
    if apply_ups(native,ups)!=image:raise ValueError('Grid UPS reconstruction failed')
    result=copy.deepcopy(report)
    result.update(output_sha256=sha256(image),patch_sha256=sha256(ups),keyboard_grid={
        'version':1,'overlay':profile,'allocation':allocation(len(files[TAG_VROM].extract(base))),
        'vrom':f'{owner_editor.NEW_VROM:08X}','relocation_vrom':f'{owner_editor.NEW_RELOCATION:08X}',
        'new_saved_bytes':0,'new_resident_module_bytes':0,'baseline_sha256':BASE_SHA,
        'status':'Shared grid installed; native drawing/input and ordinary hardware checks pending'},
        release_status='Separate English-grid candidate; native validation pending')
    verify_owned_parts(image,native,result['keyboard_grid'],result['apology_input'])
    return image,ups,result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overlay',type=Path,default=ROOT/'build/keyboard-grid-overlay')
    parser.add_argument('--output',type=Path,default=ROOT/'build/keyboard-grid-01')
    args=parser.parse_args();base=ROOT/'build/collection-artwork-01'
    image,ups,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()),args.overlay)
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':ups,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':report['output_sha256'],
        'patch_sha256':report['patch_sha256'],'allocation':report['keyboard_grid']['allocation']}))


if __name__=='__main__':main()
