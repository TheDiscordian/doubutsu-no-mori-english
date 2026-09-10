"""Complete native gyroid service English with a separate safe transient buffer."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import by_vrom,sha256,verified_rom,CODE_VROM,CODE_RAM,replace_dma,make_ups,apply_ups
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from embedded_warnings import flattened_relocations,WIDTH_SHA
from font import WIDTH_TABLE
from title_assets import DATA_BASE,REL_SHA256,SYMBOLS_SHA256

ROOT=Path(__file__).resolve().parents[1]
BASE_SHA='9f12c83314b048225e87c0c4ba46853caf3dadb21f863a234ca03a879987474d'
VROM,RELOC,RAM=0x794380,0x795290,0x8088CBD0
NEW_VROM,NEW_RELOC=0x3E40000,0x3E50000
OWNER_SHA='3aa5fc187475a596bf7360b66bd2b3ea9de72d98277f45fa6ad1a1d37b03d039'
RELOC_SHA='c292e1fbd6bc837d46ab976bb807b8d9d6481c1bdce00c22951507b432d24ce7'
SECTIONS=(3616,240,0,48,42)
PARENT,PARENT_RELOC,PARENT_AT=0x7749C0,0x7778B0,0x2BD0
PARENT_ROW=bytes.fromhex('00794380007952908088cbd08088db108088d9248088d9d48088d81c00000000')
TABLE,STATE,BUFFER,CAPACITY=0xE94,0xF10,0x30,22
PREFIX=b"It's "
ROWS=((0x7FD60,b'How can I help?'),(0x7FD7C,b'May I help you?'),
    (0x7FD8C,b'How much?'),(0x7FD98,b'Got it!'),(0x7FDA0,b'Choose one.'),
    (0x7FDAC,b"You don't have room."),(0x7FDC0,b"You can't afford that."),
    (0x7FDD8,b'Thank you very much!'),(0x7FDEC,b"That's free"),
    (0x7FDF8,b'Give Away'),(0x7FE04,b"That's display only."),(0x7FE20,b' Bells'))
# Only buffer origins, clear/reveal limits, and English prefix composition change.
PATCHES=((0x8088CD0C,0x2405000C,0x24050016),(0x8088CD20,0x27040020,0x27040030),
    (0x8088CD38,0x29010008,0x2901000B),(0x8088CD48,0x24060003,0x24060005),
    (0x8088CD58,0x252A0003,0x252A0005),(0x8088CFE0,0x2861000D,0x28610017),
    (0x8088CFEC,0x2403000C,0x24030016),(0x8088D6B0,0x24650020,0x24650030),
    (0x8088D8C0,0x24640020,0x24640030),(0x8088D8D4,0x2405000C,0x24050016),
    (0x8088D8F0,0x2405000C,0x24050016))


def source(native):
    files=by_vrom(verified_rom(native));data=files[VROM].extract(native);reloc=files[RELOC].extract(native)
    if (sha256(data)!=OWNER_SHA or sha256(reloc)!=RELOC_SHA
            or struct.unpack_from('>5I',reloc)!=SECTIONS
            or files[PARENT].extract(native)[PARENT_AT:PARENT_AT+32]!=PARENT_ROW):
        raise ValueError('Changed native gyroid service source')
    return data,reloc


def patch_owner(native,built,rel,symbols):
    old,original_reloc=source(native)
    if sha256(rel)!=REL_SHA256 or sha256(symbols)!=SYMBOLS_SHA256:
        raise ValueError('Changed supplied gyroid service reference')
    widths=by_vrom(built)[CODE_VROM].extract(built)[WIDTH_TABLE:WIDTH_TABLE+256]
    if sha256(widths)!=WIDTH_SHA or widths[32]!=rel[DATA_BASE+0x6D98+0xD3]:
        raise ValueError('Changed gyroid font metrics or reference wide-space match')
    if rel[DATA_BASE+0x7FE18:DATA_BASE+0x7FE1D]!=b"It's\xd3":
        raise ValueError('Changed complete GC price prefix')
    if old[0xE20:0xE23]!=bytes.fromhex('0E7E19'):
        raise ValueError('Changed original Japanese price/free/display prefix')
    data=bytearray(old+bytes(SECTIONS[3]+32));allowed=set();records=[]
    prefix=len(data);data.extend(PREFIX+b'\0')
    patches=PATCHES+((0x8088CD30,0x3C058089,0x3C050000|((RAM+prefix+0x8000)>>16)),
                    (0x8088CD34,0x24A5D9F0,0x24A50000|((RAM+prefix)&65535)))
    for address,before,after in patches:
        at=address-RAM
        if struct.unpack_from('>I',old,at)[0]!=before:raise ValueError('Changed gyroid message instruction')
        struct.pack_into('>I',data,at,after);allowed.update(range(at,at+4))
    for i,(donor,text) in enumerate(ROWS):
        reference=text.lstrip() if i==11 else text
        if rel[DATA_BASE+donor:DATA_BASE+donor+len(reference)]!=reference:
            raise ValueError('Changed complete gyroid response reference')
        at=TABLE+i*8;ptr,length=struct.unpack_from('>2I',old,at)
        if not 0xE24<=ptr-RAM<0xE94 or not 1<=length<=12:
            raise ValueError('Unbounded native gyroid service text')
        offset=len(data);data.extend(text+b'\0');struct.pack_into('>2I',data,at,RAM+offset,len(text))
        allowed.update(range(at,at+8))
        # Include the largest native saved price in the final state's bounds.
        complete=text if i!=11 else PREFIX+b'65535'+text
        span=sum(12-widths[c] for c in complete)
        if len(complete)>CAPACITY or span>144:raise ValueError('Complete gyroid response exceeds its native window')
        records.append({'state':i,'source_address':ptr,'source_length':length,
            'donor_data_offset':donor,'text':text.decode(),'offset':offset,'max_width':span})
    data.extend(bytes(-len(data)%16));data=bytes(data)
    original_spec=Image(RAM,sum(SECTIONS[:4]),SECTIONS)
    reloc=flattened_relocations(original_reloc,original_spec,len(data))
    spec=Image(RAM,len(data),struct.unpack_from('>5I',reloc))
    if (STATE!=len(old) or BUFFER<SECTIONS[3] or CAPACITY>32
            or any(data[STATE:STATE+SECTIONS[3]+32])):
        raise ValueError('English gyroid buffer overlaps or changes native state/callback')
    for base in (0x801A0010,0x802F8010,0x803F0010):
        previous=relocate_verified_data(original_spec,old,original_reloc,base)
        loaded=relocate_verified_data(spec,data,reloc,base)
        if any(a!=b and at not in allowed for at,(a,b) in enumerate(zip(previous,loaded))):
            raise ValueError('Gyroid English changes an unreviewed native relocation')
        hi,lo=(struct.unpack_from('>I',loaded,address-RAM)[0]&65535 for address in (0x8088CD30,0x8088CD34))
        pointer=((hi<<16)+(lo-65536 if lo&32768 else lo))&0xFFFFFFFF
        if pointer!=base+prefix:raise ValueError('Gyroid English prefix pointer relocates incorrectly')
        for row in records:
            if struct.unpack_from('>2I',loaded,TABLE+row['state']*8)!=(base+row['offset'],len(row['text'])):
                raise ValueError('Gyroid English response pointer or length changed')
    metadata=bytearray(PARENT_ROW);struct.pack_into('>4I',metadata,0,NEW_VROM,NEW_VROM+len(data),RAM,RAM+len(data))
    align=lambda n:(n+63)&~63
    growth=align(len(data))-align(sum(SECTIONS[:4]))
    # The preceding warning batch reserves 257,152 and needs 253,696 bytes.
    if not 0<growth<=257152-253696:raise ValueError('Gyroid English exceeds the shared menu pool')
    profile={'version':1,'native_sha256':OWNER_SHA,'native_relocation_sha256':RELOC_SHA,
        'owner_sha256':sha256(data),'relocation_sha256':sha256(reloc),'bytes':len(data),
        'source_rel_sha256':REL_SHA256,'font_widths_sha256':WIDTH_SHA,'rows':records,
        'prefix':PREFIX.decode(),'prefix_offset':prefix,'buffer_state_offset':BUFFER,'buffer_capacity':CAPACITY,
        'callback_state_offset':0x2C,'state_relative_address':STATE,'saved_format_changed':False,
        'sales_handlers_changed':False,'patches':list(patches),
        'allocation':{'additional_required_bytes':growth,'combined_required_bytes':253696+growth,
            'combined_reserved_bytes':257152,'ordinary_heap_end':0x80400000}}
    # JSON round trips must preserve the complete profile shape.
    profile['patches']=[list(p) for p in patches]
    return data,reloc,bytes(metadata),profile


def references():
    return ((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


def present(files):return NEW_VROM in files or NEW_RELOC in files


def verify_shared_parts(built,native,report=None):
    files,originals=by_vrom(built),by_vrom(native)
    data,reloc,parent,profile=patch_owner(native,built,*references())
    from submenu_text import POOL_PATCH,POOL_WORD
    if (VROM in files or RELOC in files or NEW_VROM not in files or NEW_RELOC not in files
            or files[NEW_VROM].index!=originals[VROM].index or files[NEW_RELOC].index!=originals[RELOC].index
            or files[NEW_VROM].extract(built)!=data or files[NEW_RELOC].extract(built)!=reloc
            or files[PARENT].extract(built)[PARENT_AT:PARENT_AT+32]!=parent
            or files[PARENT_RELOC].extract(built)!=originals[PARENT_RELOC].extract(native)
            or struct.unpack_from('>I',files[CODE_VROM].extract(built),POOL_PATCH-CODE_RAM)[0]!=POOL_WORD
            or report is not None and report!=profile):
        raise ValueError('Changed complete English gyroid service ownership or allocation')
    return {'owner_offset':PARENT_AT,'owner_bytes':parent,'allocation':profile['allocation']}


def build(native,base,report):
    if sha256(base)!=BASE_SHA or report.get('output_sha256')!=BASE_SHA:
        raise ValueError('Gyroid service requires the complete embedded English baseline')
    files,originals=by_vrom(base),by_vrom(native)
    from submenu_text import verify_shared_parts as verify_warning
    verify_warning(base,native,report['submenu_text'],report['editor_confirmation'])
    if (present(files) or files[VROM].extract(base)!=originals[VROM].extract(native)
            or files[RELOC].extract(base)!=originals[RELOC].extract(native)
            or files[PARENT].extract(base)[PARENT_AT:PARENT_AT+32]!=PARENT_ROW):
        raise ValueError('Gyroid service baseline contains unrelated owner changes')
    data,reloc,metadata,profile=patch_owner(native,base,*references())
    parent=bytearray(files[PARENT].extract(base));parent[PARENT_AT:PARENT_AT+32]=metadata
    changes={VROM:data,RELOC:reloc,PARENT:bytes(parent)}
    moved={int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
    replacements={int(v,16):files[moved.get(int(v,16),int(v,16))].extract(base) for v in report['replacement_files']}
    additions={int(v,16):files[int(v,16)].extract(base) for v in report['added_files']}
    new_moves={VROM:NEW_VROM,RELOC:NEW_RELOC}
    if any(v in moved or n in files for v,n in new_moves.items()):raise ValueError('Gyroid English VROM already owned')
    replacements.update(changes);moved.update(new_moves)
    image=replace_dma(verified_rom(native),replacements,moved,additions);new=by_vrom(image)
    if len(image)!=len(base) or set(new)!={new_moves.get(v,v) for v in files}:
        raise ValueError('Gyroid English changes unrelated cartridge identities')
    for v,entry in files.items():
        target=new[new_moves.get(v,v)];actual=target.extract(image);expected=changes.get(v,entry.extract(base))
        if v==0x19D40:actual,expected=actual[:16],expected[:16]
        if actual!=expected or target.index!=entry.index:raise ValueError('Gyroid English loses a preceding resource')
    patch=make_ups(native,image)
    if apply_ups(native,patch)!=image:raise ValueError('Gyroid English UPS reconstruction failed')
    result=copy.deepcopy(report)
    result.update(output_sha256=sha256(image),patch_sha256=sha256(patch),gyroid_service=profile,
        replacement_files=[f'{v:08X}' for v in sorted(replacements)],
        vrom_relocations={f'{v:08X}':f'{n:08X}' for v,n in moved.items()},
        release_status='English gyroid service responses and safe temporary buffer; all previous work retained')
    verify_shared_parts(image,native,profile)
    from keyboard_grid_overlay import verify_owned_parts
    verify_owned_parts(image,native,result['keyboard_grid'],result['apology_input'])
    return image,patch,result


def measure_text(ledger,native,built,report):
    old,_=source(native);installed=report.get('gyroid_service')
    if installed:verify_shared_parts(built,native,installed)
    records=[('prefix',old[0xE20:0xE23],PREFIX)]
    for i,(_,text) in enumerate(ROWS):
        ptr,n=struct.unpack_from('>2I',old,TABLE+i*8)
        records.append((f'{i:04X}',old[ptr-RAM:ptr-RAM+n],text))
    for name,source_text,text in records:
        identity='ui_gyroid_service:'+name;ledger.add(identity,source_text)
        if installed:ledger.credit(identity,text,'gyroid_service')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'build/gyroid-service-01');a=p.parse_args()
    baseline=ROOT/'build/submenu-text-01'
    image,patch,report=build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (baseline/'animal-forest-halfwidth.z64').read_bytes(),json.loads((baseline/'build.json').read_text()))
    a.output.mkdir(parents=True,exist_ok=False)
    for name,value in {'animal-forest-halfwidth.z64':image,'animal-forest-halfwidth.ups':patch,
        'build.json':(json.dumps(report,indent=2)+'\n').encode()}.items():
        with (a.output/name).open('xb') as target:target.write(value)
    print(json.dumps({'output':str(a.output),'sha256':sha256(image),'patch_sha256':sha256(patch),
        'allocation':report['gyroid_service']['allocation']}))


if __name__=='__main__':main()
