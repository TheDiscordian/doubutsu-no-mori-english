"""Install complete embedded menu English with explicit shared-pool ownership."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom,replace_dma,make_ups,apply_ups
import embedded_warnings as warning
import editor_confirmation as confirmation

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='e6511dfe0a51b75f8764eeed0159a31ee651f6d650075f42501977b0ea1d8483'
PARENT,PARENT_RELOC=0x7749C0,0x7778B0
POOL_PATCH,POOL_BEFORE,POOL_WORD=0x800C4B10,0x25CE2220,0x25CE3220
POOL_EXTRA=4096
BASE_POOL,BASE_REQUIRED=253056,252736


def references():
    rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    warning.reference(rel,symbols)
    return rel,symbols


def candidate(native,built):
    rel,symbols=references();images={};parents={};profiles=[]
    for owner in warning.OWNERS:
        data,reloc,profile=warning.patch_owner(native,built,owner)
        images[owner.vrom]=data;images[owner.relocation]=reloc
        parents[owner.parent_at]=warning.metadata(owner,len(data));profiles.append(profile)
    images[confirmation.VROM],confirm=confirmation.patch_owner(native,built,rel,symbols)
    align=lambda n:(n+63)&~63
    # Sum both growths even though the native maximum selects one pair. This
    # deliberately bounds the more conservative simultaneous-owner case.
    growth=sum(align(p['bytes'])-align(p['native_resident_bytes']) for p in profiles)
    if not 0<growth<=POOL_EXTRA or BASE_REQUIRED+growth>BASE_POOL+POOL_EXTRA:
        raise ValueError('Embedded English exceeds the shared menu reservation')
    profile={'version':1,'warnings':profiles,'allocation':{
        'additional_reserved_bytes':POOL_EXTRA,'additional_required_bytes':growth,
        'combined_pool_bytes':BASE_POOL+POOL_EXTRA,'conservative_required_bytes':BASE_REQUIRED+growth,
        'pool_word':POOL_WORD,'ordinary_heap_end':0x80400000},
        'saved_format_changed':False,'warning_handlers_changed':False,
        'status':'Complete English menu text installed; ordinary menu/hardware acceptance pending'}
    return images,parents,profile,confirm


def present(files):
    return any(v in files for owner in warning.OWNERS for v in (owner.new_vrom,owner.new_relocation))


def verify_shared_parts(built,native,report=None,confirm_report=None):
    files,originals=by_vrom(built),by_vrom(native)
    if not present(files):raise ValueError('Missing embedded English warning overlays')
    images,parents,profile,confirm=candidate(native,built)
    for owner in warning.OWNERS:
        for old,new in ((owner.vrom,owner.new_vrom),(owner.relocation,owner.new_relocation)):
            if (old in files or new not in files or files[new].index!=originals[old].index
                    or files[new].extract(built)!=images[old]):
                raise ValueError('Incomplete embedded warning DMA pair or native identity')
        if files[owner.new_relocation].index!=files[owner.new_vrom].index+1:
            raise ValueError('Embedded warning relocation lost its adjacent native slot')
    parent=files[PARENT].extract(built);code=files[CODE_VROM].extract(built)
    if (any(parent[at:at+32]!=value for at,value in parents.items())
            or files[PARENT_RELOC].extract(built)!=originals[PARENT_RELOC].extract(native)
            or files[confirmation.VROM].extract(built)!=images[confirmation.VROM]
            or files[confirmation.RELOC].extract(built)!=originals[confirmation.RELOC].extract(native)
            or struct.unpack_from('>I',code,POOL_PATCH-CODE_RAM)[0]!=POOL_WORD
            or struct.unpack_from('>I',code,0x800C4AFC-CODE_RAM)[0]!=0x3C0E8089
            or report is not None and report!=profile
            or confirm_report is not None and confirm_report!=confirm):
        raise ValueError('Changed complete embedded English ownership or shared-pool bounds')
    return {'owner_rows':parents,'pool_word':POOL_WORD,'allocation':profile['allocation']}


def build(native,base,report):
    verified_rom(native)
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Embedded English requires the complete Controller Pak artwork baseline')
    files,originals=by_vrom(base),by_vrom(native)
    if present(files) or files[0x1060].extract(base)!=originals[0x1060].extract(native):
        raise ValueError('Embedded English requires an untitled, unmodified warning baseline')
    from keyboard_grid_overlay import verify_owned_parts
    verify_owned_parts(base,native,report['keyboard_grid'],report['apology_input'])
    images,parents,profile,confirm=candidate(native,base)
    for v in images:
        if v not in files or files[v].extract(base)!=originals[v].extract(native):
            raise ValueError('Embedded menu owner has unrelated preceding changes')
    parent=bytearray(files[PARENT].extract(base));code=bytearray(files[CODE_VROM].extract(base))
    for owner in warning.OWNERS:
        if parent[owner.parent_at:owner.parent_at+32]!=bytes.fromhex(owner.parent_hex):
            raise ValueError('Embedded menu metadata already changed')
        parent[owner.parent_at:owner.parent_at+32]=parents[owner.parent_at]
    if struct.unpack_from('>I',code,POOL_PATCH-CODE_RAM)[0]!=POOL_BEFORE:
        raise ValueError('Embedded menu pool baseline changed')
    struct.pack_into('>I',code,POOL_PATCH-CODE_RAM,POOL_WORD)
    images[PARENT]=bytes(parent);images[CODE_VROM]=bytes(code)
    moved={int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    replacements={int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in report['replacement_files']}
    additions={int(v,16):files[int(v,16)].extract(base) for v in report['added_files']}
    new_moves={v:n for owner in warning.OWNERS for v,n in
               ((owner.vrom,owner.new_vrom),(owner.relocation,owner.new_relocation))}
    if any(v in moved or n in files for v,n in new_moves.items()):raise ValueError('Overlapping English warning VROM')
    moved.update(new_moves);replacements.update(images)
    image=replace_dma(native,replacements,moved,additions);new=by_vrom(image)
    if len(image)!=len(base) or set(new)!={new_moves.get(v,v) for v in files}:
        raise ValueError('Embedded menu installation changes unrelated cartridge identities')
    for v,entry in files.items():
        actual=new[new_moves.get(v,v)].extract(image);expected=images.get(v,entry.extract(base))
        if v==0x19D40:actual,expected=actual[:16],expected[:16]
        if actual!=expected or new[new_moves.get(v,v)].index!=entry.index:
            raise ValueError(f'Embedded English loses preceding resource {v:08X}')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Embedded English UPS reconstruction failed')
    result=copy.deepcopy(report)
    result.update(output_sha256=sha256(image),patch_sha256=sha256(patch),
        replacement_files=[f'{v:08X}' for v in sorted(replacements)],
        vrom_relocations={f'{v:08X}':f'{n:08X}' for v,n in moved.items()},
        submenu_text=profile,editor_confirmation=confirm,
        release_status='English embedded warnings and editor confirmation with all prior fixes')
    verify_shared_parts(image,native,profile,confirm)
    verify_owned_parts(image,native,result['keyboard_grid'],result['apology_input'])
    return image,patch,result


def measure_text(ledger,native,built,report):
    rel,symbols=references()
    confirmation.measure_text(ledger,native,built,report,rel,symbols)
    installed=report.get('submenu_text')
    if installed:verify_shared_parts(built,native,installed,report.get('editor_confirmation'))
    for owner in warning.OWNERS:
        old,_=warning.source(native,owner);groups=warning.line_groups(old,owner)
        texts=warning.WARNING_TEXT if owner==warning.WARNING else warning.PAK_TEXT
        sources={};english={}
        for (_,_,rows),lines in zip(groups,texts):
            for (_,_,_,ptr,length),text in zip(rows,lines):
                value=old[ptr-owner.ram:ptr-owner.ram+length]
                if ptr in sources and sources[ptr]!=value:raise ValueError('Inconsistent warning source span')
                sources[ptr]=value;english.setdefault(ptr,set()).add(text)
        for ptr,value in sorted(sources.items()):
            identity=f'ui_{owner.name}:{ptr:08X}'
            ledger.add(identity,value)
            if installed:
                from textcodec import encode
                ledger.credit(identity,encode(' '.join(sorted(english[ptr])),ledger.info),'submenu_text')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/submenu-text-01')
    args=parser.parse_args();base=ROOT/'build/controller-pak-artwork-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (base/'animal-forest-halfwidth.z64').read_bytes(),json.loads((base/'build.json').read_text()))
    args.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (args.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(args.output),'sha256':sha256(image),'patch_sha256':sha256(patch)}))


if __name__=='__main__':main()
