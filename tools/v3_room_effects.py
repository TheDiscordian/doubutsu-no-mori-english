"""Prepare complete room effects and additive native effect-controller tables.

Preparation is not cartridge installation or item eligibility. Generated effect
artwork and native owner images remain in ignored build directories.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_player_actions import native_references

VROM, RELOC, RAM = 0x8E0A30, 0x8E4170, 0x80A17190
SECTIONS = (10752, 3312, 80, 7632)
OWNER_SHA = '01a72c566b8198e20ec5d2659ab3d58e7fb26e2bff460a33952ee1ff0945ac75'
RELOC_SHA = '79c3813b5cbf68b2c3ab3825bfa4d4cbef4e3cc546afdcee369a79bea6961b1e'
LAMP_OWNER_SHA = '7c9894ef30cf85b7e1aefdd326cbea8e7efeb79a9e0bd2ca3bdf08188571d950'
LAMP_RELOC_SHA = '9b5119253d75fd2e3c22f86a313a56e66454862b020412de64a1bd12b097624b'
NATIVE_COUNT = 111
TABLES = ((0x2A00, 20), (0x32AC, 8), (0x3624, 1))
REFERENCES = {
    0xEF4: ((0xEF8, RAM+0x2A00),),
    0x1050: ((0x1058, RAM+0x3624),),
    0x1910: ((0x1920, RAM+0x32AC),),
    0x1988: ((0x1998, RAM+0x32AC),),
    0x1EAC: ((0x1EB4, RAM+0x32AC),),
    0x1F14: ((0x1F28, RAM+0x32AC),),
    0x1F60: ((0x1F74, RAM+0x32AC),),
    0x1FFC: ((0x2000, RAM+0x32AC),),
    0x20A0: ((0x20B0, RAM+0x32AC),),
    0x2200: ((0x2214, RAM+0x32AC),),
    0x25F0: ((0x25F4, RAM+0x32AC),),
}
FLASH_FUNCTIONS = (
    (0x29B50C,112,'e12cdd9ccc49733f893efdc63db73cd29326f3540bf98fbcba8892f42d0cd7fb'),
    (0x29B57C,192,'7db33695ef0da62adef145bd6c7f4705a02005e4c83327d0ab538c38f1270045'),
    (0x29B63C,204,'9d24d36b00953bb1d1fb45bba90d9172aca58857a882a7b204c3c1cf072f2c97'),
    (0x29B708,252,'a08bb373b555f05853c2f6de28cddeeab1bd90e09748034b3dfd6c44fbd807de'),
    (0x29B804,112,'0d12531a5c81efd4935d5ceae81aa1cc0903619bea3586319a85530f752ff816'),
    (0x29B874,20,'85487db2eed16eb10f12c8928412a5c3333b0e5c7bc2c3eda6bc40dd26820ccb'),
    (0x29B888,380,'05ad9c3e953c3bb4e251119b5c7ca11500ae3524ed26ccca4492ed1f7d2d33c0'),
    (0x29BA04,4,'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
)


def checked_controller(owner, reloc):
    pair=(sha256(owner),sha256(reloc))
    if pair not in ((OWNER_SHA,RELOC_SHA),(LAMP_OWNER_SHA,LAMP_RELOC_SHA)):
        raise ValueError('Changed complete original or timed-lamp effect controller')
    return dict(vrom=VROM,reloc=RELOC,ram=RAM,sha256=pair[0],reloc_sha256=pair[1],
        sections=SECTIONS,effect_count=111,active_slots=80,code_slots=12,code_slot_bytes=3072,
        graphics_slots=6,graphics_slot_bytes=3584,timed_lamp_retained=pair[0]==LAMP_OWNER_SHA)


def source_contract(source):
    functions = []
    for offset, size, digest in FLASH_FUNCTIONS:
        raw, row = source.function(offset)
        if len(raw) != size or sha256(raw) != digest:
            raise ValueError('Changed complete source flash behaviour')
        functions.append(row)
    profiles = []
    for name, expected in (('iam_ef_flash', FLASH_FUNCTIONS[:4]),
                           ('iam_ef_flashC', FLASH_FUNCTIONS[4:])):
        at, n = source.symbol(name)
        raw = source.raw(name)
        refs = {p-at: ref for (section,p),ref in source.section_relocations.items()
                if section == 5 and at <= p < at+n}
        if (n != 24 or raw[:16] != bytes(16) or
                refs != {i*4:(1,1,1,row[0]) for i,row in enumerate(expected)} or
                struct.unpack_from('>hhf', raw, 16) != (-2,255,struct.unpack('>f', bytes.fromhex('c47a0cff'))[0])):
            raise ValueError('Changed complete flash profile or native lifetime policy')
        profiles.append(dict(symbol=name,offset=at,bytes=n,sha256=sha256(raw),functions=refs))
    return dict(functions=functions,profiles=profiles,source_ticks_per_native_update=2,
        source_controller_ticks=240,source_flash_ticks=5,source_spawn_period=8,
        native_scene_widths={6:6,20:4,21:6,22:8},
        absent_native_scenes=['second floor','basement','island cottage'],
        light_endpoint_rounding='ceil(source ticks / 2), less than one native frame',
        source_wall_index=65,destination_wall_index=76,native_execution_tested=False)


def flash_art(source):
    """Relocate the complete legacy-native donor sprite without GX retiling.

    This source uses ordinary FD/F5/F3/F2 commands, not Dolphin FD/D2 commands.
    Its 16x16 IA8 resource is already linear with native channel ordering.
    """
    name='ef_takurami01_kira_modelT';at,n=source.symbol(name)
    model=bytearray(source.raw(name));refs=source.pointers(at,n)
    names=('ef_takurami01_1','ef_takurami01_kira_v')
    sizes=(256,64); destinations=(0,256); locations=(0x3C,0x7C)
    body=bytearray();resources=[]
    for symbol,size,destination,location in zip(names,sizes,destinations,locations,strict=True):
        target,length=source.symbol(symbol);data=source.raw(symbol)
        if (length != size or len(body) != destination or source.pointers(target,length)
                or refs.get(at+location) != target or u32(model,location)):
            raise ValueError('Changed complete legacy effect sprite resource')
        resources.append(dict(symbol=symbol,offset=target,bytes=size,native_offset=destination,
                              sha256=sha256(data)))
        body.extend(data);struct.pack_into('>I',model,location,0x06000000+destination)
    if set(refs) != {at+p for p in locations} or n != 144:
        raise ValueError('Changed complete legacy effect sprite bindings')
    # Check the entire program, including source culling, render mode, both
    # triangles, texture extent/stride/wrap, and absence of a primitive override.
    if sha256(model)!='93453da4c3e81e1ca20ea01c9d444d687b216cf677c4d3e9f0af8634af60c740':
        raise ValueError('Changed complete legacy effect sprite program')
    body.extend(model)
    return bytes(body),dict(bytes=len(body),sha256=sha256(body),resources=resources,
        model_offset=320,model_bytes=144,model_source_sha256=sha256(source.raw(name)),
        model_sha256=sha256(model),texture_format='IA8',texture_layout='native-linear',
        width=16,height=16,triangles=2,source_culling_retained=True)


def append_sprite(bank, art, receipt):
    """Append a full sprite bank using the native shared segment-6 convention."""
    if (len(bank)!=93328 or sha256(bank)!='daba24d2339b983ce39646017cf9685174ae5e074d5ad0599e6fe962fbfef952'
            or len(art)!=464 or receipt['bytes']!=len(art) or sha256(art)!=receipt['sha256']
            or receipt['model_offset']!=320 or receipt['model_bytes']!=144):
        raise ValueError('Changed complete effect artwork or native resource bank')
    start=len(bank);base=start+8;data=bytearray(art)
    for at,offset in ((320+0x3C,0),(320+0x7C,256)):
        if u32(data,at)!=0x06000000+offset:
            raise ValueError('Changed complete sprite segment binding')
        struct.pack_into('>I',data,at,0x06000000+base+offset)
    # The native controller skips each object's eight-byte resource header.
    # New effects use the complete appended span; original ranges stay intact.
    output=bank+bytes(8)+data
    return output,dict(graphics=[0x06000000+start,0x06000000+len(output)],
        resource_vrom=0x1410000+base,resource_bytes=len(data),
        model=0x06000000+base+320,additional_rom_bytes=len(output)-len(bank),
        bytes=len(output),sha256=sha256(output))


def profile_overlay(symbols, controller=False):
    """Native loader packet with absolute shared callbacks and no writable state."""
    prefix='af_v3_flash_controller_' if controller else 'af_v3_flash_'
    pointers=[symbols[prefix+role] for role in ('init','ct','mv','dw')]
    if any(type(p)!=int or p&3 or not 0x804C8000<=p<0x804CC000 for p in pointers):
        raise ValueError('Effect callback escapes checked shared room packet')
    data=struct.pack('>4IhhI',*pointers,-2,255,0xC47A0CFF)+bytes(8)
    # Native descriptor's VROM end points to this relocation trailer.
    relocation=struct.pack('>5I',0,32,0,0,0)+bytes(8)+struct.pack('>I',32)
    return data+relocation


def wall_binding(image, report):
    """Verify the actual installed wall against the complete donor pixels."""
    from v3_asset_loader import BLOB
    from v3_registry import SURFACES
    from v3_room_surfaces import convert_record,pixel_digest
    rows=[r for r in report['room_surfaces']['rows'] if r['source_item_id']=='2741']
    if len(rows)!=1 or SURFACES[0x2741]!=(76,0x274C):
        raise ValueError('Missing additive ringside wall identity')
    row=rows[0]
    source=(ROOT/'build/gamecube/files/forest_2nd.arc.unpacked/data/player_room_wall.bin').read_bytes()
    if sha256(source)!='2ed5e747a35ceeacbf1eff9f4655afe0ad4ae95c4b466759f09bb116d9c9037c':
        raise ValueError('Changed complete donor wall bank')
    original=source[65*0x1020:66*0x1020];wanted=convert_record(original,2)
    blob=by_vrom(image)[BLOB].extract(image);at=row['blob_offset']
    if (row['source_index']!=65 or row['destination_index']!=76 or row['bytes']!=len(wanted)
            or blob[at:at+len(wanted)]!=wanted or row['converted_sha256']!=sha256(wanted)):
        raise ValueError('Changed installed complete ringside artwork')
    return dict(source_item='2741',destination_item='274C',source_index=65,index=76,
        source_sha256=sha256(original),converted_sha256=sha256(wanted),pixels=8192,
        pixels_sha256=pixel_digest(wanted),base_sha256=sha256(image))


def extend_controller(owner, reloc, additions):
    """Append effect identities without replacing native effects or their pools.

    Materialise the original BSS as zero-filled initial data, preserving every
    original linked state address. Append expanded read-only tables after it.
    Only table-address operands and the checked public bound change in code;
    the original relocation records continue to relocate those addresses.
    """
    original=checked_controller(owner,reloc)
    if not 1<=len(additions)<=16:
        raise ValueError('Effect extension requires a bounded nonempty batch')
    groups,absolute,_,_,_=native_references(owner,reloc,expected_sections=SECTIONS)
    wanted={RAM+at for at,_ in TABLES}
    observed={hi:tuple(refs) for hi,refs in groups.items() if any(t in wanted for _,t in refs)}
    if observed!=REFERENCES or any(t in wanted for t in absolute.values()):
        raise ValueError('Changed complete effect-table reader set')
    bounds=[at for at in range(0,SECTIONS[0],4)
            if u32(owner,at)>>26 in (10,11) and u32(owner,at)&65535==NATIVE_COUNT]
    if bounds!=[0x1048] or u32(owner,0x1048)!=0x28C1006F:
        raise ValueError('Changed public effect identity bound')
    tails=[bytearray(),bytearray(),bytearray()]
    for i,row in enumerate(additions,NATIVE_COUNT):
        if set(row)!={'id','overlay','graphics','unique'} or row['id']!=i:
            raise ValueError('Non-additive or incomplete effect identity')
        start,end,ram,ram_end,profile=row['overlay']
        gs,ge=row['graphics']
        if (not 0<start<end or not 0x80000000<=ram<ram_end<0x80800000
                or ram_end-ram>0xC00 or not ram<=profile<=ram_end-24 or
                (start|end|ram|ram_end|profile)&3 or
                not (gs==ge==0 or 0x06000000<=gs<ge<=0x07000000 and 8<ge-gs<=0xE08) or
                row['unique'] not in (0,1)):
            raise ValueError('Effect resource exceeds native loader bounds')
        tails[0].extend(struct.pack('>5I',*row['overlay']))
        tails[1].extend(struct.pack('>2I',gs,ge));tails[2].append(row['unique'])
    image=bytearray(owner)+bytes(SECTIONS[3]);tables=[];targets={}
    for (at,stride),tail in zip(TABLES,tails,strict=True):
        image.extend(bytes(-len(image)%4));dest=len(image)
        data=owner[at:at+stride*NATIVE_COUNT]+tail;image.extend(data)
        targets[RAM+at]=RAM+dest
        tables.append(dict(original_offset=at,offset=dest,stride=stride,bytes=len(data),sha256=sha256(data)))
    image.extend(bytes(-len(image)%16));patches=[]
    for hi,refs in observed.items():
        high_values={(targets[t]+0x8000)>>16&65535 for _,t in refs}
        if len(high_values)!=1:raise ValueError('Effect table high-half reader has conflicting targets')
        replacements={hi:(u32(owner,hi)&0xFFFF0000)|high_values.pop()}
        replacements.update({lo:(u32(owner,lo)&0xFFFF0000)|(targets[t]&65535) for lo,t in refs})
        for at,word in replacements.items():
            struct.pack_into('>I',image,at,word)
            patches.append(dict(offset=at,before=u32(owner,at),after=word))
    bound=0x28C10000|(NATIVE_COUNT+len(additions));struct.pack_into('>I',image,0x1048,bound)
    patches.append(dict(offset=0x1048,before=0x28C1006F,after=bound))
    fixed=bytearray(reloc)
    sections=(*SECTIONS[:2],len(image)-sum(SECTIONS[:2]),0)
    struct.pack_into('>4I',fixed,0,*sections)
    native_references(image,fixed,expected_sections=sections)
    return bytes(image),bytes(fixed),dict(format='AFV3-EFFECT-CONTROLLER-1',native_count=NATIVE_COUNT,
        count=NATIVE_COUNT+len(additions),tables=tables,patches=sorted(patches,key=lambda p:p['offset']),
        sections=sections,bytes=len(image),sha256=sha256(image),reloc_sha256=sha256(fixed),
        additional_scene_bytes=len(image)-sum(SECTIONS),materialized_zero_bytes=SECTIONS[3],
        original_effects_preserved=True,active_pool_capacity=80,code_pool_slots=12,
        additions=additions,original=original,installed=False,native_execution_tested=False)


def prepare(output, base_lock):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Choose a fresh ignored build directory')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    from v3_furniture_install import inputs
    image,base_report=inputs(base_lock)
    contract=source_contract(source);contract['wall']=wall_binding(image,base_report)
    art,receipt=flash_art(source)
    files=by_vrom(image)
    controller=files[VROM].extract(image);relocation=files[RELOC].extract(image)
    contract['native_controller']=checked_controller(controller,relocation)
    bank,bank_receipt=append_sprite(files[0x1410000].extract(image),art,receipt)
    output.mkdir(parents=True)
    write_new(output/'flash.bin',art)
    write_new(output/'effect-art-bank.bin',bank)
    _,code=compile_part('room_effects',output/'callbacks',defines=(f'AF_EFFECT_FLASH_MODEL=0x{bank_receipt["model"]:08X}u',))
    profiles=[]
    for kind in (False,True):
        data=profile_overlay(code['symbols'],kind);name='flash-controller.bin' if kind else 'flash-profile.bin'
        write_new(output/name,data);profiles.append(dict(file=name,bytes=len(data),sha256=sha256(data)))
    report=dict(format='AFV3-ROOM-EFFECTS-PREPARED-1',source=contract,artwork=receipt,code=code,
        bank=bank_receipt,profiles=profiles,base_sha256=sha256(image),
        sources={p:sha256((ROOT/p).read_bytes()) for p in
            ('tools/v3_room_effects.py','tools/v3_asset_loader.py','overlays/v3/room_effects.c',
             'overlays/v3/room_effects.h','overlays/v3/room_effects.ld')},
        installed=False,selectable_imports_added=0,
        pending=['link callbacks into shared room packet','install additive controller and sprite resources',
                 'bind endpoint-hit policy and both complete sound programs','focused native integration'])
    write_new(output/'effects.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--base-lock',type=Path,required=True)
    args=parser.parse_args();r=prepare(args.output,args.base_lock)
    print(json.dumps(dict(artwork_bytes=r['artwork']['bytes'],callback_bytes=r['code']['bytes'],installed=False)))
